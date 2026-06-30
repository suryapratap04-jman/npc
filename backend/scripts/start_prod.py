import sys
import time
import logging
import hashlib
from pathlib import Path
import httpx
from sqlalchemy import text
from qdrant_client import QdrantClient

# Append workspace directory for absolute imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.config.settings import settings
from backend.database.session import engine, SessionLocal
from backend.database.models import Employee, Base
from backend.scripts.load_clean_data import seed_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("start_prod")

def wait_for_db():
    logger.info("Checking PostgreSQL database availability...")
    for i in range(30):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            logger.info("PostgreSQL database is ready and connected.")
            return True
        except Exception as e:
            logger.info(f"PostgreSQL not ready yet ({e}). Retrying in 2 seconds...")
            time.sleep(2)
    logger.error("PostgreSQL was not ready in time.")
    return False

def wait_for_qdrant():
    logger.info("Checking Qdrant vector database availability...")
    for i in range(30):
        try:
            client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            client.get_collections()
            logger.info("Qdrant vector database is ready and connected.")
            return True
        except Exception as e:
            logger.info(f"Qdrant not ready yet ({e}). Retrying in 2 seconds...")
            time.sleep(2)
    logger.error("Qdrant was not ready in time.")
    return False

def wait_for_ollama():
    logger.info("Checking Ollama availability...")
    url = f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}"
    for i in range(30):
        try:
            r = httpx.get(url, timeout=5.0)
            if r.status_code == 200:
                logger.info("Ollama is ready and operational.")
                return True
        except Exception as e:
            logger.info(f"Ollama not ready yet ({e}). Retrying in 2 seconds...")
            time.sleep(2)
    logger.error("Ollama was not ready in time.")
    return False

def check_and_pull_ollama_model():
    url_tags = f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}/api/tags"
    url_pull = f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}/api/pull"
    model_name = settings.OLLAMA_MODEL
    try:
        r = httpx.get(url_tags, timeout=10.0)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            if any(model_name in m or m in model_name for m in models):
                logger.info(f"Ollama model '{model_name}' is already present locally.")
                return
            
            logger.info(f"Ollama model '{model_name}' not found. Pulling model (this can take several minutes)...")
            r_pull = httpx.post(url_pull, json={"name": model_name, "stream": False}, timeout=600.0)
            if r_pull.status_code == 200:
                logger.info(f"Successfully pulled Ollama model '{model_name}'.")
            else:
                logger.error(f"Failed to pull Ollama model: Status code {r_pull.status_code}")
    except Exception as e:
        logger.error(f"Error checking/pulling Ollama model: {e}")

def get_csv_hashes() -> dict:
    hashes = {}
    cleaned_dir = Path(__file__).parent.parent.parent / "datasets" / "cleaned"
    files = {
        "employees": "employees_clean.csv",
        "projects": "projects_clean.csv",
        "allocations": "allocations_clean.csv",
        "skills": "skills_clean.csv",
        "competencies": "competencies_clean.csv",
        "pipeline": "pipeline_clean.csv"
    }
    for key, filename in files.items():
        filepath = cleaned_dir / filename
        if filepath.exists():
            h = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    h.update(chunk)
            hashes[key] = h.hexdigest()
        else:
            hashes[key] = ""
    return hashes

def main():
    if not wait_for_db():
        sys.exit(1)
        
    if not wait_for_qdrant():
        sys.exit(1)

    if wait_for_ollama():
        check_and_pull_ollama_model()

    # 1. Initialize DB tables
    logger.info("Initializing relational database tables if needed...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Check and pull incremental hashes
    from backend.cache.cache_service import cache_service
    from backend.recommendation.precomputation import (
        precompute_candidate_pool, precompute_skills_idf,
        rebuild_qdrant_embeddings, warm_cache
    )
    
    current_hashes = get_csv_hashes()
    stored_hashes = cache_service.get("precomputed:csv_hashes") or {}
    
    db = SessionLocal()
    try:
        employee_count = db.query(Employee).count()
        logger.info(f"Relational Database check: {employee_count} employee records found.")
        
        # Check if Redis precomputed candidate pool is present
        candidate_pool_cached = cache_service.get("precomputed:candidate_pool")
        
        needs_seeding = (employee_count == 0)
        needs_precompute = (not candidate_pool_cached)
        changed_targets = []
        
        if needs_seeding:
            logger.info("Relational Database is empty. Seeding database with clean datasets...")
            seed_database()
            changed_targets = ["employees", "projects", "pipeline"]
            needs_precompute = True
        else:
            for key, curr_hash in current_hashes.items():
                if curr_hash != stored_hashes.get(key):
                    logger.info(f"Detected changes in cleaned dataset: {key}_clean.csv")
                    changed_targets.append(key)
            
            if changed_targets:
                logger.info(f"Incremental update triggered for: {changed_targets}. Seeding database...")
                seed_database()
                needs_precompute = True
            else:
                logger.info("Relational Database hashes match. Skipping seeding stage.")
                
        # Handle Qdrant embeddings checks
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        collections = [col.name for col in client.get_collections().collections]
        
        if not collections or "employees" not in collections or "projects" not in collections or "pipeline" not in collections:
            logger.info("Qdrant collection embeddings empty/missing. Forcing rebuild...")
            rebuild_qdrant_embeddings(db, "all")
            needs_precompute = True
        elif changed_targets:
            rebuild_emp = any(k in changed_targets for k in ["employees", "skills", "competencies"])
            rebuild_proj = any(k in changed_targets for k in ["projects", "allocations"])
            rebuild_pipe = "pipeline" in changed_targets
            
            if rebuild_emp:
                rebuild_qdrant_embeddings(db, "employees")
            if rebuild_proj:
                rebuild_qdrant_embeddings(db, "projects")
            if rebuild_pipe:
                rebuild_qdrant_embeddings(db, "pipeline")
                
        # Run precomputations and warming if needed
        if needs_precompute:
            logger.info("Precomputing AI Profiles and warming Redis cache...")
            precompute_candidate_pool(db)
            precompute_skills_idf(db)
            warm_cache()
            
            # Store updated hashes
            cache_service.set("precomputed:csv_hashes", current_hashes, 3600 * 24 * 30)
            logger.info("AI Knowledge Base fully warmed and ready!")
        else:
            logger.info("AI Knowledge Base is already warmed and up-to-date. Skipping precomputation.")
            
    except Exception as e:
        logger.error(f"Error during startup initialization workflow: {e}")
        raise e
    finally:
        db.close()

    # 3. Run application
    logger.info("Starting FastAPI backend application...")
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
