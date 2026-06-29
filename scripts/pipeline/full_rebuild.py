import os
import sys
import logging
import subprocess
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("full_rebuild")

def run_stage(name: str, script_path: str):
    logger.info(f"==================================================")
    logger.info(f"STARTING STAGE: {name}")
    logger.info(f"==================================================")
    
    # Resolve script absolute path
    proj_root = Path(__file__).parent.parent.parent
    full_path = proj_root / script_path
    
    if not full_path.exists():
        logger.error(f"Script not found: {full_path}")
        sys.exit(1)
        
    try:
        # Run using the same python interpreter
        # Set PYTHONPATH so absolute imports work
        env = os.environ.copy()
        env["PYTHONPATH"] = str(proj_root) + os.pathsep + str(proj_root / "scripts") + os.pathsep + env.get("PYTHONPATH", "")
        
        # Windows command context support
        result = subprocess.run(
            [sys.executable, "-u", str(full_path)],
            check=True,
            env=env,
            cwd=str(proj_root)
        )
        logger.info(f"STAGE SUCCESSFUL: {name}\n")
    except subprocess.CalledProcessError as err:
        logger.error(f"STAGE FAILED: {name} (Error: {err})")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error executing stage {name}: {e}")
        sys.exit(1)

def main():
    logger.info("Initializing complete DataOps / MLOps Rebuild Pipeline...")
    
    # Stage 1: Data Cleaning and Validation
    run_stage("Data Discovery, Validation & Cleaning", "scripts/cleaning/clean_data.py")
    
    # Stage 2: Feature Engineering
    run_stage("Feature Engineering Recommendations", "scripts/cleaning/feature_engineering.py")
    
    # Stage 3: Relational Ingestion (PostgreSQL)
    run_stage("PostgreSQL Ingestion & Reload", "backend/scripts/load_clean_data.py")
    
    # Stage 4: Profile Encoding & Vector Indexing (Qdrant)
    run_stage("Vector Embedding Generation & Qdrant Indexing", "backend/embeddings/generate_embeddings.py")
    
    # Stage 5: Final Validation & Integration Verification
    run_stage("Orchestration System Verification", "scripts/pipeline/verify_pipeline.py")
    
    logger.info("==================================================")
    logger.info("SUCCESS: Entire MLOps/DataOps Rebuild Pipeline Completed successfully!")
    logger.info("==================================================")

if __name__ == "__main__":
    main()
