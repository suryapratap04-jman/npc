import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "datasets" / "raw"
CLEANED_DIR = BASE_DIR / "datasets" / "cleaned"
CLEANING_DIR = BASE_DIR / "scripts" / "cleaning"
REPORTS_DIR = CLEANING_DIR / "reports"

# Ensure directories exist
CLEANED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Raw files mapping
RAW_FILES = {
    "employees": "01. 260624 employee_details.csv",
    "projects": "02. 260624 project_details.csv",
    "allocations": "03. 260623_Project_Allocation_Details.csv",
    "timesheets": "04. 260624 timesheet_details_2026.csv.csv",
    "skills": "05. 260624 Skill_Data.xlsx",
    "competencies": "06. 260623_Competency_Details.xlsx",
    "pipeline": "07. 260624_Pipeline_Details.xlsx",
    "weekly_status": "09. 260624_Project_Weekly_Status_Details.csv.csv"
}

# Clean output names
CLEAN_FILES = {
    "employees": "employees_clean.csv",
    "projects": "projects_clean.csv",
    "allocations": "allocations_clean.csv",
    "timesheets": "timesheets_clean.csv",
    "skills": "skills_clean.csv",
    "competencies": "competencies_clean.csv",
    "pipeline": "pipeline_clean.csv",
    "weekly_status": "weekly_status_clean.csv"
}

# Date format parsed/standardized
TARGET_DATE_FORMAT = "%Y-%m-%d"
RAW_DATE_FORMAT = "%d-%m-%Y"

# Competency column mappings to map long questions to short column names
COMPETENCY_QUESTION_MAP = {
    # Solution Enabler
    "demonstrates strong capability to manage and influence client stakeholders effectively across varying seniority levels": "stakeholder_management",
    "operates in a consultative / advisory capacity, guiding clients toward optimal solutions": "consultative_guidance",
    "brings strong techno-functional consulting expertise aligned to jman's delivery context": "techno_functional",
    "brings strong techno‑functional consulting expertise aligned to jman’s delivery context": "techno_functional", # handles non-breaking hyphen variant
    "communicates with clarity, with the ability to confidently explain complex concepts in a simple, structured manner": "communication",
    "effectively navigates ambiguity and delivery-stage complexity, maintaining composure and driving outcomes under pressure": "ambiguity_navigation",
    "effectively navigates ambiguity and delivery‑stage complexity, maintaining composure and driving outcomes under pressure": "ambiguity_navigation",

    # Solution Consultant
    "effectivetly articulates jman's capabilities and offerrings in terms of delivery and outcome, and leads on advancing our offerring.": "capabilities_articulation",
    "effectivetly articulates jman's capabilities and offerrings in terms of delivery and outcome, and leads on advancing our offerring. ": "capabilities_articulation", # handles trailing space
    "expert in estimating and designing solution architectures. drive team to meet sprint plan, deadlines and best practices; instrumental in making the team meet the expected deadlines without compromising on quality": "solution_architecture",
    "good at estimating and drafting project plans. define sprints and story points. advocate and implement agile squad model.": "project_planning",
    "good at estimating and drafting project plans. define sprints and story points. advocate and implement agile squad model. ": "project_planning"
}

# Skill standardizations mapping (case-insensitive keys, standardized values)
SKILL_MAP = {
    "python": "Python",
    "python and pyspark libraries": "Python",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "sql": "SQL",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "kubernetes": "Kubernetes",
    "docker": "Docker",
    "pyspark": "PySpark",
    "databricks": "Databricks",
    "snowflake": "Snowflake",
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "excel": "Excel",
}

# Subskill specific maps
SUBSKILL_MAP = {
    "python": "Python",
    "sql": "SQL",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
}
