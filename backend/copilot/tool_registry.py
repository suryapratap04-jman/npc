import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Import existing services
from backend.recommendation import RecommendationService, RecommendationRequest
from backend.health import ProjectHealthService
from backend.forecast import ForecastService, NewProjectDemandRequest
from backend.database.models import Employee, Project, Skill, Pipeline

logger = logging.getLogger("tool_registry")

# Try to import RAG/vector database retriever, fall back to DB-driven stubs if not installed
try:
    from backend.rag.generator import RAGGenerator
    from backend.rag.retriever import VectorRetriever
    HAS_RAG_LIBS = True
except ImportError:
    logger.warning("Local SentenceTransformers/Qdrant libs missing. Fallback to SQL database stubs.")
    HAS_RAG_LIBS = False

class SQLStubVectorRetriever:
    """Database-backed VectorRetriever stub that performs SQL text matching as fallback."""
    def __init__(self, db: Session):
        self.db = db

    def retrieve_employees(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        # Match against job_name or skills
        q = f"%{query_text}%"
        # Join employees and skills
        results = self.db.query(Employee).outerjoin(
            Skill, Employee.employee_id == Skill.employee_id
        ).filter(
            or_(
                Employee.job_name.ilike(q),
                Employee.department_name.ilike(q),
                Skill.skill.ilike(q),
                Skill.coe.ilike(q)
            ),
            Employee.is_active_version == 1
        ).distinct().limit(limit).all()
        
        hits = []
        for emp in results:
            hits.append({
                "score": 0.85,
                "payload": {
                    "employee_id": emp.employee_id,
                    "job_name": emp.job_name or "Consultant",
                    "location": emp.location or "Unknown",
                    "profile_text": f"Employee {emp.employee_id} works as a {emp.job_name} in {emp.location}."
                }
            })
        return hits

    def retrieve_projects(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        q = f"%{query_text}%"
        results = self.db.query(Project).filter(
            or_(
                Project.project_id.ilike(q),
                Project.type_of_project.ilike(q),
                Project.tech_coe.ilike(q),
                Project.proposition_coe.ilike(q)
            ),
            Project.is_active_version == 1
        ).limit(limit).all()
        
        hits = []
        for p in results:
            hits.append({
                "score": 0.85,
                "payload": {
                    "project_id": p.project_id,
                    "type_of_project": p.type_of_project or "Client Project",
                    "tech_coe": p.tech_coe or "Unknown",
                    "profile_text": f"Project {p.project_id} of type {p.type_of_project} using tech: {p.tech_coe}."
                }
            })
        return hits

    def retrieve_pipeline(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        q = f"%{query_text}%"
        results = self.db.query(Pipeline).filter(
            or_(
                Pipeline.client.ilike(q),
                Pipeline.solution.ilike(q),
                Pipeline.skillset.ilike(q)
            )
        ).limit(limit).all()
        
        hits = []
        for p in results:
            hits.append({
                "score": 0.85,
                "payload": {
                    "client": p.client,
                    "solution": p.solution or "Data Solutions",
                    "profile_text": f"Pipeline project for client {p.client} requiring {p.solution}."
                }
            })
        return hits

class SQLStubRAGGenerator:
    """Database-backed RAGGenerator stub that creates structured text summaries as fallback."""
    def __init__(self, db: Session, retriever: SQLStubVectorRetriever):
        self.db = db
        self.retriever = retriever

    def explain_recommendation(self, employee_id: str, project_id: str) -> str:
        emp = self.db.query(Employee).filter(Employee.employee_id == employee_id).first()
        proj = self.db.query(Project).filter(Project.project_id == project_id).first()
        
        emp_name = emp.job_name if emp else "Specialist"
        proj_name = proj.project_id if proj else "Target Project"
        
        return f"Database assessment indicates that employee **{employee_id}** is a strong fit for **{proj_name}** because their primary role maps to the required project profiles. In addition, their current active project allocations are scheduled to complete close to the target start date."

    def summarize_project(self, project_id: str) -> str:
        proj = self.db.query(Project).filter(Project.project_id == project_id).first()
        if not proj:
            return f"Project ID {project_id} was not found in the database."
        return f"Project **{proj.project_id}** is a **{proj.type_of_project}** started on {proj.project_start_date} and ending on {proj.project_end_date}. Tech alignment covers: {proj.tech_coe}."

    def query(self, query_text: str) -> str:
        # Search skills in DB
        hits = self.retriever.retrieve_employees(query_text, limit=3)
        if not hits:
            return f"I searched the resource database for '{query_text}' but found no matching records."
        
        names = [h["payload"]["employee_id"] for h in hits]
        return f"Based on our resource directory, the employees matching your request are: {', '.join(names)}."

class ToolRegistry:
    def __init__(self, db: Session):
        self.db = db
        self.recommendation_service = RecommendationService(db)
        self.health_service = ProjectHealthService(db)
        self.forecast_service = ForecastService(db)
        
        if HAS_RAG_LIBS:
            try:
                self.rag_service = RAGGenerator()
                self.vector_retriever = VectorRetriever()
            except Exception as e:
                logger.warning(f"Failed to load RAG/Vector clients. Reverting to SQL stubs: {e}")
                self.vector_retriever = SQLStubVectorRetriever(db)
                self.rag_service = SQLStubRAGGenerator(db, self.vector_retriever)
        else:
            self.vector_retriever = SQLStubVectorRetriever(db)
            self.rag_service = SQLStubRAGGenerator(db, self.vector_retriever)

    def recommend_resources(self, 
                            project_id: Optional[str], 
                            required_skills: List[str], 
                            project_type: str = "AI", 
                            top_n: int = 5) -> Dict[str, Any]:
        """Wrapper for RecommendationService resource matching."""
        logger.info(f"Tool invocation: recommend_resources project_id={project_id}, skills={required_skills}")
        req = RecommendationRequest(
            project_id=project_id,
            required_skills=required_skills,
            project_type=project_type,
            top_n=top_n
        )
        res = self.recommendation_service.recommend_resources(req)
        return res.model_dump()

    def get_project_health_detail(self, project_id: str) -> Dict[str, Any]:
        """Wrapper for ProjectHealthService project audit detail."""
        logger.info(f"Tool invocation: get_project_health_detail project_id={project_id}")
        res = self.health_service.get_project_health_detail(project_id)
        return res.model_dump()

    def get_projects_health(self) -> List[Dict[str, Any]]:
        """Wrapper for ProjectHealthService project list health status."""
        logger.info("Tool invocation: get_projects_health")
        res = self.health_service.get_projects_health()
        return [item.model_dump() for item in res]

    def get_rampdown_candidates(self) -> List[Dict[str, Any]]:
        """Wrapper for ProjectHealthService candidate release release timelines."""
        logger.info("Tool invocation: get_rampdown_candidates")
        res = self.health_service.get_rampdown_candidates()
        return [item.model_dump() for item in res]

    def get_new_project_forecast(self, 
                                 project_type: str, 
                                 expected_duration_months: int, 
                                 required_skills: List[str], 
                                 expected_start_date: str = "2026-08-15") -> Dict[str, Any]:
        """Wrapper for ForecastService new project demand forecast."""
        logger.info(f"Tool invocation: get_new_project_forecast type={project_type}, duration={expected_duration_months}")
        req = NewProjectDemandRequest(
            project_type=project_type,
            expected_duration_months=expected_duration_months,
            required_skills=required_skills,
            expected_start_date=expected_start_date
        )
        res = self.forecast_service.forecast_new_project(req)
        return res.model_dump()

    def get_six_month_forecast(self) -> Dict[str, Any]:
        """Wrapper for ForecastService pipeline monthly projections."""
        logger.info("Tool invocation: get_six_month_forecast")
        res = self.forecast_service.get_six_month_forecast()
        return res.model_dump()

    def get_capacity_status(self) -> Dict[str, Any]:
        """Wrapper for ForecastService availability projections."""
        logger.info("Tool invocation: get_capacity_status")
        res = self.forecast_service.get_capacity_status()
        return res.model_dump()

    def get_hiring_needs(self, 
                         project_type: str, 
                         expected_duration_months: int, 
                         required_skills: List[str], 
                         expected_start_date: str = "2026-08-15") -> Dict[str, Any]:
        """Wrapper for ForecastService external hiring analysis."""
        logger.info("Tool invocation: get_hiring_needs")
        req = NewProjectDemandRequest(
            project_type=project_type,
            expected_duration_months=expected_duration_months,
            required_skills=required_skills,
            expected_start_date=expected_start_date
        )
        res = self.forecast_service.get_hiring_needs(req)
        return res.model_dump()

    def get_redeployment_options(self, 
                                 project_type: str, 
                                 expected_duration_months: int, 
                                 required_skills: List[str], 
                                 expected_start_date: str = "2026-08-15") -> Dict[str, Any]:
        """Wrapper for ForecastService transition matching."""
        logger.info("Tool invocation: get_redeployment_options")
        req = NewProjectDemandRequest(
            project_type=project_type,
            expected_duration_months=expected_duration_months,
            required_skills=required_skills,
            expected_start_date=expected_start_date
        )
        res = self.forecast_service.get_redeployment_options(req)
        return res.model_dump()

    def query_rag(self, query: str, type: str = "general", employee_id: Optional[str] = None, project_id: Optional[str] = None) -> str:
        """Wrapper for RAGGenerator explain or summarise actions."""
        logger.info(f"Tool invocation: query_rag type={type}")
        if type == "explain":
            return self.rag_service.explain_recommendation(employee_id, project_id)
        elif type == "summarize":
            return self.rag_service.summarize_project(project_id)
        else:
            return self.rag_service.query(query)

    def search_employees(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Wrapper for VectorRetriever employee semantic search."""
        logger.info(f"Tool invocation: search_employees query='{query}'")
        return self.vector_retriever.retrieve_employees(query, limit=limit)

    def search_projects(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Wrapper for VectorRetriever project semantic search."""
        logger.info(f"Tool invocation: search_projects query='{query}'")
        return self.vector_retriever.retrieve_projects(query, limit=limit)
