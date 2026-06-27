import os
import re
import sys
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any, Tuple

# Set matplotlib backend to Agg to prevent graphical UI popups on Windows
plt.switch_backend('Agg')

# Import project configurations and helpers
from cleaning.config import (
    BASE_DIR, RAW_DIR, CLEANED_DIR, CLEANING_DIR, REPORTS_DIR,
    RAW_FILES, CLEAN_FILES, TARGET_DATE_FORMAT, COMPETENCY_QUESTION_MAP,
    SKILL_MAP, SUBSKILL_MAP
)
from cleaning.utils import (
    setup_logger, load_dataset, standardize_columns, clean_text_field,
    parse_date, parse_experience, parse_utilization, standardize_skill_name
)

# Logger setup
logger = logging.getLogger("clean_data")
logger.setLevel(logging.INFO)

# We will write both to console and cleaning_log.txt
log_file = CLEANING_DIR / "cleaning_log.txt"
file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

def load_all_raw() -> Dict[str, Any]:
    logger.info("Step 1: Loading raw datasets automatically...")
    datasets = {}
    for key in RAW_FILES:
        try:
            datasets[key] = load_dataset(key)
            logger.info(f"Loaded {key} successfully.")
        except Exception as e:
            logger.error(f"Error loading {key}: {e}")
    return datasets

def run_profiling(datasets: Dict[str, Any]):
    logger.info("Step 2 & 3: Generating dataset summary and data dictionary...")
    
    summary_rows = []
    dict_rows = []
    
    for key, data in datasets.items():
        # Handle multi-sheet Excel files as distinct sub-tables for profiling
        sub_dfs = {}
        if isinstance(data, dict):
            for sname, sdf in data.items():
                sub_dfs[f"{key}_{sname.strip()}"] = sdf
        else:
            sub_dfs[key] = data
            
        for name, df in sub_dfs.items():
            rows, cols = df.shape
            # Memory usage in MB
            mem = df.memory_usage(deep=True).sum() / 1024 / 1024
            dups = df.duplicated().sum()
            
            # Identify candidate keys
            pk_candidates = []
            for col in df.columns:
                # If column has no nulls and is unique, it's a PK candidate
                if df[col].isnull().sum() == 0 and df[col].nunique() == rows and rows > 0:
                    pk_candidates.append(col)
                    
            pk_str = ", ".join(pk_candidates) if pk_candidates else "None"
            
            # Infer foreign keys
            fk_candidates = []
            col_names_lower = [str(c).lower() for c in df.columns]
            for col in df.columns:
                col_lower = str(col).lower()
                if "employee" in col_lower or "emp_id" in col_lower:
                    if col_lower not in ["employee_id", "employee id"] or "employee" in name:
                        fk_candidates.append(f"{col} -> employees.employee_id")
                if "project" in col_lower or "proj_id" in col_lower:
                    if col_lower not in ["project_id", "project id"] or "project" in name:
                        fk_candidates.append(f"{col} -> projects.project_id")
                        
            fk_str = ", ".join(fk_candidates) if fk_candidates else "None"
            
            summary_rows.append({
                "Dataset Name": name,
                "Rows": rows,
                "Columns": cols,
                "Memory Usage": f"{mem:.3f} MB",
                "Duplicate Rows": dups,
                "Primary Key Candidate": pk_str,
                "Possible Foreign Keys": fk_str
            })
            
            # Generate Data Dictionary details
            for col in df.columns:
                null_cnt = df[col].isnull().sum()
                null_pct = (null_cnt / rows * 100) if rows > 0 else 0
                unique_cnt = df[col].nunique()
                
                # Minimum and Maximum calculation
                try:
                    col_clean = df[col].dropna()
                    c_min = col_clean.min() if len(col_clean) > 0 else ""
                    c_max = col_clean.max() if len(col_clean) > 0 else ""
                except:
                    c_min, c_max = "", ""
                    
                # Safe samples list
                samples = df[col].dropna().head(3).tolist()
                samples_str = str([str(s)[:30] for s in samples])
                
                dict_rows.append({
                    "Dataset Name": name,
                    "Column Name": col,
                    "Data Type": str(df[col].dtype),
                    "Unique Count": unique_cnt,
                    "Null Count": null_cnt,
                    "Null Percentage": f"{null_pct:.2f}%",
                    "Minimum": str(c_min)[:50],
                    "Maximum": str(c_max)[:50],
                    "Example Values": samples_str
                })
                
    # Save reports
    pd.DataFrame(summary_rows).to_csv(CLEANING_DIR / "dataset_summary.csv", index=False)
    pd.DataFrame(dict_rows).to_csv(CLEANING_DIR / "data_dictionary.csv", index=False)
    logger.info("Saved dataset_summary.csv and data_dictionary.csv.")

def run_missing_value_analysis(datasets: Dict[str, Any]):
    logger.info("Step 4: Running Missing Value Analysis...")
    missing_analysis = []
    
    # We will generate a nice bar plot of null percentages
    plot_data = {}
    
    for key, data in datasets.items():
        sub_dfs = {}
        if isinstance(data, dict):
            for sname, sdf in data.items():
                sub_dfs[f"{key}_{sname.strip()}"] = sdf
        else:
            sub_dfs[key] = data
            
        for name, df in sub_dfs.items():
            total_rows = len(df)
            for col in df.columns:
                null_cnt = df[col].isnull().sum()
                null_pct = (null_cnt / total_rows * 100) if total_rows > 0 else 0
                
                if null_cnt > 0:
                    missing_analysis.append({
                        "Dataset": name,
                        "Column": col,
                        "Missing Count": null_cnt,
                        "Missing Percentage": f"{null_pct:.2f}%"
                    })
                    
                # Add to plot tracking
                plot_data[f"{name}.{col}"] = null_pct
                
    # Filter columns with missing values to plot
    plot_data = {k: v for k, v in plot_data.items() if v > 0}
    if plot_data:
        # Sort values
        sorted_plot = sorted(plot_data.items(), key=lambda x: x[1], reverse=True)
        # Limit to top 20 missing columns to prevent cluttered charts
        top_plot = sorted_plot[:20]
        
        cols = [x[0] for x in top_plot]
        pcts = [x[1] for x in top_plot]
        
        plt.figure(figsize=(12, 6))
        plt.barh(cols, pcts, color="crimson")
        plt.xlabel("Missing Percentage (%)")
        plt.ylabel("Column Name")
        plt.title("Top 20 Missing Value Percentages by Column")
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / "missing_values.png")
        plt.close()
        
        # Save null percentage plot separately as well
        plt.figure(figsize=(12, 6))
        plt.bar(range(len(pcts)), pcts, color="tomato")
        plt.xticks(range(len(pcts)), [c.split(".")[-1] for c in cols], rotation=45, ha="right")
        plt.ylabel("Null %")
        plt.title("Null Percentage of Fields")
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / "null_percentage.png")
        plt.close()
        
    logger.info("Saved missing_values.png and null_percentage.png.")

def run_duplicate_analysis(datasets: Dict[str, Any]):
    logger.info("Step 5: Running Duplicate Analysis...")
    dup_rows = []
    
    # Track metrics for visualization
    plot_dups = {}
    
    for key, data in datasets.items():
        sub_dfs = {}
        if isinstance(data, dict):
            for sname, sdf in data.items():
                sub_dfs[f"{key}_{sname.strip()}"] = sdf
        else:
            sub_dfs[key] = data
            
        for name, df in sub_dfs.items():
            exact_dups = df.duplicated().sum()
            plot_dups[name] = exact_dups
            
            # Check duplicates in key ID candidate columns
            id_dups = {}
            id_cols = [c for c in df.columns if any(k in str(c).lower() for k in ["employee_id", "employee id", "project_id", "project id", "timesheet_id", "wsr_id", "wsr_key", "surrogate_key", "rolebased_user_id"])]
            
            for id_col in id_cols:
                # Remove nulls before checking unique key duplicate
                id_clean = df[id_col].dropna()
                dups_cnt = id_clean.duplicated().sum()
                id_dups[id_col] = dups_cnt
                
            dup_rows.append({
                "Dataset": name,
                "Exact Duplicate Rows": exact_dups,
                "ID Column Duplicates": str(id_dups)
            })
            
    pd.DataFrame(dup_rows).to_csv(CLEANING_DIR / "duplicate_report.csv", index=False)
    logger.info("Saved duplicate_report.csv.")
    
    # Generate duplicate summary plot
    plt.figure(figsize=(10, 5))
    names = list(plot_dups.keys())
    counts = list(plot_dups.values())
    plt.bar(names, counts, color="teal")
    plt.ylabel("Duplicate Row Count")
    plt.title("Exact Duplicate Count by Dataset")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "duplicate_summary.png")
    plt.close()
    logger.info("Saved duplicate_summary.png.")

def run_relationship_validation(datasets: Dict[str, Any]):
    logger.info("Step 6: Running Relationship Validation...")
    
    relationship_rows = []
    
    # Master employee IDs
    df_emp = datasets["employees"]
    emp_master = set(df_emp["employee_id"].dropna().unique())
    
    # Master project IDs
    df_proj = datasets["projects"]
    proj_master = set(df_proj["project_id"].dropna().unique())
    
    # 1. Employees to Allocations relationship
    df_alloc = datasets["allocations"]
    alloc_emp_ids = df_alloc["employee_id"].dropna().astype(str).unique()
    orphaned_alloc_emps = [e for e in alloc_emp_ids if e not in emp_master]
    
    relationship_rows.append({
        "Relationship": "Employees -> Allocations",
        "Primary Table": "employees (employee_id)",
        "Foreign Table": "allocations (employee_id)",
        "Status": "Valid" if len(orphaned_alloc_emps) == 0 else "Broken References",
        "Orphaned Count": len(orphaned_alloc_emps),
        "Orphaned Key Sample": str(orphaned_alloc_emps[:5]),
        "Description": "Allocations made to non-existent employees in employees master."
    })
    
    # 2. Projects to Allocations relationship
    alloc_proj_ids = df_alloc["project_id"].dropna().astype(str).unique()
    orphaned_alloc_projs = [p for p in alloc_proj_ids if p not in proj_master]
    
    relationship_rows.append({
        "Relationship": "Projects -> Allocations",
        "Primary Table": "projects (project_id)",
        "Foreign Table": "allocations (project_id)",
        "Status": "Valid" if len(orphaned_alloc_projs) == 0 else "Broken References",
        "Orphaned Count": len(orphaned_alloc_projs),
        "Orphaned Key Sample": str(orphaned_alloc_projs[:5]),
        "Description": "Allocations made to non-existent project IDs in projects master."
    })
    
    # 3. Employees to Timesheets
    df_ts = datasets["timesheets"]
    ts_emp_ids = df_ts["employee_id"].dropna().astype(str).unique()
    orphaned_ts_emps = [e for e in ts_emp_ids if e not in emp_master]
    
    relationship_rows.append({
        "Relationship": "Employees -> Timesheets",
        "Primary Table": "employees (employee_id)",
        "Foreign Table": "timesheets (employee_id)",
        "Status": "Valid" if len(orphaned_ts_emps) == 0 else "Broken References",
        "Orphaned Count": len(orphaned_ts_emps),
        "Orphaned Key Sample": str(orphaned_ts_emps[:5]),
        "Description": "Timesheets submitted by employees missing in employees master."
    })
    
    # 4. Projects to Timesheets
    ts_proj_ids = df_ts["project_id"].dropna().astype(str).unique()
    orphaned_ts_projs = [p for p in ts_proj_ids if p not in proj_master]
    
    relationship_rows.append({
        "Relationship": "Projects -> Timesheets",
        "Primary Table": "projects (project_id)",
        "Foreign Table": "timesheets (project_id)",
        "Status": "Valid" if len(orphaned_ts_projs) == 0 else "Broken References",
        "Orphaned Count": len(orphaned_ts_projs),
        "Orphaned Key Sample": str(orphaned_ts_projs[:5]),
        "Description": "Timesheets logged for project IDs missing in projects master."
    })
    
    # 5. Projects to Weekly Status Reports (WSR)
    df_wsr = datasets["weekly_status"]
    # project_id_masked is referenced
    wsr_proj_ids = df_wsr["project_id_masked"].dropna().astype(str).unique()
    # Note: Weekly Status project IDs might be masked (e.g. CLIENT_661-683) or normal. Let's see if they match projects.
    # Since they are masked and mapped, let's see how many matches exist.
    orphaned_wsr_projs = [p for p in wsr_proj_ids if p not in proj_master]
    
    relationship_rows.append({
        "Relationship": "Projects -> Weekly Status Reports",
        "Primary Table": "projects (project_id)",
        "Foreign Table": "weekly_status (project_id_masked)",
        "Status": "Valid" if len(orphaned_wsr_projs) == 0 else "Broken References",
        "Orphaned Count": len(orphaned_wsr_projs),
        "Orphaned Key Sample": str(orphaned_wsr_projs[:5]),
        "Description": "Weekly status reports logged for projects missing in projects master (could be due to ID masking)."
    })
    
    # 6. Employees to Skills
    df_skills = datasets["skills"]
    skills_emp_ids = df_skills["employee_id"].dropna().astype(str).unique()
    orphaned_skills_emps = [e for e in skills_emp_ids if e not in emp_master]
    
    relationship_rows.append({
        "Relationship": "Employees -> Skills",
        "Primary Table": "employees (employee_id)",
        "Foreign Table": "skills (employee_id)",
        "Status": "Valid" if len(orphaned_skills_emps) == 0 else "Broken References",
        "Orphaned Count": len(orphaned_skills_emps),
        "Orphaned Key Sample": str(orphaned_skills_emps[:5]),
        "Description": "Skills listed for employee IDs missing in employees master."
    })
    
    pd.DataFrame(relationship_rows).to_csv(CLEANING_DIR / "relationship_report.csv", index=False)
    logger.info("Saved relationship_report.csv.")

def merge_competencies(comp_raw: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Consolidates the three sheets of Competency Details into a single wide DataFrame."""
    logger.info("Merging competencies sheets...")
    
    # Standardize columns and questions
    merged_dfs = []
    
    for sheet_name, df in comp_raw.items():
        logger.info(f"Processing sheet: {sheet_name}")
        df_clean = df.copy()
        
        # 1. Clean column headers
        clean_cols = []
        for col in df_clean.columns:
            # Lowcase and clean text
            col_str = str(col).strip().lower().replace("\xa0", " ").replace("\u2011", "-")
            # If it's a question, check config mapping
            mapped = False
            for question, short_name in COMPETENCY_QUESTION_MAP.items():
                if question in col_str:
                    clean_cols.append(short_name)
                    mapped = True
                    break
            
            if not mapped:
                # Handle generic score columns, e.g. Score, Score.1, Score .1
                if "score" in col_str:
                    # Let's map it dynamically by checking the preceding question's name!
                    # Preceding column should have been mapped
                    prev_col = clean_cols[-1]
                    clean_cols.append(f"{prev_col}_score")
                else:
                    # e.g., Employee ID -> employee_id
                    c = re.sub(r"[^a-z0-9_]+", "_", col_str).strip("_")
                    clean_cols.append(c)
                    
        df_clean.columns = clean_cols
        
        # Standardize ID column
        df_clean = df_clean.rename(columns={"employee_id": "employee_id", "employee_id_": "employee_id"})
        # Save cleaned sheet to merges
        merged_dfs.append(df_clean)
        
    # Combine the three dataframes
    # They have different dimensions and columns. We align on employee_id, designation, coe_dep.
    logger.info("Concatenating competency sheets and aligning columns...")
    df_combined = pd.concat(merged_dfs, ignore_index=True)
    
    # Group by employee_id, designation, coe_dep to merge rows for the same employee if they exist in multiple sheets
    # (they shouldn't, but grouping is safe)
    # We will aggregate using 'first' for non-null values
    groupby_cols = ["employee_id", "designation", "coe_dep"]
    other_cols = [c for c in df_combined.columns if c not in groupby_cols]
    
    # Fill NaN and group
    df_merged = df_combined.groupby(groupby_cols, as_index=False, dropna=False)[other_cols].first()
    
    return df_merged

def clean_data_pipeline(datasets: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    logger.info("Step 7: Performing Data Cleaning operations...")
    cleaned_dfs = {}
    current_date = pd.to_datetime("2026-06-27")
    
    # 1. EMPLOYEES CLEANING
    logger.info("Cleaning employees dataset...")
    df_emp = standardize_columns(datasets["employees"])
    # Text cleanups
    df_emp["location"] = df_emp["location"].apply(clean_text_field).fillna("Unknown")
    df_emp["job_name"] = df_emp["job_name"].apply(clean_text_field).fillna("Unknown")
    df_emp["department_name"] = df_emp["department_name"].apply(clean_text_field).fillna("Unknown")
    df_emp["manager_id"] = df_emp["manager_id"].apply(clean_text_field).fillna("Unknown")
    
    # Dates
    df_emp["date_of_join"] = df_emp["date_of_join"].apply(parse_date)
    df_emp["date_of_resignation"] = df_emp["date_of_resignation"].apply(parse_date)
    
    # Impossibles flags
    df_emp["impossible_value_flag"] = 0
    # Future join dates
    future_join_idx = df_emp[df_emp["date_of_join"] > current_date].index
    if len(future_join_idx) > 0:
        df_emp.loc[future_join_idx, "impossible_value_flag"] = 1
        logger.warning(f"Flagged {len(future_join_idx)} employees with future joining dates.")
        
    # Resignation before join
    res_before_join_idx = df_emp[df_emp["date_of_resignation"] < df_emp["date_of_join"]].index
    if len(res_before_join_idx) > 0:
        df_emp.loc[res_before_join_idx, "impossible_value_flag"] = 1
        logger.warning(f"Flagged {len(res_before_join_idx)} employees with resignation date before join date.")
        
    cleaned_dfs["employees"] = df_emp
    
    # 2. PROJECTS CLEANING
    logger.info("Cleaning projects dataset...")
    df_proj = standardize_columns(datasets["projects"])
    
    # Handle missing project_id (lost deals)
    # Give them a temporary ID to ensure referential safety but document
    null_proj_idx = df_proj[df_proj["project_id"].isnull()].index
    if len(null_proj_idx) > 0:
        logger.info(f"Projects with null project_id: {len(null_proj_idx)} (DEAL LOST). Mapping to placeholder project_ids.")
        for idx in null_proj_idx:
            # We generate a unique placeholder based on the index
            df_proj.loc[idx, "project_id"] = f"LOST_DEAL_{idx}"
            
    df_proj["project_start_date"] = df_proj["project_start_date"].apply(parse_date)
    df_proj["project_end_date"] = df_proj["project_end_date"].apply(parse_date)
    df_proj["type_of_project"] = df_proj["type_of_project"].apply(clean_text_field)
    df_proj["project_status"] = df_proj["project_status"].apply(clean_text_field)
    
    # Impossibles flag
    df_proj["impossible_value_flag"] = 0
    invalid_dates_idx = df_proj[df_proj["project_end_date"] < df_proj["project_start_date"]].index
    if len(invalid_dates_idx) > 0:
        df_proj.loc[invalid_dates_idx, "impossible_value_flag"] = 1
        logger.warning(f"Flagged {len(invalid_dates_idx)} projects where end date is before start date.")
        
    cleaned_dfs["projects"] = df_proj
    
    # 3. ALLOCATIONS CLEANING
    logger.info("Cleaning allocations dataset...")
    df_alloc = standardize_columns(datasets["allocations"])
    
    # Fill missing values
    df_alloc["employee_id"] = df_alloc["employee_id"].apply(clean_text_field).fillna("VACANT_ROLE")
    df_alloc["project_id"] = df_alloc["project_id"].apply(clean_text_field).fillna("UNKNOWN_PROJECT")
    
    df_alloc["allocated_start_date"] = df_alloc["allocated_start_date"].apply(parse_date)
    df_alloc["allocated_end_date"] = df_alloc["allocated_end_date"].apply(parse_date)
    
    df_alloc["allocation_by_percentage"] = df_alloc["allocation_by_percentage"].apply(parse_utilization)
    df_alloc["resourcing_status"] = df_alloc["resourcing_status"].apply(clean_text_field)
    
    # Flags for impossible values
    df_alloc["impossible_value_flag"] = 0
    # End date before start date
    invalid_alloc_dates = df_alloc[df_alloc["allocated_end_date"] < df_alloc["allocated_start_date"]].index
    if len(invalid_alloc_dates) > 0:
        df_alloc.loc[invalid_alloc_dates, "impossible_value_flag"] = 1
        logger.warning(f"Flagged {len(invalid_alloc_dates)} allocations where end date is before start date.")
        
    # Allocation % > 100 or negative
    invalid_alloc_pcts = df_alloc[(df_alloc["allocation_by_percentage"] > 100) | (df_alloc["allocation_by_percentage"] < 0)].index
    if len(invalid_alloc_pcts) > 0:
        df_alloc.loc[invalid_alloc_pcts, "impossible_value_flag"] = 1
        logger.warning(f"Flagged {len(invalid_alloc_pcts)} allocations with invalid percentage values.")
        
    cleaned_dfs["allocations"] = df_alloc
    
    # 4. TIMESHEETS CLEANING
    logger.info("Cleaning timesheets dataset...")
    df_ts = standardize_columns(datasets["timesheets"])
    
    df_ts["employee_id"] = df_ts["employee_id"].apply(clean_text_field)
    # Check for placeholder employee '0' and mark/flag
    placeholder_emp_idx = df_ts[df_ts["employee_id"] == "0"].index
    if len(placeholder_emp_idx) > 0:
        logger.warning(f"Flagged {len(placeholder_emp_idx)} timesheets with placeholder employee_id = '0'.")
        df_ts.loc[placeholder_emp_idx, "employee_id"] = "UNKNOWN_EMPLOYEE"
        
    df_ts["project_id"] = df_ts["project_id"].apply(clean_text_field).fillna("UNKNOWN_PROJECT")
    df_ts["date"] = df_ts["date"].apply(parse_date)
    df_ts["created_at"] = df_ts["created_at"].apply(parse_date)
    df_ts["updated_at"] = df_ts["updated_at"].apply(parse_date)
    
    # Flag impossible values
    df_ts["impossible_value_flag"] = 0
    negative_hours = df_ts[df_ts["time"] < 0].index
    if len(negative_hours) > 0:
        df_ts.loc[negative_hours, "impossible_value_flag"] = 1
        logger.warning(f"Flagged {len(negative_hours)} timesheet hours as negative.")
        
    cleaned_dfs["timesheets"] = df_ts
    
    # 5. SKILLS CLEANING
    logger.info("Cleaning skills dataset...")
    df_skills = standardize_columns(datasets["skills"])
    
    df_skills["skill"] = df_skills["skill"].apply(standardize_skill_name)
    df_skills["subskill"] = df_skills["subskill"].apply(standardize_skill_name)
    df_skills["designation"] = df_skills["designation"].apply(clean_text_field)
    df_skills["coe"] = df_skills["coe"].apply(clean_text_field)
    df_skills["coe_skill"] = df_skills["coe_skill"].apply(clean_text_field)
    
    # Convert Experience string to numeric midpoint
    df_skills["experience_numeric"] = df_skills["experience"].apply(parse_experience)
    
    cleaned_dfs["skills"] = df_skills
    
    # 6. COMPETENCIES CLEANING
    logger.info("Cleaning competencies dataset (merging Excel sheets)...")
    # Call merge competencies helper
    df_comp = merge_competencies(datasets["competencies"])
    
    # Standardize columns for the merged output
    df_comp = standardize_columns(df_comp)
    df_comp["employee_id"] = df_comp["employee_id"].apply(clean_text_field)
    df_comp["designation"] = df_comp["designation"].apply(clean_text_field)
    df_comp["coe_dep"] = df_comp["coe_dep"].apply(clean_text_field)
    
    # Map score columns explicitly using standardize
    # Let's clean text in status columns (Yes/No)
    status_cols = [c for c in df_comp.columns if c.endswith("_status") or "management" in c or "guidance" in c or "functional" in c or "communication" in c or "navigation" in c or "articulation" in c or "architecture" in c or "planning" in c]
    status_cols = [c for c in status_cols if "score" not in c]
    for sc in status_cols:
        df_comp[sc] = df_comp[sc].apply(clean_text_field)
        
    cleaned_dfs["competencies"] = df_comp
    
    # 7. PIPELINE CLEANING
    logger.info("Cleaning pipeline dataset (Forecast sheet)...")
    # The pipeline Excel contains multiple sheets. The Forecast is the primary pipeline resource request sheet.
    df_pipe_raw = datasets["pipeline"]["Forecast"]
    df_pipe = standardize_columns(df_pipe_raw)
    
    # Format date columns
    df_pipe["request_received"] = df_pipe["request_received"].apply(parse_date)
    df_pipe["original_requested_start_date"] = df_pipe["original_requested_start_date"].apply(parse_date)
    df_pipe["likely_start_date"] = df_pipe["likely_start_date"].apply(parse_date)
    
    # Fill descriptive categories
    df_pipe["cluster"] = df_pipe["cluster"].fillna(-1).astype(int)
    df_pipe["client"] = df_pipe["client"].apply(clean_text_field).fillna("Unknown")
    df_pipe["status"] = df_pipe["status"].apply(clean_text_field).fillna("Unknown")
    df_pipe["priority"] = df_pipe["priority"].apply(clean_text_field).fillna("Medium")
    
    cleaned_dfs["pipeline"] = df_pipe
    
    # 8. WEEKLY STATUS CLEANING
    logger.info("Cleaning weekly status dataset...")
    df_wsr = standardize_columns(datasets["weekly_status"])
    
    df_wsr["week_start_date"] = df_wsr["week_start_date"].apply(parse_date)
    df_wsr["week_end_date"] = df_wsr["week_end_date"].apply(parse_date)
    df_wsr["created_at"] = df_wsr["created_at"].apply(parse_date)
    df_wsr["updated_at"] = df_wsr["updated_at"].apply(parse_date)
    
    # Text cleanups
    for col in ["scope_status", "schedule_status", "quality_status", "csat_status", "team_status"]:
        df_wsr[col] = df_wsr[col].apply(clean_text_field)
        
    cleaned_dfs["weekly_status"] = df_wsr
    
    return cleaned_dfs

def compute_data_quality_report(datasets_raw: Dict[str, Any], datasets_clean: Dict[str, pd.DataFrame]):
    logger.info("Step 8: Generating Data Quality Report...")
    
    quality_rows = []
    
    # Master records for referential checks
    emp_master = set(datasets_clean["employees"]["employee_id"].dropna().unique())
    proj_master = set(datasets_clean["projects"]["project_id"].dropna().unique())
    
    for key, df in datasets_clean.items():
        total_rows = len(df)
        if total_rows == 0:
            quality_rows.append({
                "Dataset": key,
                "Completeness Score": 100,
                "Consistency Score": 100,
                "Integrity Score": 100,
                "Uniqueness Score": 100,
                "Quality Score": 100
            })
            continue
            
        # 1. Completeness: check null percentage of critical columns
        # Avoid counting non_active or reservation columns that are naturally sparse
        critical_cols = [c for c in df.columns if not any(x in c for x in ["resignation", "proposition", "tech_coe", "manager_id", "job_name", "pru_id", "submitted_on", "is_billable", "type", "comments"])]
        null_counts = df[critical_cols].isnull().sum().sum()
        total_cells = total_rows * len(critical_cols)
        completeness = (1.0 - (null_counts / total_cells)) * 100
        
        # 2. Consistency: check flags for impossible values or out-of-order dates
        consistency = 100.0
        if "impossible_value_flag" in df.columns:
            imp_cnt = df["impossible_value_flag"].sum()
            consistency = (1.0 - (imp_cnt / total_rows)) * 100
            
        # 3. Uniqueness: check duplicates of primary keys or general rows
        uniqueness = 100.0
        pk_cols = []
        if key == "employees":
            pk_cols = ["employee_id"]
        elif key == "projects":
            pk_cols = ["project_id"]
        elif key == "timesheets":
            pk_cols = ["timesheet_surrogate_key"]
        elif key == "weekly_status":
            pk_cols = ["wsr_key"]
        elif key == "competencies":
            pk_cols = ["employee_id"]
            
        if pk_cols:
            pk_dups = df[pk_cols].duplicated().sum()
            uniqueness = (1.0 - (pk_dups / total_rows)) * 100
        else:
            # Fallback to general duplicates check
            dups = df.duplicated().sum()
            uniqueness = (1.0 - (dups / total_rows)) * 100
            
        # 4. Integrity: check broken foreign keys references
        integrity = 100.0
        orphans = 0
        
        if key == "allocations":
            emp_orphans = df[~df["employee_id"].isin(emp_master | {"VACANT_ROLE"})].shape[0]
            proj_orphans = df[~df["project_id"].isin(proj_master | {"UNKNOWN_PROJECT"})].shape[0]
            orphans = emp_orphans + proj_orphans
            integrity = (1.0 - (orphans / (total_rows * 2))) * 100
        elif key == "timesheets":
            emp_orphans = df[~df["employee_id"].isin(emp_master | {"UNKNOWN_EMPLOYEE"})].shape[0]
            proj_orphans = df[~df["project_id"].isin(proj_master | {"UNKNOWN_PROJECT"})].shape[0]
            orphans = emp_orphans + proj_orphans
            integrity = (1.0 - (orphans / (total_rows * 2))) * 100
        elif key == "skills":
            emp_orphans = df[~df["employee_id"].isin(emp_master)].shape[0]
            orphans = emp_orphans
            integrity = (1.0 - (orphans / total_rows)) * 100
        elif key == "competencies":
            emp_orphans = df[~df["employee_id"].isin(emp_master)].shape[0]
            orphans = emp_orphans
            integrity = (1.0 - (orphans / total_rows)) * 100
            
        # Overall Quality Score: simple average of indicators
        quality_score = (completeness + consistency + uniqueness + integrity) / 4.0
        
        quality_rows.append({
            "Dataset Name": key,
            "Completeness": f"{completeness:.2f}",
            "Consistency": f"{consistency:.2f}",
            "Accuracy": f"{consistency:.2f}", # Map Consistency to Accuracy
            "Uniqueness": f"{uniqueness:.2f}",
            "Validity": f"{consistency:.2f}",   # Map consistency to Validity
            "Integrity": f"{integrity:.2f}",
            "Quality Score": f"{quality_score:.2f}"
        })
        
    quality_df = pd.DataFrame(quality_rows)
    quality_df.to_csv(CLEANING_DIR / "quality_report.csv", index=False)
    # Print nice table to log
    logger.info("\n" + "="*60 + "\nDATA QUALITY REPORT\n" + "="*60)
    logger.info("\n" + quality_df.to_string(index=False))
    logger.info("Saved quality_report.csv.")

def generate_visualizations(datasets_raw: Dict[str, Any], datasets_clean: Dict[str, pd.DataFrame]):
    logger.info("Step 13: Generating Visualization Graphs...")
    
    # 1. Dataset Sizes (Row count)
    plt.figure(figsize=(10, 5))
    sizes = {k: len(v) for k, v in datasets_clean.items()}
    plt.bar(sizes.keys(), sizes.values(), color="dodgerblue")
    plt.ylabel("Row Count")
    plt.title("Row Count of Cleaned Datasets")
    plt.xticks(rotation=45, ha="right")
    plt.yscale('log')  # timesheets is very large
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "dataset_sizes.png")
    plt.close()
    
    # 2. Top Skills by Employee Count
    plt.figure(figsize=(10, 5))
    df_skills = datasets_clean["skills"]
    top_skills = df_skills["skill"].value_counts().head(10)
    plt.barh(top_skills.index, top_skills.values, color="mediumseagreen")
    plt.xlabel("Skill Occurrence Count")
    plt.title("Top 10 Standardized Skills")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "top_skills.png")
    plt.close()
    
    # 3. Top Competencies Distribution (Average Scores)
    plt.figure(figsize=(10, 5))
    df_comp = datasets_clean["competencies"]
    score_cols = [c for c in df_comp.columns if c.endswith("_score")]
    if score_cols:
        avg_scores = df_comp[score_cols].mean().sort_values(ascending=False)
        plt.bar(avg_scores.index, avg_scores.values, color="mediumorchid")
        plt.ylabel("Average Rating (0-5)")
        plt.title("Average Competency Score by Skill Domain")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / "top_competencies.png")
        plt.close()
        
    # 4. Allocation Distribution
    plt.figure(figsize=(10, 5))
    df_alloc = datasets_clean["allocations"]
    plt.hist(df_alloc["allocation_by_percentage"].dropna(), bins=10, color="orange", edgecolor="black", alpha=0.7)
    plt.xlabel("Allocation %")
    plt.ylabel("Frequency")
    plt.title("Distribution of Project Allocation Percentages")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "allocation_distribution.png")
    plt.close()
    
    logger.info("Saved all visualization graphs to cleaning/reports/.")

def export_clean_data(datasets_clean: Dict[str, pd.DataFrame]):
    logger.info("Step 11: Exporting Clean Data to cleanedData/ directory...")
    for key, df in datasets_clean.items():
        fname = CLEAN_FILES[key]
        out_path = CLEANED_DIR / fname
        df.to_csv(out_path, index=False)
        logger.info(f"Exported cleaned dataset: {fname} (Shape: {df.shape})")

def main():
    setup_logger()
    logger.info("Starting Data Discovery and Cleaning Pipeline...")
    
    # Load
    raw_dfs = load_all_raw()
    
    # Summarize & Dictionary
    run_profiling(raw_dfs)
    
    # Missing Value Analysis
    run_missing_value_analysis(raw_dfs)
    
    # Duplicate Analysis
    run_duplicate_analysis(raw_dfs)
    
    # Relationship validation
    run_relationship_validation(raw_dfs)
    
    # Perform cleaning
    cleaned_dfs = clean_data_pipeline(raw_dfs)
    
    # Compute Quality Report
    compute_data_quality_report(raw_dfs, cleaned_dfs)
    
    # Generate Visualizations
    generate_visualizations(raw_dfs, cleaned_dfs)
    
    # Export
    export_clean_data(cleaned_dfs)
    
    logger.info("Data Discovery and Cleaning Pipeline completed successfully!")

if __name__ == "__main__":
    main()
