import logging
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from backend.config.settings import settings
from backend.database.session import get_db, engine
from backend.database.models import Employee, Project, Skill, Pipeline, Allocation, Competency
from backend.embeddings.generate_embeddings import run_indexing
from backend.recommendation import RecommendationService, RecommendationRequest, RecommendationResponse, BenchmarkResponse, RecommendationBenchmarker
from backend.rag.retriever import VectorRetriever
from backend.health import ProjectHealthService, ProjectHealthSummary, ProjectHealthDetail, RampDownDetail, ProjectHealthAnalysisRequest
from backend.rag.generator import RAGGenerator
from backend.forecast import (
    ForecastService, NewProjectDemandRequest, NewProjectForecastResponse,
    SixMonthForecastResponse, CapacityStatusResponse, HiringResponse, RedeploymentResponse
)
from backend.copilot import (
    CopilotService, CopilotChatRequest, CopilotChatResponse,
    CopilotExplainRequest, CopilotExplainResponse, ConversationHistoryResponse
)
from backend.cache import (
    cache,
    NS_RECOMMENDATION, TTL_RECOMMENDATION,
    NS_DASHBOARD, TTL_DASHBOARD,
    NS_FORECAST, TTL_FORECAST,
    NS_HEALTH, TTL_HEALTH,
    NS_SEARCH, TTL_SEARCH,
    NS_EMPLOYEE, TTL_EMPLOYEE,
    NS_PROJECT, TTL_PROJECT,
    NS_COPILOT, TTL_COPILOT_SESSION
)

# Register database event listeners for cache invalidation
import backend.database.events

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("main_api")

app = FastAPI(
    title="AI Resource Management API Platform",
    description="Backend AI microservices supporting resource matching, forecasting, semantic search, and RAG.",
    version="1.0.0"
)

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG components lazily
_retriever = None
_generator = None

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = VectorRetriever()
    return _retriever

def get_generator():
    global _generator
    if _generator is None:
        _generator = RAGGenerator()
    return _generator

# Pydantic Schemas for Requests
class SearchRequest(BaseModel):
    query: str
    limit: int = 5

class RAGQueryRequest(BaseModel):
    query: Optional[str] = None
    collection: str = "employees"
    employee_id: Optional[str] = None
    project_id: Optional[str] = None
    type: str = "general" # general, explain, summarize

# --- STARTUP EVENT ---

@app.on_event("startup")
def startup_event():
    logger.info("Initializing Redis namespaces and verification on startup...")
    from backend.cache.redis_client import verify_redis_connection, get_redis_client
    from backend.config.settings import settings
    if settings.CACHE_ENABLED:
        if verify_redis_connection():
            client = get_redis_client()
            if not client.exists("metrics:hits"):
                client.set("metrics:hits", 0)
            if not client.exists("metrics:misses"):
                client.set("metrics:misses", 0)
            logger.info("Redis cache successfully verified and namespaces initialized.")
        else:
            logger.warning("Redis cache enabled but connection check failed on startup.")

# --- API ENDPOINTS ---

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Verifies relational database, vector database, local LLM, and Redis cache connectivity."""
    status = {
        "relational_db": "healthy",
        "vector_db": "healthy",
        "llm_orchestrator": "healthy",
        "redis_cache": "healthy",
        "status": "all_services_operational"
    }
    
    # 1. Test Postgres
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Healthcheck failed on Postgres: {e}")
        status["relational_db"] = f"unhealthy: {e}"
        status["status"] = "degraded_state"
        
    # 2. Test Qdrant Client
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        client.get_collections()
    except Exception as e:
        logger.error(f"Healthcheck failed on Qdrant: {e}")
        status["vector_db"] = f"unhealthy: {e}"
        status["status"] = "degraded_state"

    # 3. Test Ollama/LLM provider
    try:
        from backend.llm import get_llm_provider
        provider = get_llm_provider()
        if settings.LLM_PROVIDER == "ollama":
            import httpx
            r = httpx.get(f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}/")
            if r.status_code != 200:
                raise Exception("Ollama endpoint returned non-200.")
        else:
            if not provider.api_key:
                raise Exception(f"{settings.LLM_PROVIDER} API Key is not set.")
    except Exception as e:
        logger.error(f"Healthcheck failed on LLM: {e}")
        status["llm_orchestrator"] = f"unhealthy: {e}"
        status["status"] = "degraded_state"
        
    # 4. Test Redis Cache
    if settings.CACHE_ENABLED:
        try:
            from backend.cache.redis_client import verify_redis_connection
            if not verify_redis_connection():
                raise Exception("Redis ping failed.")
        except Exception as e:
            logger.error(f"Healthcheck failed on Redis: {e}")
            status["redis_cache"] = f"unhealthy: {e}"
            status["status"] = "degraded_state"
    else:
        status["redis_cache"] = "disabled"
        
    if status["status"] == "degraded_state":
        raise HTTPException(status_code=503, detail=status)
        
    return status

# --- CACHE MONITORING ---

@app.get("/api/cache/metrics")
def get_cache_metrics():
    """Fetches Redis cache usage metrics and ratios."""
    from backend.cache.cache_service import cache_service
    return cache_service.get_metrics()

@app.post("/api/cache/clear")
def clear_cache(namespace: Optional[str] = Query(None, description="Specific namespace to clear. Clears all if empty.")):
    """Manually clears the cache namespaces."""
    from backend.cache.cache_service import cache_service
    if namespace:
        count = cache_service.invalidate_namespace(namespace)
        return {"status": "success", "message": f"Cleared {count} keys in namespace '{namespace}'."}
    else:
        # scan for all and flush
        from backend.cache.redis_client import get_redis_client
        try:
            client = get_redis_client()
            client.flushdb()
            # reset metrics
            client.set("metrics:hits", 0)
            client.set("metrics:misses", 0)
            return {"status": "success", "message": "Flushed all cache namespaces and reset metrics counters."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# --- RELATIONAL RESOURCES ---

@app.get("/api/employees")
@cache(namespace=NS_EMPLOYEE, ttl_seconds=TTL_EMPLOYEE)
def get_employees(db: Session = Depends(get_db), limit: int = 20, location: Optional[str] = None):
    query = db.query(Employee)
    if location:
        query = query.filter(Employee.location.ilike(location))
    employees = query.limit(limit).all()
    
    enriched = []
    for emp in employees:
        skills = db.query(Skill).filter(Skill.employee_id == emp.employee_id).all()
        comp = db.query(Competency).filter(Competency.employee_id == emp.employee_id).first()
        allocs = db.query(Allocation).filter(
            Allocation.employee_id == emp.employee_id,
            Allocation.is_allocation_active == 1
        ).all()
        
        allocation_percentage = sum(a.allocation_by_percentage for a in allocs if a.allocation_by_percentage)
        
        current_project_id = None
        if allocs:
            sorted_allocs = sorted(allocs, key=lambda a: a.allocation_by_percentage or 0, reverse=True)
            current_project_id = sorted_allocs[0].project_id

        skill_names = [s.skill for s in skills if s.skill]
        
        comp_names = []
        if comp:
            comp_map = {
                "Stakeholder Management": comp.stakeholder_management_score,
                "Consultative Guidance": comp.consultative_guidance_score,
                "Techno-Functional Expertise": comp.techno_functional_score,
                "Communication Skills": comp.communication_score,
                "Ambiguity Navigation": comp.ambiguity_navigation_score,
                "Capabilities Articulation": comp.capabilities_articulation_score,
                "Solution Architecture": comp.solution_architecture_score,
                "Project Planning": comp.project_planning_score
            }
            comp_names = [k for k, v in comp_map.items() if v is not None and v >= 3]

        experience_years = max([s.experience_numeric for s in skills if s.experience_numeric is not None] or [4])

        enriched.append({
            "employee_id": emp.employee_id,
            "location": emp.location,
            "date_of_join": emp.date_of_join,
            "date_of_resignation": emp.date_of_resignation,
            "job_name": emp.job_name,
            "department_name": emp.department_name,
            "manager_id": emp.manager_id,
            "account_status": emp.account_status,
            "is_active_version": emp.is_active_version,
            "impossible_value_flag": emp.impossible_value_flag,
            
            # Enriched fields
            "allocation_percentage": allocation_percentage,
            "current_project_id": current_project_id,
            "skills": skill_names,
            "competencies": comp_names,
            "experience_years": experience_years,
            "email": f"{emp.employee_id.lower()}@company.com"
        })
    return enriched

@app.get("/api/projects")
@cache(namespace=NS_PROJECT, ttl_seconds=TTL_PROJECT)
def get_projects(db: Session = Depends(get_db), limit: int = 20, status: Optional[str] = None):
    query = db.query(Project)
    if status:
        query = query.filter(Project.project_status.ilike(status))
    return query.limit(limit).all()

@app.get("/api/skills")
def get_skills(db: Session = Depends(get_db), limit: int = 50, skill_name: Optional[str] = None):
    query = db.query(Skill)
    if skill_name:
        query = query.filter(Skill.skill.ilike(skill_name))
    return query.limit(limit).all()

@app.get("/api/pipeline")
def get_pipeline(db: Session = Depends(get_db), limit: int = 20, client: Optional[str] = None):
    query = db.query(Pipeline)
    if client:
        query = query.filter(Pipeline.client.ilike(client))
    return query.limit(limit).all()

# --- EMBEDDING OPS ---

@app.post("/api/embeddings/generate")
def trigger_embeddings_indexing():
    """Triggers building AI Profiles and indexing vector collections in Qdrant."""
    logger.info("Triggered embeddings index sync API request...")
    try:
        run_indexing()
        return {"status": "success", "message": "Embedding sync completed successfully across all collections."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to synchronize embeddings: {e}")

# --- SEMANTIC SEARCH ---

@app.post("/api/search/employees")
@cache(namespace=NS_SEARCH, ttl_seconds=TTL_SEARCH)
def search_employees(req: SearchRequest, retriever: VectorRetriever = Depends(get_retriever)):
    """Performs vector semantic similarity search for employee profiles."""
    logger.info(f"API Semantic Search Employees: query='{req.query}'")
    results = retriever.retrieve_employees(req.query, limit=req.limit)
    return results

@app.post("/api/search/projects")
@cache(namespace=NS_SEARCH, ttl_seconds=TTL_SEARCH)
def search_projects(req: SearchRequest, retriever: VectorRetriever = Depends(get_retriever)):
    """Performs vector semantic similarity search for projects."""
    logger.info(f"API Semantic Search Projects: query='{req.query}'")
    results = retriever.retrieve_projects(req.query, limit=req.limit)
    return results

# --- RETRIEVAL AUGMENTED GENERATION (RAG) ---

@app.post("/api/rag/query")
def query_rag_pipeline(req: RAGQueryRequest, generator: RAGGenerator = Depends(get_generator)):
    """Q&A retrieval pipeline explaining staffing matches or summarizing scopes."""
    logger.info(f"API RAG Request Type: {req.type}")
    
    if req.type == "explain":
        if not req.employee_id or not req.project_id:
            raise HTTPException(status_code=400, detail="RAG type 'explain' requires both 'employee_id' and 'project_id'.")
        answer = generator.explain_recommendation(req.employee_id, req.project_id)
        return {"query_type": "explain_recommendation", "answer": answer}
        
    elif req.type == "summarize":
        if not req.project_id:
            raise HTTPException(status_code=400, detail="RAG type 'summarize' requires 'project_id'.")
        answer = generator.summarize_project(req.project_id)
        return {"query_type": "summarize_project", "answer": answer}
        
    elif req.type == "general":
        if not req.query:
            raise HTTPException(status_code=400, detail="RAG type 'general' requires a 'query' string.")
        answer = generator.query(req.query, collection_name=req.collection)
        return {"query_type": "general_qa", "answer": answer}
        
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported RAG query type '{req.type}'.")

# --- RECOMMENDATION SERVICE ---

@app.post("/api/recommend/resources", response_model=RecommendationResponse)
@cache(namespace=NS_RECOMMENDATION, ttl_seconds=TTL_RECOMMENDATION)
def recommend_resources(req: RecommendationRequest, db: Session = Depends(get_db)):
    """
    Ranks active employees for allocation recommendations based on skills, competencies, and utilization, 
    explaining choices via a generative LLM summary.
    """
    try:
        service = RecommendationService(db)
        return service.recommend_resources(req)
    except Exception as e:
        logger.error(f"Error executing recommendation matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommend/benchmark", response_model=BenchmarkResponse)
def benchmark_recommendations(req: RecommendationRequest, db: Session = Depends(get_db)):
    """
    Runs all recommendation strategies on the same request and returns their ranked outputs and metrics comparison.
    """
    try:
        benchmarker = RecommendationBenchmarker(db)
        return benchmarker.run_benchmark(req)
    except Exception as e:
        logger.error(f"Error executing recommendation benchmarking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- PROJECT HEALTH & CAPACITY INTELLIGENCE ---

@app.get("/api/health/projects", response_model=List[ProjectHealthSummary])
@cache(namespace=NS_HEALTH, ttl_seconds=TTL_HEALTH)
def get_projects_health(db: Session = Depends(get_db)):
    """
    Retrieves health status summaries for all active projects.
    """
    try:
        service = ProjectHealthService(db)
        return service.get_projects_health()
    except Exception as e:
        logger.error(f"Error fetching projects health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health/projects/{project_id}", response_model=ProjectHealthDetail)
@cache(namespace=NS_HEALTH, ttl_seconds=TTL_HEALTH)
def get_project_health_detail(project_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a detailed risk, utilization, and cost recovery audit for a single project.
    """
    try:
        service = ProjectHealthService(db)
        return service.get_project_health_detail(project_id)
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error fetching project detail health for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/health/analyze", response_model=ProjectHealthDetail)
def analyze_project_health(req: ProjectHealthAnalysisRequest, db: Session = Depends(get_db)):
    """
    Triggers diagnostic audit pipeline for a specific project.
    """
    try:
        service = ProjectHealthService(db)
        return service.get_project_health_detail(req.project_id)
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error running project health analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health/rampdown", response_model=List[RampDownDetail])
@cache(namespace=NS_HEALTH, ttl_seconds=TTL_HEALTH)
def get_rampdown_candidates(db: Session = Depends(get_db)):
    """
    Lists active projects candidate for releasing allocations/resources.
    """
    try:
        service = ProjectHealthService(db)
        return service.get_rampdown_candidates()
    except Exception as e:
        logger.error(f"Error fetching rampdown projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health/utilization")
@cache(namespace=NS_HEALTH, ttl_seconds=TTL_HEALTH)
def get_utilization_stats(db: Session = Depends(get_db)):
    """
    Returns workload utilization and overallocation percentages per active project.
    """
    try:
        service = ProjectHealthService(db)
        return service.get_utilization_stats()
    except Exception as e:
        logger.error(f"Error fetching utilization stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health/billability")
@cache(namespace=NS_HEALTH, ttl_seconds=TTL_HEALTH)
def get_billability_stats(db: Session = Depends(get_db)):
    """
    Returns billing efficiency breakdown and shadow resource logs per active project.
    """
    try:
        service = ProjectHealthService(db)
        return service.get_billability_stats()
    except Exception as e:
        logger.error(f"Error fetching billability stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- DEMAND FORECAST & CAPACITY PLANNING INTELLIGENCE (USE CASE 2) ---

@app.post("/api/forecast/new-project", response_model=NewProjectForecastResponse)
@cache(namespace=NS_FORECAST, ttl_seconds=TTL_FORECAST)
def forecast_new_project(req: NewProjectDemandRequest, db: Session = Depends(get_db)):
    """
    Predicts team composition, duration, FTEs, costs, and hiring vs redeployment actions for a new project.
    """
    try:
        service = ForecastService(db)
        return service.forecast_new_project(req)
    except Exception as e:
        logger.error(f"Error forecasting new project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/forecast/six-month", response_model=SixMonthForecastResponse)
@cache(namespace=NS_FORECAST, ttl_seconds=TTL_FORECAST)
def get_six_month_forecast(db: Session = Depends(get_db)):
    """
    Computes a rolling 6-month operational forecast of volume, utilization, capacity, and role demand.
    """
    try:
        service = ForecastService(db)
        return service.get_six_month_forecast()
    except Exception as e:
        logger.error(f"Error compiling six-month forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/forecast/capacity", response_model=CapacityStatusResponse)
@cache(namespace=NS_FORECAST, ttl_seconds=TTL_FORECAST)
def get_capacity_status(db: Session = Depends(get_db)):
    """
    Returns the organization's resource capacity projections for 0, 30, 60, and 90 days.
    """
    try:
        service = ForecastService(db)
        return service.get_capacity_status()
    except Exception as e:
        logger.error(f"Error fetching capacity status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/forecast/hiring", response_model=HiringResponse)
@cache(namespace=NS_FORECAST, ttl_seconds=TTL_FORECAST)
def get_hiring_needs(
    project_type: str = Query(..., description="Project type (e.g. AI)"),
    expected_duration_months: int = Query(6, description="Duration in months"),
    required_skills: List[str] = Query(default=[], description="Required skills list"),
    expected_start_date: str = Query("2026-08-15", description="Start date YYYY-MM-DD"),
    expected_team_size: Optional[int] = Query(None, description="Optional team size limit"),
    db: Session = Depends(get_db)
):
    """
    Returns prioritized external hiring requirements for a new project spec.
    """
    try:
        req = NewProjectDemandRequest(
            project_type=project_type,
            expected_duration_months=expected_duration_months,
            required_skills=required_skills,
            expected_start_date=expected_start_date,
            expected_team_size=expected_team_size
        )
        service = ForecastService(db)
        return service.get_hiring_needs(req)
    except Exception as e:
        logger.error(f"Error compiling hiring needs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/forecast/redeployment", response_model=RedeploymentResponse)
@cache(namespace=NS_FORECAST, ttl_seconds=TTL_FORECAST)
def get_redeployment_options(
    project_type: str = Query(..., description="Project type (e.g. AI)"),
    expected_duration_months: int = Query(6, description="Duration in months"),
    required_skills: List[str] = Query(default=[], description="Required skills list"),
    expected_start_date: str = Query("2026-08-15", description="Start date YYYY-MM-DD"),
    expected_team_size: Optional[int] = Query(None, description="Optional team size limit"),
    db: Session = Depends(get_db)
):
    """
    Returns available internal redeployment candidates for a new project spec.
    """
    try:
        req = NewProjectDemandRequest(
            project_type=project_type,
            expected_duration_months=expected_duration_months,
            required_skills=required_skills,
            expected_start_date=expected_start_date,
            expected_team_size=expected_team_size
        )
        service = ForecastService(db)
        return service.get_redeployment_options(req)
    except Exception as e:
        logger.error(f"Error compiling redeployment options: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- AI RESOURCE MANAGEMENT COPILOT ---

@app.post("/api/copilot/chat", response_model=CopilotChatResponse)
def copilot_chat(req: CopilotChatRequest, db: Session = Depends(get_db)):
    """
    Conversational chat endpoint for resource managers to query recommendations, health, capacity, and forecasts.
    """
    try:
        service = CopilotService(db)
        return service.chat(req)
    except Exception as e:
        logger.error(f"Error in copilot chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/copilot/query", response_model=CopilotChatResponse)
def copilot_query(req: CopilotChatRequest, db: Session = Depends(get_db)):
    """
    Single query endpoint (bypassing session loop context or treating it as a one-off run).
    """
    try:
        service = CopilotService(db)
        return service.chat(req)
    except Exception as e:
        logger.error(f"Error in copilot query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/copilot/explain", response_model=CopilotExplainResponse)
@cache(namespace=NS_COPILOT, ttl_seconds=TTL_COPILOT_SESSION)
def copilot_explain(req: CopilotExplainRequest, db: Session = Depends(get_db)):
    """
    Direct endpoint explaining resource allocations using semantic and RAG models.
    """
    try:
        service = CopilotService(db)
        return service.explain(req)
    except Exception as e:
        logger.error(f"Error in copilot explain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/copilot/history", response_model=ConversationHistoryResponse)
@cache(namespace=NS_COPILOT, ttl_seconds=TTL_COPILOT_SESSION)
def get_copilot_history(session_id: str = Query("default"), db: Session = Depends(get_db)):
    """
    Returns conversational session logs for a given session.
    """
    try:
        service = CopilotService(db)
        return service.get_history(session_id)
    except Exception as e:
        logger.error(f"Error fetching copilot history: {e}")
        raise HTTPException(status_code=500, detail=str(e))



