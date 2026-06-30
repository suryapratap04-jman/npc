# 03. Data Pipeline

This document describes the ETL pipeline for cleaning raw datasets and seeding the databases.

## 1. Directory Layout
- Raw Data Files: `datasets/raw/` (e.g. `employees.csv`, `skills.csv`, `competencies.csv`, `projects.csv`, `allocations.csv`, `pipeline.csv`).
- Cleaned Data Files: `datasets/cleaned/` (e.g. `employees_clean.csv`, `skills_clean.csv`, `competencies_clean.csv`, `projects_clean.csv`, `allocations_clean.csv`, `pipeline_clean.csv`).

## 2. ETL Processing Logic
Managed via `scripts/cleaning/clean_data.py`:
- **Date Standardizing**: Re-formats dates to standard `YYYY-MM-DD`.
- **Reference Checks**: Removes allocations referencing non-existent employees or projects.
- **Deduplication**: Filters duplicate profiles and resolves overlapping allocation dates.
- **Null Parsing**: Replaces missing numeric ratings with default values.

## 3. Database Seeding
After data cleaning:
- The script uses SQLAlchemy to clear existing tables and upload the clean dataset.
- It triggers vector profile rebuilding if the CSV hash files indicate changes.
