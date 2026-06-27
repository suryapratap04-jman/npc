import os
import sys
import uuid
import logging
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any

# Enable absolute path imports for the backend directory
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.config.settings import settings
from backend.database.session import SessionLocal
from backend.database.models import Employee, Project, Allocation, Skill, Competency, Pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("generate_embeddings")

# Import dependencies inside try/except block to keep Docker builds safe before library download
try:
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
except ImportError:
    logger.warning("Local libraries (sentence-transformers or qdrant-client) not installed yet. Running stub mode.")

def generate_uuid_from_string(val: str) -> str:
    """Generates a deterministic UUID from a string key to ensure idempotency in Qdrant."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, val))

def encode_in_chunks(model, texts: List[str], chunk_size: int = 128, batch_size: int = 8) -> List[List[float]]:
    """Encodes a list of text strings in smaller chunks to control the memory footprint on virtualized CPUs."""
    embeddings = []
    total = len(texts)
    for i in range(0, total, chunk_size):
        chunk = texts[i:i + chunk_size]
        logger.info(f"Encoding chunk {i // chunk_size + 1}/{(total - 1) // chunk_size + 1} ({len(chunk)} items)...")
        chunk_embeddings = model.encode(chunk, batch_size=batch_size, show_progress_bar=False)
        embeddings.extend(chunk_embeddings.tolist())
    return embeddings

def build_employee_profile(emp: Employee, skills: List[Skill], comp: Competency, allocs: List[Allocation]) -> str:
    """Compiles a rich textual profile representation of an Employee for semantic indexing."""
    profile_parts = [
        f"Employee ID: {emp.employee_id}",
        f"Role Designation: {emp.job_name}",
        f"Department: {emp.department_name}",
        f"Location: {emp.location}"
    ]
    
    # Skills details
    if skills:
        skill_strings = []
        for s in skills:
            exp_str = f" ({s.experience})" if s.experience else ""
            score_str = f" score {s.score}" if s.score is not None else ""
            skill_strings.append(f"{s.skill} - {s.subskill}{exp_str}{score_str}")
        profile_parts.append("Skills & Experience: " + "; ".join(skill_strings))
    else:
        profile_parts.append("Skills: None registered.")

    # Competency scores
    if comp:
        comp_strings = []
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
        for capability, score in comp_map.items():
            if score is not None:
                comp_strings.append(f"{capability}: {score}/5")
        if comp_strings:
            profile_parts.append("Qualitative Core Competencies: " + "; ".join(comp_strings))
            
    # Allocation status
    active_allocs = [a for a in allocs if a.is_allocation_active == 1]
    total_util = sum(a.allocation_by_percentage for a in active_allocs if a.allocation_by_percentage)
    profile_parts.append(f"Current Utilization Rate: {total_util}%")
    if active_allocs:
        proj_list = [f"Project {a.project_id} (allocation {a.allocation_by_percentage}%)" for a in active_allocs]
        profile_parts.append("Active Projects: " + ", ".join(proj_list))
    else:
        profile_parts.append("Active Projects: None. Currently unallocated (bench status).")

    return "\n".join(profile_parts)

def build_project_profile(proj: Project, allocs: List[Allocation]) -> str:
    """Compiles a rich textual profile representation of a Project for semantic indexing."""
    profile_parts = [
        f"Project ID: {proj.project_id}",
        f"Client: {proj.client_id}",
        f"Type: {proj.type_of_project}",
        f"Status: {proj.project_status}",
        f"Technical Center of Excellence: {proj.tech_coe or 'N/A'}",
        f"Proposition COE: {proj.proposition_coe or 'N/A'}",
        f"Timeline: From {proj.project_start_date} to {proj.project_end_date}"
    ]
    
    if allocs:
        active_allocs = [a for a in allocs if a.is_allocation_active == 1]
        profile_parts.append(f"Team Size: {len(active_allocs)} active resources allocated.")
    else:
        profile_parts.append("Team Size: No active resources allocated.")
        
    return "\n".join(profile_parts)

def build_pipeline_profile(pipe: Pipeline) -> str:
    """Compiles a rich textual profile representation of a pipeline opportunity."""
    profile_parts = [
        f"Pipeline Opportunity ID: {pipe.id}",
        f"Solution requested: {pipe.solution or 'N/A'}",
        f"Status: {pipe.status or 'N/A'}",
        f"Client: {pipe.client or 'N/A'} (Priority: {pipe.client_priority or 'N/A'})",
        f"Required Start Date: {pipe.original_requested_start_date}",
        f"Likely Start Date: {pipe.likely_start_date}",
        f"Required Duration: {pipe.number_of_weeks or 0} weeks",
        f"Skillset specifications: {pipe.skillset or 'N/A'}",
        f"Comments: {pipe.comments or 'None'}"
    ]
    return "\n".join(profile_parts)

def run_indexing():
    logger.info("Initializing vector indexing pipeline...")
    
    # 1. Initialize Clients
    qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
    logger.info(f"Connecting to Qdrant at {qdrant_url}")
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    
    # Load SentenceTransformers model
    logger.info(f"Loading local embedding model: {settings.EMBEDDING_MODEL}")
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    model.max_seq_length = 512 # Set sequence length limit to prevent OOM errors
    
    # Generate dummy to get vector dimension size dynamically
    dummy_vec = model.encode(["test"])
    vector_dim = len(dummy_vec[0])
    logger.info(f"Detected vector embedding dimension: {vector_dim}")
    
    # Define collections
    collections_to_init = ["employees", "projects", "pipeline"]
    for coll_name in collections_to_init:
        # Check if exists, delete or skip
        exists = client.collection_exists(collection_name=coll_name)
        if exists:
            logger.info(f"Collection '{coll_name}' already exists. Re-creating for fresh synchronization.")
            client.delete_collection(collection_name=coll_name)
            
        client.create_collection(
            collection_name=coll_name,
            vectors_config=qmodels.VectorParams(
                size=vector_dim,
                distance=qmodels.Distance.COSINE
            )
        )
        logger.info(f"Initialized empty Qdrant collection '{coll_name}'.")

    db = SessionLocal()
    try:
        # --- INDEX EMPLOYEES ---
        logger.info("Fetching employees from PostgreSQL to construct AI Profiles...")
        employees = db.query(Employee).all()
        
        profiles_txts = []
        payloads = []
        point_ids = []
        
        for emp in employees:
            skills = db.query(Skill).filter(Skill.employee_id == emp.employee_id).all()
            comp = db.query(Competency).filter(Competency.employee_id == emp.employee_id).first()
            allocs = db.query(Allocation).filter(Allocation.employee_id == emp.employee_id).all()
            
            profile_txt = build_employee_profile(emp, skills, comp, allocs)
            profiles_txts.append(profile_txt)
            
            payload = {
                "employee_id": emp.employee_id,
                "job_name": emp.job_name,
                "department_name": emp.department_name,
                "location": emp.location,
                "skills": [s.skill for s in skills],
                "subskills": [s.subskill for s in skills],
                "profile_text": profile_txt
            }
            payloads.append(payload)
            point_ids.append(generate_uuid_from_string(f"employee:{emp.employee_id}"))
            
        if profiles_txts:
            logger.info(f"Encoding {len(profiles_txts)} employee profiles in parallel batches...")
            embeddings = encode_in_chunks(model, profiles_txts, chunk_size=128, batch_size=8)
            
            employee_points = [
                qmodels.PointStruct(id=point_ids[i], vector=embeddings[i], payload=payloads[i])
                for i in range(len(point_ids))
            ]
            client.upsert(collection_name="employees", points=employee_points)
            logger.info(f"Successfully synchronized {len(employee_points)} Employee AI Profiles to Qdrant.")
            
        # --- INDEX PROJECTS ---
        logger.info("Fetching projects from PostgreSQL to construct AI Profiles...")
        projects = db.query(Project).all()
        
        profiles_txts = []
        payloads = []
        point_ids = []
        
        for proj in projects:
            allocs = db.query(Allocation).filter(Allocation.project_id == proj.project_id).all()
            
            profile_txt = build_project_profile(proj, allocs)
            profiles_txts.append(profile_txt)
            
            payload = {
                "project_id": proj.project_id,
                "client_id": proj.client_id,
                "type_of_project": proj.type_of_project,
                "project_status": proj.project_status,
                "tech_coe": proj.tech_coe,
                "proposition_coe": proj.proposition_coe,
                "profile_text": profile_txt
            }
            payloads.append(payload)
            point_ids.append(generate_uuid_from_string(f"project:{proj.project_id}"))
            
        if profiles_txts:
            logger.info(f"Encoding {len(profiles_txts)} project profiles in parallel batches...")
            embeddings = encode_in_chunks(model, profiles_txts, chunk_size=128, batch_size=8)
            
            project_points = [
                qmodels.PointStruct(id=point_ids[i], vector=embeddings[i], payload=payloads[i])
                for i in range(len(point_ids))
            ]
            client.upsert(collection_name="projects", points=project_points)
            logger.info(f"Successfully synchronized {len(project_points)} Project AI Profiles to Qdrant.")

        # --- INDEX PIPELINE OPPORTUNITIES ---
        logger.info("Fetching pipeline requests from PostgreSQL to construct AI Profiles...")
        pipeline_items = db.query(Pipeline).all()
        
        profiles_txts = []
        payloads = []
        point_ids = []
        
        for pipe in pipeline_items:
            profile_txt = build_pipeline_profile(pipe)
            profiles_txts.append(profile_txt)
            
            payload = {
                "pipeline_id": pipe.id,
                "client": pipe.client,
                "solution": pipe.solution,
                "status": pipe.status,
                "profile_text": profile_txt
            }
            payloads.append(payload)
            point_ids.append(generate_uuid_from_string(f"pipeline:{pipe.id}"))
            
        if profiles_txts:
            logger.info(f"Encoding {len(profiles_txts)} pipeline profiles in parallel batches...")
            embeddings = encode_in_chunks(model, profiles_txts, chunk_size=128, batch_size=8)
            
            pipeline_points = [
                qmodels.PointStruct(id=point_ids[i], vector=embeddings[i], payload=payloads[i])
                for i in range(len(point_ids))
            ]
            client.upsert(collection_name="pipeline", points=pipeline_points)
            logger.info(f"Successfully synchronized {len(pipeline_points)} Pipeline Opportunity Profiles to Qdrant.")
            
        logger.info("Vector Database sync completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during vector embedding generation: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    run_indexing()
