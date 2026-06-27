import pandas as pd
from pathlib import Path
from cleaning.config import CLEANING_DIR

def generate_recommendations():
    recs = [
        # Employee Features
        {
            "entity_type": "Employee",
            "feature_name": "current_utilization",
            "description": "The current sum of active project allocations for the employee as a percentage.",
            "rationale": "Helps match resource availability for new projects and avoid over-allocation.",
            "source_columns": "allocations.allocation_by_percentage, allocations.is_allocation_active",
            "calculation_formula": "Sum(allocation_by_percentage) where is_allocation_active == 1"
        },
        {
            "entity_type": "Employee",
            "feature_name": "average_billability",
            "description": "Historical percentage of time spent on billable projects vs non-billable/overhead.",
            "rationale": "Measures revenue-generating efficiency of the resource.",
            "source_columns": "timesheets.is_billable, timesheets.time",
            "calculation_formula": "Sum(time where is_billable == True) / Sum(time)"
        },
        {
            "entity_type": "Employee",
            "feature_name": "projects_completed",
            "description": "Total number of completed projects the employee has worked on.",
            "rationale": "Quantifies delivery experience and tenure on historical client tasks.",
            "source_columns": "allocations.project_id, projects.project_status",
            "calculation_formula": "Count(Distinct project_id where project_status == 'COMPLETE')"
        },
        {
            "entity_type": "Employee",
            "feature_name": "skill_count",
            "description": "Total number of unique skills registered for the employee.",
            "rationale": "Indicates resource breadth and flexibility for multi-functional tasks.",
            "source_columns": "skills.skill",
            "calculation_formula": "Count(Distinct skill)"
        },
        {
            "entity_type": "Employee",
            "feature_name": "years_experience",
            "description": "Average or maximum years of experience listed in the employee's skill set.",
            "rationale": "Provides a numeric metric of seniority and technical depth.",
            "source_columns": "skills.experience",
            "calculation_formula": "Max(experience_numeric)"
        },
        {
            "entity_type": "Employee",
            "feature_name": "average_competency_score",
            "description": "Mean rating across all capability scores from performance reviews.",
            "rationale": "Indicates qualitative stakeholder communication and execution scores.",
            "source_columns": "competencies.communication_score, competencies.stakeholder_management_score, ...",
            "calculation_formula": "Mean of non-null competency scores"
        },
        # Project Features
        {
            "entity_type": "Project",
            "feature_name": "project_duration_days",
            "description": "Total duration of the project from start to end date.",
            "rationale": "Indicates project size, scope, and capacity allocation window.",
            "source_columns": "projects.project_start_date, projects.project_end_date",
            "calculation_formula": "project_end_date - project_start_date"
        },
        {
            "entity_type": "Project",
            "feature_name": "historical_team_size",
            "description": "Unique count of employees allocated to the project historically.",
            "rationale": "Measures complexity and coordination overhead of the project.",
            "source_columns": "allocations.employee_id",
            "calculation_formula": "Count(Distinct employee_id)"
        },
        {
            "entity_type": "Project",
            "feature_name": "skill_diversity_index",
            "description": "The number of unique skills required/utilized on the project.",
            "rationale": "Determines cross-functional complexity and key technical requirements.",
            "source_columns": "allocations.employee_id, skills.skill",
            "calculation_formula": "Count(Distinct skills.skill of allocated employees)"
        },
        {
            "entity_type": "Project",
            "feature_name": "project_type_classification",
            "description": "Categorical type of project, e.g. Client Project, Internal, etc.",
            "rationale": "Useful for categorizing billability and resource matching priority.",
            "source_columns": "projects.type_of_project",
            "calculation_formula": "Direct mapping of type_of_project"
        },
        {
            "entity_type": "Project",
            "feature_name": "historical_success_rate",
            "description": "Ratio of successful completion (on time/within budget) based on Weekly Status Reports.",
            "rationale": "Indicates risks and project health, helping forecast resource needs.",
            "source_columns": "weekly_status.scope_status, weekly_status.schedule_status",
            "calculation_formula": "Percentage of weeks with green (or non-red) status values"
        }
    ]
    
    df = pd.DataFrame(recs)
    out_path = Path(CLEANING_DIR) / "feature_recommendations.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated feature recommendations at {out_path}")

if __name__ == "__main__":
    generate_recommendations()
