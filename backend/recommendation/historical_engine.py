import logging
import datetime
from typing import Dict, Any, List, Set
from sqlalchemy.orm import Session
from backend.database.models import Allocation, Project

logger = logging.getLogger("historical_engine")

class HistoricalEngine:
    def __init__(self, db: Session, config: Dict[str, Any]):
        self.db = db
        self.config = config
        self.employee_metrics = {}

    def precompute_metrics(self, employee_ids: List[str], current_project_id: str, required_skills: List[str], project_type: str):
        """
        Queries all allocations for the employees and computes pre-aggregated historical experience stats.
        """
        if not employee_ids:
            return

        # 1. Fetch all allocations for these employees
        allocations = self.db.query(Allocation).filter(
            Allocation.employee_id.in_(employee_ids)
        ).all()

        # Group allocations by employee
        emp_allocs = {emp_id: [] for emp_id in employee_ids}
        for alloc in allocations:
            if alloc.employee_id in emp_allocs:
                emp_allocs[alloc.employee_id].append(alloc)

        # 2. Fetch all referenced projects to map their metadata
        referenced_project_ids = {a.project_id for a in allocations if a.project_id}
        projects = []
        if referenced_project_ids:
            projects = self.db.query(Project).filter(
                Project.project_id.in_(list(referenced_project_ids))
            ).all()
        projects_map = {p.project_id: p for p in projects}

        # Get details of current project if available
        curr_project = None
        if current_project_id:
            curr_project = self.db.query(Project).filter(Project.project_id == current_project_id).first()

        curr_client_id = curr_project.client_id if curr_project else None
        curr_coe = curr_project.tech_coe if curr_project else None

        # 3. Compute stats for each employee
        for emp_id, allocs in emp_allocs.items():
            if not allocs:
                # Cold-start fallback
                self.employee_metrics[emp_id] = {
                    "score": 50.0, # soft fallback
                    "similar_project_count": 0,
                    "similar_tech_count": 0,
                    "similar_domain_count": 0,
                    "similar_client_count": 0,
                    "avg_duration_days": 0.0,
                    "historical_completion_rate": 1.0
                }
                continue

            similar_client_count = 0
            similar_domain_count = 0
            similar_tech_count = 0
            similar_project_count = 0
            durations = []
            completed_allocations_count = 0

            for alloc in allocs:
                proj = projects_map.get(alloc.project_id)
                if not proj:
                    continue

                similar_project_count += 1

                # Client match
                if curr_client_id and proj.client_id == curr_client_id:
                    similar_client_count += 1

                # Domain match
                if project_type:
                    p_type = project_type.lower().strip()
                    proj_type_val = (proj.type_of_project or "").lower().strip()
                    proj_prop_coe = (proj.proposition_coe or "").lower().strip()
                    if p_type in proj_type_val or p_type in proj_prop_coe:
                        similar_domain_count += 1

                # Technology match
                if curr_coe and proj.tech_coe:
                    if curr_coe.lower().strip() == proj.tech_coe.lower().strip():
                        similar_tech_count += 1
                elif required_skills and proj.tech_coe:
                    proj_coe_lower = proj.tech_coe.lower().strip()
                    if any(s.lower().strip() in proj_coe_lower for s in required_skills):
                        similar_tech_count += 1

                # Duration in days
                if alloc.allocated_start_date and alloc.allocated_end_date:
                    dur = (alloc.allocated_end_date - alloc.allocated_start_date).days
                    durations.append(max(0, dur))

                # Completion check
                res_status = (alloc.resourcing_status or "").upper().strip()
                if "COMPLETED" in res_status or alloc.is_allocation_active == 0:
                    completed_allocations_count += 1

            avg_dur = sum(durations) / len(durations) if durations else 0.0
            comp_rate = completed_allocations_count / len(allocs) if allocs else 1.0

            # Calculate Historical Experience Score
            score = (
                20.0 * min(similar_client_count, 3.0) +
                20.0 * min(similar_domain_count, 3.0) +
                20.0 * min(similar_tech_count, 3.0) +
                20.0 * min(avg_dur / 180.0, 1.0) +
                20.0 * comp_rate
            )
            score = round(max(0.0, min(100.0, score)), 2)

            self.employee_metrics[emp_id] = {
                "score": score,
                "similar_project_count": similar_project_count,
                "similar_tech_count": similar_tech_count,
                "similar_domain_count": similar_domain_count,
                "similar_client_count": similar_client_count,
                "avg_duration_days": round(avg_dur, 2),
                "historical_completion_rate": round(comp_rate, 2)
            }

    def calculate_score(self, emp_id: str) -> float:
        """
        Returns the precomputed historical success score for a candidate.
        """
        metrics = self.employee_metrics.get(emp_id)
        if metrics:
            return metrics["score"]
        return 50.0  # soft fallback if not precomputed
