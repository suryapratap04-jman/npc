import logging
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from backend.config.settings import settings
from backend.database.session import get_db, engine
from backend.database.models import Employee, Project, Skill, Pipeline
from backend.embeddings.generate_embeddings import run_indexing
from backend.rag.retriever import VectorRetriever
from backend.rag.generator import RAGGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("main_api")

app = FastAPI(
    title="AI Resource Management API Platform",
    description="Backend AI microservices supporting resource matching, forecasting, semantic search, and RAG.",
    version="1.0.0"
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

# --- API ENDPOINTS ---

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Verifies relational database, vector database, and local LLM connectivity."""
    status = {
        "relational_db": "healthy",
        "vector_db": "healthy",
        "llm_orchestrator": "healthy",
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
        # Check running or collections list
        client.get_collections()
    except Exception as e:
        logger.error(f"Healthcheck failed on Qdrant: {e}")
        status["vector_db"] = f"unhealthy: {e}"
        status["status"] = "degraded_state"

    # 3. Test Ollama/LLM provider
    try:
        from backend.llm import get_llm_provider
        provider = get_llm_provider()
        # Small verify
        if settings.LLM_PROVIDER == "ollama":
            import httpx
            r = httpx.get(f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}/")
            if r.status_code != 200:
                raise Exception("Ollama endpoint returned non-200.")
        else:
            # For cloud provider check if key is loaded
            if not provider.api_key:
                raise Exception(f"{settings.LLM_PROVIDER} API Key is not set.")
    except Exception as e:
        logger.error(f"Healthcheck failed on LLM: {e}")
        status["llm_orchestrator"] = f"unhealthy: {e}"
        status["status"] = "degraded_state"
        
    if status["status"] == "degraded_state":
        raise HTTPException(status_code=503, detail=status)
        
    return status

# --- RELATIONAL RESOURCES ---

@app.get("/api/employees")
def get_employees(db: Session = Depends(get_db), limit: int = 20, location: Optional[str] = None):
    query = db.query(Employee)
    if location:
        query = query.filter(Employee.location.ilike(location))
    return query.limit(limit).all()

@app.get("/api/projects")
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
def search_employees(req: SearchRequest, retriever: VectorRetriever = Depends(get_retriever)):
    """Performs vector semantic similarity search for employee profiles."""
    logger.info(f"API Semantic Search Employees: query='{req.query}'")
    results = retriever.retrieve_employees(req.query, limit=req.limit)
    return results

@app.post("/api/search/projects")
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
