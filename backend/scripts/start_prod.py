import sys
import time
import logging
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
from backend.embeddings.generate_embeddings import run_indexing

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
            # Match model name cleanly
            if any(model_name in m or m in model_name for m in models):
                logger.info(f"Ollama model '{model_name}' is already present locally.")
                return
            
            logger.info(f"Ollama model '{model_name}' not found. Pulling model (this can take several minutes)...")
            # Request pull
            r_pull = httpx.post(url_pull, json={"name": model_name, "stream": False}, timeout=600.0)
            if r_pull.status_code == 200:
                logger.info(f"Successfully pulled Ollama model '{model_name}'.")
            else:
                logger.error(f"Failed to pull Ollama model: Status code {r_pull.status_code}")
    except Exception as e:
        logger.error(f"Error checking/pulling Ollama model: {e}")

def main():
    if not wait_for_db():
        sys.exit(1)
        
    if not wait_for_qdrant():
        sys.exit(1)

    # 1. Initialize DB tables
    logger.info("Initializing relational database tables if needed...")
    Base.metadata.create_all(bind=engine)
    
    # Check if DB is seeded
    db = SessionLocal()
    try:
        employee_count = db.query(Employee).count()
        logger.info(f"Relational Database check: {employee_count} employee records found.")
        if employee_count == 0:
            logger.info("Relational Database is empty. Seeding database with clean datasets...")
            seed_database()
        else:
            logger.info("Relational Database already seeded. Skipping seed stage.")
    except Exception as e:
        logger.error(f"Error checking/seeding PostgreSQL: {e}")
    finally:
        db.close()

    # 2. Check Qdrant collection embeddings
    try:
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        collections = [col.name for col in client.get_collections().collections]
        needs_indexing = False
        
        if not collections or "employees" not in collections or "projects" not in collections:
            needs_indexing = True
        else:
            emp_info = client.get_collection(collection_name="employees")
            proj_info = client.get_collection(collection_name="projects")
            if emp_info.points_count == 0 or proj_info.points_count == 0:
                needs_indexing = True
                
        if needs_indexing:
            logger.info("Qdrant collection embeddings empty/missing. Running AI Profile indexing pipeline...")
            run_indexing()
        else:
            logger.info("Qdrant collections already contain vector points. Skipping indexing.")
    except Exception as e:
        logger.error(f"Error checking/indexing Qdrant collections: {e}")

    # 3. Pull model in Ollama if online
    if wait_for_ollama():
        check_and_pull_ollama_model()

    # 4. Run application
    logger.info("Starting FastAPI backend application...")
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
