import logging
from typing import Dict, Any, List
from collections import defaultdict
from sqlalchemy.orm import Session
from backend.database.models import Allocation, Skill

logger = logging.getLogger("health_recommendation_engine")

class ActionRecommendationEngine:
    def __init__(self, db: Session):
        self.db = db

    def generate_recommendations(
        self,
        project_id: str,
        features: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        utilization_analysis: Dict[str, Any],
        billability_analysis: Dict[str, Any],
        rampdown_analysis: Dict[str, Any],
        team_employee_ids: List[str]
    ) -> List[str]:
        """
        Generates concrete, actionable recommendations based on health analysis.
        """
        actions = []

        # 1. Schedule risks
        delay_days = features.get("delay_days", 0)
        sched_status = str(features.get("schedule_status", "Green")).upper().strip()
        
        if "RED" in sched_status or delay_days > 14:
            actions.append(f"Escalate project schedule delay of {delay_days} days immediately with stakeholders.")
        elif "AMBER" in sched_status or delay_days > 0:
            actions.append(f"Review upcoming deliverables to address active schedule delay of {delay_days} days.")

        # 2. Scope creep / Delivery risks
        scope_status = str(features.get("scope_status", "Green")).upper().strip()
        quality_status = str(features.get("quality_status", "Green")).upper().strip()
        csat_status = str(features.get("csat_status", "Green")).upper().strip()
        
        if "RED" in scope_status:
            actions.append("Initiate scope review; freeze feature updates to prevent further scope creep.")
        if "RED" in quality_status or "RED" in csat_status:
            actions.append("Escalate quality/CSAT risk. Conduct a post-mortem review of deliverables.")

        # 3. Overallocation Burnout Mitigation
        if utilization_analysis.get("overallocated_count", 0) > 0:
            overallocated_emps = []
            if team_employee_ids:
                global_allocs = self.db.query(Allocation).filter(
                    Allocation.employee_id.in_(team_employee_ids),
                    Allocation.is_allocation_active == 1
                ).all()
                global_util = defaultdict(float)
                for ga in global_allocs:
                    global_util[ga.employee_id] += float(ga.allocation_by_percentage or 0.0)
                
                for emp_id, util in global_util.items():
                    if util > 100.0:
                        overallocated_emps.append(emp_id)
            
            for emp_id in overallocated_emps:
                actions.append(f"Reduce allocation for Employee {emp_id} to prevent burnout (currently overallocated).")

        # 4. Underutilization & Reassignments
        if rampdown_analysis.get("is_suitable", False) or utilization_analysis.get("underutilized_count", 0) > 0:
            underutilized_emps = []
            if team_employee_ids:
                global_allocs = self.db.query(Allocation).filter(
                    Allocation.employee_id.in_(team_employee_ids),
                    Allocation.is_allocation_active == 1
                ).all()
                global_util = defaultdict(float)
                for ga in global_allocs:
                    global_util[ga.employee_id] += float(ga.allocation_by_percentage or 0.0)
                
                for emp_id, util in global_util.items():
                    if util < 40.0:
                        underutilized_emps.append(emp_id)

            for emp_id in underutilized_emps:
                actions.append(f"Reassign Employee {emp_id} to another project due to underutilization.")

        # 5. Billability audit
        bill_pct = billability_analysis.get("percentage", 100.0)
        shadow_cnt = billability_analysis.get("shadow_resources_count", 0)
        
        if bill_pct < 70.0:
            actions.append(f"Audit timesheets immediately; overall project recovery is poor ({bill_pct:.1f}%).")
        if shadow_cnt > 0:
            actions.append(f"Investigate {shadow_cnt} shadow resources logging zero billable hours in past 2 weeks.")

        # 6. Ramp-Down release
        if rampdown_analysis.get("is_suitable", False):
            release_count = rampdown_analysis.get("estimated_release_count", 0)
            release_dt = rampdown_analysis.get("earliest_release_date")
            actions.append(f"Initiate ramp-down: release {release_count} resources on or before {release_dt}.")

        # General default fallback if everything is healthy
        if not actions:
            actions.append("Maintain current staffing levels. Monitor weekly deliverables.")

        return actions
