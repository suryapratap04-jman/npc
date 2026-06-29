import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.session import SessionLocal
from backend.database.models import Employee, Project, Allocation, Skill, Competency, Pipeline
from backend.config.settings import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_pipeline")

def verify():
    logger.info("Starting System Verification Stage...")
    errors = []
    
    # 1. Verify PostgreSQL Row Counts
    db = SessionLocal()
    try:
        logger.info("Checking PostgreSQL row counts...")
        counts = {
            "Employees": (Employee, 1042),
            "Projects": (Project, 2052),
            "Allocations": (Allocation, 31969),
            "Skills": (Skill, 82211),
            "Competencies": (Competency, 196),
            "Pipeline": (Pipeline, 293)
        }
        
        for name, (model, expected) in counts.items():
            cnt = db.query(model).count()
            logger.info(f" - {name}: count={cnt} (Expected={expected})")
            if cnt != expected:
                errors.append(f"PostgreSQL Table '{name}' row count mismatch: found {cnt}, expected {expected}")
                
    except Exception as e:
        logger.error(f"PostgreSQL validation failed: {e}")
        errors.append(f"PostgreSQL connection/query error: {e}")
    finally:
        db.close()
        
    # 2. Verify Qdrant Collections
    try:
        logger.info("Checking Qdrant vector database...")
        from qdrant_client import QdrantClient
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        
        expected_collections = {
            "employees": 1042,
            "projects": 2052,
            "pipeline": 293
        }
        
        # Check model dimensions dynamically
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        dummy_vec = model.encode(["test"])
        expected_dim = len(dummy_vec[0])
        logger.info(f"Embedding model dimension: {expected_dim}")
        
        for coll_name, expected_points in expected_collections.items():
            if not client.collection_exists(coll_name):
                errors.append(f"Qdrant Collection '{coll_name}' is missing.")
                continue
                
            info = client.get_collection(coll_name)
            logger.info(f" - Collection: {coll_name}, points={info.points_count}, status={info.status}, vector_size={info.config.params.vectors.size}")
            
            if info.points_count != expected_points:
                errors.append(f"Qdrant Collection '{coll_name}' points mismatch: found {info.points_count}, expected {expected_points}")
                
            if info.config.params.vectors.size != expected_dim:
                errors.append(f"Qdrant Collection '{coll_name}' dimension mismatch: found {info.config.params.vectors.size}, expected {expected_dim}")
                
            if str(info.status).lower() not in ["green", "ok", "status.green", "status.ok"]:
                errors.append(f"Qdrant Collection '{coll_name}' status unhealthy: {info.status}")
                
    except Exception as e:
        logger.error(f"Qdrant validation failed: {e}")
        errors.append(f"Qdrant connection/query error: {e}")
        
    # 3. Verify Recommendation Engine Readiness
    try:
        logger.info("Testing Recommendation Engine readiness...")
        from backend.recommendation.recommendation_service import RecommendationService
        from backend.recommendation.schemas import RecommendationRequest
        
        db = SessionLocal()
        service = RecommendationService(db)
        req = RecommendationRequest(
            project_id="CLIENT_101_005",
            required_skills=["Python", "SQL"],
            project_type="AI",
            required_competencies=["Communication Skills"],
            project_start_date="2026-08-01",
            top_n=5
        )
        res = service.recommend_resources(req)
        db.close()
        
        logger.info(f"Recommendation test succeeded. Returned {len(res.recommendations)} candidates.")
        if not res.recommendations:
            errors.append("Recommendation readiness test returned an empty list of recommendations.")
            
    except Exception as e:
        logger.error(f"Recommendation test failed: {e}")
        errors.append(f"Recommendation engine error: {e}")
        
    # Final verdict
    if errors:
        logger.error(f"Verification FAILED with {len(errors)} errors:")
        for err in errors:
            logger.error(f" - [ERROR] {err}")
        sys.exit(1)
    else:
        logger.info("SUCCESS: All system verification checks passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    verify()
