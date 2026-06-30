import logging
import math
import hashlib
import json
from collections import defaultdict, Counter
from datetime import date
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from backend.config.settings import settings
from backend.database.session import SessionLocal
from backend.database.models import Employee, Project, Allocation, Skill, Competency, Pipeline
from backend.cache.cache_service import cache_service
from backend.embeddings.generate_embeddings import (
    build_employee_profile, build_project_profile, build_pipeline_profile,
    generate_uuid_from_string, encode_in_chunks
)

logger = logging.getLogger("precomputation")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DictObject:
    """
    Wrapper class that allows both dictionary key access and attribute access
    for seamless compatibility with the existing recommendation engines.
    """
    def __init__(self, d):
        for k, v in d.items():
            if isinstance(v, dict):
                self.__dict__[k] = DictObject(v)
            elif isinstance(v, list):
                self.__dict__[k] = [DictObject(i) if isinstance(i, dict) else i for i in v]
            else:
                self.__dict__[k] = v

    def __getattr__(self, name):
        return self.__dict__.get(name)

    def __getitem__(self, key):
        return self.__dict__.get(key)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        res = {}
        for k, v in self.__dict__.items():
            if isinstance(v, DictObject):
                res[k] = v.to_dict()
            elif isinstance(v, list):
                res[k] = [item.to_dict() if isinstance(item, DictObject) else item for item in v]
            else:
                res[k] = v
        return res

def precompute_candidate_pool(db: Session) -> List[Dict[str, Any]]:
    """Precomputes the entire active candidate pool and stores it in Redis cache."""
    logger.info("Starting candidate pool precomputation...")
    
    employees = db.query(Employee).filter(
        (Employee.date_of_resignation == None) | (Employee.date_of_resignation > Employee.date_of_join)
    ).all()
    
    all_skills = db.query(Skill).all()
    skills_map = defaultdict(list)
    for s in all_skills:
        if s.employee_id:
            skills_map[s.employee_id].append({
                "skill": s.skill,
                "subskill": s.subskill,
                "experience": s.experience,
                "experience_numeric": s.experience_numeric,
                "score": s.score
            })

    all_competencies = db.query(Competency).all()
    competencies_map = {}
    for c in all_competencies:
        competencies_map[c.employee_id] = {
            "stakeholder_management_score": c.stakeholder_management_score,
            "consultative_guidance_score": c.consultative_guidance_score,
            "techno_functional_score": c.techno_functional_score,
            "communication_score": c.communication_score,
            "ambiguity_navigation_score": c.ambiguity_navigation_score,
            "capabilities_articulation_score": c.capabilities_articulation_score,
            "solution_architecture_score": c.solution_architecture_score,
            "project_planning_score": c.project_planning_score
        }

    all_active_allocations = db.query(Allocation).filter(
        Allocation.is_allocation_active == 1
    ).all()
    
    allocations_map = defaultdict(list)
    for a in all_active_allocations:
        if a.employee_id:
            allocations_map[a.employee_id].append({
                "project_id": a.project_id,
                "allocation_by_percentage": a.allocation_by_percentage,
                "is_allocation_active": a.is_allocation_active,
                "allocated_start_date": str(a.allocated_start_date) if a.allocated_start_date else None,
                "allocated_end_date": str(a.allocated_end_date) if a.allocated_end_date else None
            })

    non_bau_project_ids = set()
    active_projects = db.query(Project).filter(Project.is_active_version == 1).all()
    for p in active_projects:
        if p.client_id != "CLIENT_127" and p.type_of_project != "BAU Activity":
            non_bau_project_ids.add(p.project_id)

    projects_info = {
        p.project_id: {
            "client_id": p.client_id,
            "type_of_project": p.type_of_project,
            "project_end_date": str(p.project_end_date) if p.project_end_date else None
        }
        for p in active_projects
    }
    cache_service.set("precomputed:projects_info", projects_info, 3600 * 24 * 7)

    projects_name_map = {}
    for p in active_projects:
        projects_name_map[p.project_id] = f"{p.client_id or 'Client'} - {p.type_of_project or 'Engagement'}"

    pool = []
    for emp in employees:
        emp_id = emp.employee_id
        emp_skills = skills_map.get(emp_id, [])
        emp_comp = competencies_map.get(emp_id, None)
        emp_allocs = allocations_map.get(emp_id, [])

        emp_dict = {
            "employee_id": emp.employee_id,
            "job_name": emp.job_name,
            "department_name": emp.department_name,
            "location": emp.location,
            "date_of_join": str(emp.date_of_join) if emp.date_of_join else None,
            "date_of_resignation": str(emp.date_of_resignation) if emp.date_of_resignation else None,
            "manager_id": emp.manager_id,
            "account_status": emp.account_status,
            "is_active_version": emp.is_active_version
        }

        pool.append({
            "employee_id": emp_id,
            "employee": emp_dict,
            "skills": emp_skills,
            "competency": emp_comp,
            "allocations": emp_allocs,
            "non_bau_project_ids": list(non_bau_project_ids),
            "projects_name_map": projects_name_map
        })

    cache_service.set("precomputed:candidate_pool", pool, 3600 * 24 * 7)
    cache_service.set("precomputed:projects_name_map", projects_name_map, 3600 * 24 * 7)
    logger.info(f"Candidate pool precomputed and stored in Redis ({len(pool)} records).")
    return pool

def precompute_skills_idf(db: Session) -> Tuple[Dict[str, float], float]:
    """Precomputes Skill Rarity (IDF) and saves it to Redis cache."""
    logger.info("Computing skills rarity (IDF)...")
    active_employees = db.query(Employee).filter(
        (Employee.date_of_resignation == None) | (Employee.date_of_resignation > Employee.date_of_join)
    ).all()
    active_emp_ids = {emp.employee_id for emp in active_employees}
    total_active_employees = len(active_emp_ids) or 1

    all_skills = db.query(Skill).all()
    skill_counts = Counter(
        s.skill.lower().strip()
        for s in all_skills
        if s.skill and s.employee_id in active_emp_ids
    )
    
    skills_idf = {
        skill: math.log(1.0 + total_active_employees / (1.0 + count))
        for skill, count in skill_counts.items()
    }
    default_idf = math.log(1.0 + total_active_employees / 1.0)
    
    payload = {
        "skills_idf": skills_idf,
        "default_idf": default_idf
    }
    cache_service.set("precomputed:skills_idf", payload, 3600 * 24 * 7)
    logger.info("Skills rarity (IDF) stored in Redis.")
    return skills_idf, default_idf

def rebuild_qdrant_embeddings(db: Session, target_type: str = "all"):
    """
    Triggers Qdrant collection recreation and batch vector upserts for updated models.
    Supports targeting specific CSV data types: 'employees', 'projects', 'pipeline', or 'all'.
    """
    logger.info(f"Rebuilding Qdrant embeddings for target_type: {target_type}...")
    from sentence_transformers import SentenceTransformer
    
    qclient = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    model.max_seq_length = 512
    
    dummy_vec = model.encode(["test"])
    vector_dim = len(dummy_vec[0])
    
    targets = ["employees", "projects", "pipeline"] if target_type == "all" else [target_type]
    
    for coll in targets:
        exists = qclient.collection_exists(collection_name=coll)
        if exists:
            qclient.delete_collection(collection_name=coll)
        qclient.create_collection(
            collection_name=coll,
            vectors_config=qmodels.VectorParams(
                size=vector_dim,
                distance=qmodels.Distance.COSINE
            )
        )
        logger.info(f"Recreated empty Qdrant collection: {coll}")
        
        # 1. EMPLOYEES
        if coll == "employees":
            employees = db.query(Employee).all()
            profiles_txts, payloads, point_ids = [], [], []
            for emp in employees:
                skills = db.query(Skill).filter(Skill.employee_id == emp.employee_id).all()
                comp = db.query(Competency).filter(Competency.employee_id == emp.employee_id).first()
                allocs = db.query(Allocation).filter(Allocation.employee_id == emp.employee_id).all()
                
                profile_txt = build_employee_profile(emp, skills, comp, allocs)
                profiles_txts.append(profile_txt)
                payloads.append({
                    "employee_id": emp.employee_id,
                    "job_name": emp.job_name,
                    "department_name": emp.department_name,
                    "location": emp.location,
                    "skills": [s.skill for s in skills],
                    "subskills": [s.subskill for s in skills],
                    "profile_text": profile_txt
                })
                point_ids.append(generate_uuid_from_string(f"employee:{emp.employee_id}"))
                
            if profiles_txts:
                embeddings = encode_in_chunks(model, profiles_txts, chunk_size=128, batch_size=8)
                points = [
                    qmodels.PointStruct(id=point_ids[i], vector=embeddings[i], payload=payloads[i])
                    for i in range(len(point_ids))
                ]
                qclient.upsert(collection_name="employees", points=points)
                logger.info(f"Upserted {len(points)} employees to Qdrant.")
                
        # 2. PROJECTS
        elif coll == "projects":
            projects = db.query(Project).all()
            profiles_txts, payloads, point_ids = [], [], []
            for proj in projects:
                allocs = db.query(Allocation).filter(Allocation.project_id == proj.project_id).all()
                profile_txt = build_project_profile(proj, allocs)
                profiles_txts.append(profile_txt)
                payloads.append({
                    "project_id": proj.project_id,
                    "client_id": proj.client_id,
                    "type_of_project": proj.type_of_project,
                    "project_status": proj.project_status,
                    "tech_coe": proj.tech_coe,
                    "proposition_coe": proj.proposition_coe,
                    "profile_text": profile_txt
                })
                point_ids.append(generate_uuid_from_string(f"project:{proj.project_id}"))
                
            if profiles_txts:
                embeddings = encode_in_chunks(model, profiles_txts, chunk_size=128, batch_size=8)
                points = [
                    qmodels.PointStruct(id=point_ids[i], vector=embeddings[i], payload=payloads[i])
                    for i in range(len(point_ids))
                ]
                qclient.upsert(collection_name="projects", points=points)
                logger.info(f"Upserted {len(points)} projects to Qdrant.")
                
        # 3. PIPELINE
        elif coll == "pipeline":
            pipeline_items = db.query(Pipeline).all()
            profiles_txts, payloads, point_ids = [], [], []
            for pipe in pipeline_items:
                profile_txt = build_pipeline_profile(pipe)
                profiles_txts.append(profile_txt)
                payloads.append({
                    "pipeline_id": pipe.id,
                    "client": pipe.client,
                    "solution": pipe.solution,
                    "status": pipe.status,
                    "profile_text": profile_txt
                })
                point_ids.append(generate_uuid_from_string(f"pipeline:{pipe.id}"))
                
            if profiles_txts:
                embeddings = encode_in_chunks(model, profiles_txts, chunk_size=128, batch_size=8)
                points = [
                    qmodels.PointStruct(id=point_ids[i], vector=embeddings[i], payload=payloads[i])
                    for i in range(len(point_ids))
                ]
                qclient.upsert(collection_name="pipeline", points=points)
                logger.info(f"Upserted {len(points)} pipeline items to Qdrant.")

def warm_cache():
    """Warms the Redis cache by invoking local API endpoints via FastAPI's TestClient."""
    logger.info("Initializing Redis Cache Warming Loop...")
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    
    endpoints = [
        "/api/dashboard/summary",
        "/api/forecast/summary",
        "/api/health/projects",
        "/api/health/utilization",
        "/api/employees?limit=100",
        "/api/projects?limit=100",
        "/api/pipeline?limit=100"
    ]
    for ep in endpoints:
        try:
            logger.info(f"Warming route: GET {ep}")
            client.get(ep)
        except Exception as e:
            logger.warning(f"Error warming route {ep}: {e}")
            
    db = SessionLocal()
    try:
        pipeline_items = db.query(Pipeline).filter(Pipeline.skillset != None, Pipeline.skillset != "").all()
        logger.info(f"Found {len(pipeline_items)} pipeline requests to warm recommendation scoring...")
        for item in pipeline_items:
            try:
                skills = [s.strip() for s in item.skillset.split(",") if s.strip()]
                if not skills:
                    continue
                req_body = {
                    "project_id": str(item.id),
                    "required_skills": skills,
                    "project_type": item.request_type or "AI",
                    "top_n": 10,
                    "strategy": "hybrid_v1"
                }
                logger.info(f"Warming recommendations: POST /api/recommend/resources for project {item.id} ({item.client})")
                client.post("/api/recommend/resources", json=req_body)
            except Exception as e:
                logger.warning(f"Error warming recommendation project {item.id}: {e}")
    finally:
        db.close()
    logger.info("Cache warming sequence completed successfully!")
