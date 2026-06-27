import os
import sys
import pandas as pd
from pathlib import Path
from cleaning.config import CLEANED_DIR, CLEANING_DIR, CLEAN_FILES

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_validation():
    report_lines = []
    def log_val(msg):
        print(msg)
        report_lines.append(msg)
        
    log_val("DATASET POST-CLEANING VALIDATION REPORT")
    log_val("=======================================")
    
    validation_passed = True
    
    # 1. Check all files exist
    log_val("\nChecking if cleaned files exist...")
    all_files_exist = True
    for key, fname in CLEAN_FILES.items():
        path = CLEANED_DIR / fname
        if path.exists():
            log_val(f"✔ {fname} exists.")
        else:
            log_val(f"✘ {fname} DOES NOT exist!")
            all_files_exist = False
            validation_passed = False
            
    if not all_files_exist:
        log_val("Halting validation: Clean files are missing!")
        write_report(report_lines)
        return
        
    # Load all cleaned files
    dfs = {k: pd.read_csv(CLEANED_DIR / CLEAN_FILES[k]) for k in CLEAN_FILES}
    
    # 2. Check unique Primary Keys
    log_val("\nChecking uniqueness and null count of Primary Keys...")
    pk_checks = [
        ("employees", "employee_id"),
        ("projects", "project_id"),
        ("timesheets", "timesheet_surrogate_key"),
        ("weekly_status", "wsr_key"),
        ("competencies", "employee_id")
    ]
    
    for key, pk in pk_checks:
        df = dfs[key]
        nulls = df[pk].isnull().sum()
        dups = df[pk].duplicated().sum()
        if nulls == 0 and dups == 0:
            log_val(f"✔ PK {pk} in dataset {key} is unique and has 0 nulls.")
        else:
            log_val(f"✘ PK {pk} in dataset {key} has {nulls} nulls and {dups} duplicates!")
            validation_passed = False
            
    # 3. Check Date Formats (asserting YYYY-MM-DD pattern)
    log_val("\nChecking Date format patterns (expecting YYYY-MM-DD)...")
    date_cols = {
        "employees": ["date_of_join", "date_of_resignation"],
        "projects": ["project_start_date", "project_end_date"],
        "allocations": ["allocated_start_date", "allocated_end_date"],
        "timesheets": ["date", "created_at", "updated_at"],
        "pipeline": ["request_received", "original_requested_start_date", "likely_start_date"],
        "weekly_status": ["week_start_date", "week_end_date", "created_at", "updated_at"]
    }
    
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"
    for key, cols in date_cols.items():
        df = dfs[key]
        for col in cols:
            # Check non-null dates
            non_null_dates = df[col].dropna().astype(str)
            if len(non_null_dates) == 0:
                continue
            invalid_format_count = (~non_null_dates.str.match(date_pattern)).sum()
            if invalid_format_count == 0:
                log_val(f"✔ Dates in {key}.{col} are standardized correctly.")
            else:
                log_val(f"✘ Column {key}.{col} has {invalid_format_count} dates not matching YYYY-MM-DD format! Sample: {non_null_dates[~non_null_dates.str.match(date_pattern)].head(2).tolist()}")
                validation_passed = False
                
    # 4. Check Allocation Ranges
    log_val("\nChecking allocation percentages ranges (0 - 100)...")
    df_alloc = dfs["allocations"]
    out_of_range = df_alloc[(df_alloc["allocation_by_percentage"] < 0) | (df_alloc["allocation_by_percentage"] > 100)]
    if len(out_of_range) == 0:
        log_val("✔ All allocation percentages are within valid [0, 100] range.")
    else:
        log_val(f"✘ Found {len(out_of_range)} allocation records with percentages outside [0, 100]!")
        validation_passed = False
        
    # 5. Check Referential Integrity
    log_val("\nChecking Referential Integrity...")
    emp_ids = set(dfs["employees"]["employee_id"].dropna().unique())
    proj_ids = set(dfs["projects"]["project_id"].dropna().unique())
    
    # Allocations integrity
    alloc_emp_diff = set(df_alloc["employee_id"].dropna().unique()) - emp_ids - {"VACANT_ROLE"}
    alloc_proj_diff = set(df_alloc["project_id"].dropna().unique()) - proj_ids - {"UNKNOWN_PROJECT"}
    
    if len(alloc_emp_diff) == 0:
        log_val("✔ allocations.employee_id referential check passed.")
    else:
        log_val(f"✘ Allocations references non-existent employees: {list(alloc_emp_diff)[:5]}")
        validation_passed = False
        
    if len(alloc_proj_diff) == 0:
        log_val("✔ allocations.project_id referential check passed.")
    else:
        log_val(f"✘ Allocations references non-existent projects: {list(alloc_proj_diff)[:5]}")
        validation_passed = False
        
    # Timesheets integrity
    df_ts = dfs["timesheets"]
    ts_emp_diff = set(df_ts["employee_id"].dropna().unique()) - emp_ids - {"UNKNOWN_EMPLOYEE"}
    ts_proj_diff = set(df_ts["project_id"].dropna().unique()) - proj_ids - {"UNKNOWN_PROJECT"}
    
    if len(ts_emp_diff) == 0:
        log_val("✔ timesheets.employee_id referential check passed.")
    else:
        log_val(f"✘ Timesheets references non-existent employees: {list(ts_emp_diff)[:5]}")
        validation_passed = False
        
    if len(ts_proj_diff) == 0:
        log_val("✔ timesheets.project_id referential check passed.")
    else:
        log_val(f"✘ Timesheets references non-existent projects: {list(ts_proj_diff)[:5]}")
        validation_passed = False
        
    # Skills integrity
    df_skills = dfs["skills"]
    skills_emp_diff = set(df_skills["employee_id"].dropna().unique()) - emp_ids
    if len(skills_emp_diff) == 0:
        log_val("✔ skills.employee_id referential check passed.")
    else:
        log_val(f"✘ Skills references non-existent employees: {list(skills_emp_diff)[:5]}")
        validation_passed = False
        
    # Competencies integrity
    df_comp = dfs["competencies"]
    comp_emp_diff = set(df_comp["employee_id"].dropna().unique()) - emp_ids
    if len(comp_emp_diff) == 0:
        log_val("✔ competencies.employee_id referential check passed.")
    else:
        log_val(f"✘ Competencies references non-existent employees: {list(comp_emp_diff)[:5]}")
        validation_passed = False
        
    # 6. Conclusion
    log_val("\n" + "="*40)
    if validation_passed:
        log_val("STATUS: VALIDATION SUCCESSFUL (All checks passed!)")
    else:
        log_val("STATUS: VALIDATION FAILED (Check errors listed above)")
    log_val("="*40)
    
    write_report(report_lines)
    
def write_report(lines):
    report_path = CLEANING_DIR / "validation_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"Validation report saved to {report_path}")

if __name__ == "__main__":
    run_validation()
