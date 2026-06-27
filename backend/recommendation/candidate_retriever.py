import logging
from collections import defaultdict
from typing import List, Dict, Any, Set, Optional
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from backend.config.settings import settings
from backend.database.models import Employee, Project, Allocation, Skill, Competency
from backend.embeddings.generate_embeddings import generate_uuid_from_string

logger = logging.getLogger("candidate_retriever")

class CandidateRetriever:
    def __init__(self, db: Session):
        self.db = db
        # Lazy initialization of sentence-transformers and Qdrant to keep load fast
        self.qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            self._model.max_seq_length = 512
        return self._model

    def get_project_vector(self, project_id: str) -> List[float]:
        """Retrieves the embedding vector for a project from Qdrant."""
        try:
            point_id = generate_uuid_from_string(f"project:{project_id}")
            res = self.qdrant_client.retrieve(
                collection_name="projects",
                ids=[point_id],
                with_vectors=True
            )
            if res and res[0].vector:
                return res[0].vector
        except Exception as e:
            logger.warning(f"Could not retrieve project vector for {project_id} from Qdrant: {e}")
        return []

    def get_similar_projects(self, project_id: str, limit: int = 5) -> List[str]:
        """Finds IDs of similar projects based on vector distance in Qdrant."""
        proj_vector = self.get_project_vector(project_id)
        if not proj_vector:
            return []
        try:
            res = self.qdrant_client.query_points(
                collection_name="projects",
                query=proj_vector,
                limit=limit + 1  # include self
            )
            similar_ids = []
            for hit in res.points:
                p_id = hit.payload.get("project_id")
                if p_id and p_id != project_id:
                    similar_ids.append(p_id)
            return similar_ids[:limit]
        except Exception as e:
            logger.error(f"Error querying similar projects in Qdrant: {e}")
            return []

    def retrieve_candidates(self, required_skills: List[str], project_id: Optional[str] = None, top_n: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves a candidate pool by combining Postgres active employees and Qdrant similarity matches.
        """
        logger.info(f"Retrieving candidate pool. Skills: {required_skills}, Project: {project_id}")

        # 1. Fetch active employees from Postgres
        employees = self.db.query(Employee).filter(
            (Employee.date_of_resignation == None) | (Employee.date_of_resignation > Employee.date_of_join)
        ).all()
        
        if not employees:
            logger.warning("No active employees found in PostgreSQL database.")
            return []

        # 2. Batch retrieve related structures to avoid N+1 query overhead
        all_skills = self.db.query(Skill).all()
        skills_map = defaultdict(list)
        for s in all_skills:
            if s.employee_id:
                skills_map[s.employee_id].append(s)

        all_competencies = self.db.query(Competency).all()
        competencies_map = {c.employee_id: c for c in all_competencies}

        all_active_allocations = self.db.query(Allocation).filter(
            Allocation.is_allocation_active == 1
        ).all()
        
        allocations_map = defaultdict(list)
        for a in all_active_allocations:
            if a.employee_id:
                allocations_map[a.employee_id].append(a)

        # 3. Hybrid search - Qdrant Employee similarity
        qdrant_scores: Dict[str, float] = {}
        try:
            query_text = f"Skills requested: {', '.join(required_skills)}"
            query_vector = self.model.encode([query_text])[0].tolist()
            
            res = self.qdrant_client.query_points(
                collection_name="employees",
                query=query_vector,
                limit=top_n
            )
            for hit in res.points:
                emp_id = hit.payload.get("employee_id")
                if emp_id:
                    qdrant_scores[emp_id] = float(hit.score)
        except Exception as q_err:
            logger.warning(f"Could not perform semantic Qdrant employee query: {q_err}")

        # 4. Hybrid search - Similar historical project employees
        historical_allocated_employee_ids: Set[str] = set()
        if project_id:
            similar_project_ids = self.get_similar_projects(project_id, limit=5)
            if similar_project_ids:
                logger.info(f"Similar historical projects found: {similar_project_ids}")
                hist_allocations = self.db.query(Allocation).filter(
                    Allocation.project_id.in_(similar_project_ids)
                ).all()
                for ha in hist_allocations:
                    if ha.employee_id:
                        historical_allocated_employee_ids.add(ha.employee_id)

        # 5. Compile candidate pool objects
        candidate_pool = []
        for emp in employees:
            emp_id = emp.employee_id
            emp_skills = skills_map.get(emp_id, [])
            emp_comp = competencies_map.get(emp_id, None)
            emp_allocs = allocations_map.get(emp_id, [])

            # Compute current utilization
            utilization = sum(float(a.allocation_by_percentage or 0.0) for a in emp_allocs)

            # Determine Qdrant semantic/similar project score labels
            qdrant_score = qdrant_scores.get(emp_id, 0.0)
            has_similar_proj_experience = emp_id in historical_allocated_employee_ids

            candidate_pool.append({
                "employee": emp,
                "skills": emp_skills,
                "competency": emp_comp,
                "allocations": emp_allocs,
                "utilization": utilization,
                "qdrant_score": qdrant_score,
                "has_similar_proj_experience": has_similar_proj_experience
            })

        logger.info(f"Retrieved {len(candidate_pool)} total candidates in the pool.")
        return candidate_pool
