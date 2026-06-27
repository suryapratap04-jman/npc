import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

# Enable absolute path imports for the backend directory
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.config.settings import settings
from backend.database.session import engine, Base, SessionLocal
from backend.database.models import (
    Employee, Project, Allocation, Skill, Competency, Timesheet, WeeklyStatus, Pipeline
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("load_clean_data")

# Determine cleanedData directory location relative to the project root
CLEANED_DATA_DIR = Path(__file__).parent.parent.parent / "cleanedData"

def clean_df_for_db(df: pd.DataFrame, date_cols: list) -> pd.DataFrame:
    """Prepares DataFrame for db entry, parsing dates, converting NaN to None."""
    df_clean = df.copy()
    # Convert dates
    for col in date_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors="coerce").dt.date
            
    # Replace NaN/NaT with None so SQLAlchemy writes NULL
    df_clean = df_clean.replace({np.nan: None})
    return df_clean

def seed_database():
    logger.info("Initializing relational database tables...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Clear existing data in CASCADE order to make the script fully idempotent
        logger.info("Truncating existing tables for clean load...")
        db.execute(text("TRUNCATE TABLE timesheets, allocations, skills, competencies, weekly_status, pipeline, employees, projects CASCADE;"))
        db.commit()
        
        # 1. Employees
        logger.info("Loading employees_clean.csv...")
        df_emp = pd.read_csv(CLEANED_DATA_DIR / "employees_clean.csv")
        df_emp = clean_df_for_db(df_emp, ["date_of_join", "date_of_resignation"])
        db.bulk_insert_mappings(Employee, df_emp.to_dict(orient="records"))
        logger.info(f"Loaded {len(df_emp)} employees.")
        
        # 2. Projects
        logger.info("Loading projects_clean.csv...")
        df_proj = pd.read_csv(CLEANED_DATA_DIR / "projects_clean.csv")
        df_proj = clean_df_for_db(df_proj, ["project_start_date", "project_end_date"])
        db.bulk_insert_mappings(Project, df_proj.to_dict(orient="records"))
        logger.info(f"Loaded {len(df_proj)} projects.")
        
        # 3. Allocations
        logger.info("Loading allocations_clean.csv...")
        df_alloc = pd.read_csv(CLEANED_DATA_DIR / "allocations_clean.csv")
        df_alloc = clean_df_for_db(df_alloc, ["allocated_start_date", "allocated_end_date"])
        db.bulk_insert_mappings(Allocation, df_alloc.to_dict(orient="records"))
        logger.info(f"Loaded {len(df_alloc)} allocations.")
        
        # 4. Skills
        logger.info("Loading skills_clean.csv...")
        df_skills = pd.read_csv(CLEANED_DATA_DIR / "skills_clean.csv")
        df_skills = clean_df_for_db(df_skills, [])
        db.bulk_insert_mappings(Skill, df_skills.to_dict(orient="records"))
        logger.info(f"Loaded {len(df_skills)} skills records.")
        
        # 5. Competencies
        logger.info("Loading competencies_clean.csv...")
        df_comp = pd.read_csv(CLEANED_DATA_DIR / "competencies_clean.csv")
        df_comp = clean_df_for_db(df_comp, [])
        db.bulk_insert_mappings(Competency, df_comp.to_dict(orient="records"))
        logger.info(f"Loaded {len(df_comp)} competencies records.")
        
        # 6. Timesheets
        logger.info("Loading timesheets_clean.csv...")
        # Since timesheets is large (~128k rows), load in chunks for speed and memory efficiency
        ts_path = CLEANED_DATA_DIR / "timesheets_clean.csv"
        total_ts = 0
        for chunk in pd.read_csv(ts_path, chunksize=25000):
            chunk_clean = clean_df_for_db(chunk, ["date", "created_at", "updated_at", "submitted_on"])
            db.bulk_insert_mappings(Timesheet, chunk_clean.to_dict(orient="records"))
            total_ts += len(chunk)
        logger.info(f"Loaded {total_ts} timesheets.")
        
        # 7. Weekly Status
        logger.info("Loading weekly_status_clean.csv...")
        df_wsr = pd.read_csv(CLEANED_DATA_DIR / "weekly_status_clean.csv")
        df_wsr = clean_df_for_db(df_wsr, ["week_start_date", "week_end_date", "created_at", "updated_at"])
        db.bulk_insert_mappings(WeeklyStatus, df_wsr.to_dict(orient="records"))
        logger.info(f"Loaded {len(df_wsr)} weekly status records.")
        
        # 8. Pipeline
        logger.info("Loading pipeline_clean.csv...")
        df_pipe = pd.read_csv(CLEANED_DATA_DIR / "pipeline_clean.csv")
        df_pipe = clean_df_for_db(df_pipe, ["request_received", "original_requested_start_date", "likely_start_date"])
        db.bulk_insert_mappings(Pipeline, df_pipe.to_dict(orient="records"))
        logger.info(f"Loaded {len(df_pipe)} pipeline records.")
        
        db.commit()
        logger.info("Database seeding completed successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
