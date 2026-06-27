import logging
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session

from backend.database.models import Project, Allocation, Employee, Skill
from backend.forecast.demand_feature_builder import DemandFeatureBuilder

logger = logging.getLogger("redeployment_engine")

class RedeploymentEngine:
    def __init__(self, db: Session, feature_builder: DemandFeatureBuilder):
        self.db = db
        self.feature_builder = feature_builder

    def get_candidate_redeployments(self, 
                                    expected_start_date_str: str, 
                                    required_roles: List[str], 
                                    required_skills: List[str]) -> Dict[str, Any]:
        """
        Identifies and ranks active employees who have allocations ramping down
        near the project start date, sorted by skill match score.
        """
        try:
            start_date = date.fromisoformat(expected_start_date_str)
        except Exception:
            start_date = date(2026, 8, 15)  # default fallback
            
        emp_roles = self.feature_builder.load_employee_roles()
        
        # 1. Fetch skills per employee for skill-match scoring
        skills = self.db.query(Skill).all()
        skills_by_emp: Dict[str, Set[str]] = {}
        for s in skills:
            if s.employee_id and s.skill:
                skills_by_emp.setdefault(s.employee_id, set()).add(s.skill.lower().strip())
                
        # 2. Query allocations that end before or around the project start date
        # Candidates are employees whose allocations are active now but end before the start date + 14 days
        # We query all active allocations
        allocations = self.db.query(Allocation).filter(
            Allocation.is_active_version == 1,
            Allocation.is_allocation_active == 1
        ).all()
        
        # Track latest ending allocation per employee
        latest_alloc_by_emp: Dict[str, Allocation] = {}
        for a in allocations:
            if not a.employee_id:
                continue
            cur_latest = latest_alloc_by_emp.get(a.employee_id)
            if not cur_latest:
                latest_alloc_by_emp[a.employee_id] = a
            else:
                a_end = a.allocated_end_date or date(2099, 12, 31)
                cur_end = cur_latest.allocated_end_date or date(2099, 12, 31)
                if a_end > cur_end:
                    latest_alloc_by_emp[a.employee_id] = a

        redeployment_options = []
        role_key_map = {
            "Architect": "architect",
            "Consultant": "consultant",
            "Backend Engineer": "backend",
            "Frontend Engineer": "frontend",
            "Data Engineer": "data_engineer",
            "Data Scientist": "data_scientist",
            "QA": "qa",
            "DevOps": "devops"
        }
        
        for emp_id, a in latest_alloc_by_emp.items():
            role = emp_roles.get(emp_id)
            if not role:
                continue
                
            role_key = role_key_map.get(role)
            if not role_key or role_key not in required_roles:
                continue
                
            a_end = a.allocated_end_date
            # Check if availability is within range: ends before start_date or within 14 days after (transitional)
            # If a_end is None, it means indefinite allocation (not a candidate for redeployment)
            if not a_end:
                continue
                
            # Candidates must become available within [-60, +15] days of the expected start date
            days_diff = (a_end - start_date).days
            if -60 <= days_diff <= 15:
                # Calculate skill match score
                emp_skills = skills_by_emp.get(emp_id, set())
                match_score = 0.0
                if required_skills:
                    overlap = emp_skills.intersection({s.lower().strip() for s in required_skills})
                    match_score = len(overlap) / len(required_skills)
                else:
                    match_score = 1.0  # default if no skills specified
                    
                redeployment_options.append({
                    "employee_id": emp_id,
                    "name": f"Employee {emp_id[-6:]}" if len(emp_id) > 6 else emp_id,
                    "role": role_key,
                    "current_project_id": a.project_id,
                    "project_end_date": a_end.isoformat(),
                    "available_from": a_end.isoformat(),
                    "match_score": round(match_score, 2)
                })
                
        # Sort options: highest match score first, then earliest available
        redeployment_options.sort(key=lambda x: (-x["match_score"], x["available_from"]))
        
        # Group list of candidate employee IDs per role for simple lookup by service/hiring engines
        candidates_by_role: Dict[str, List[str]] = {r: [] for r in required_roles}
        for opt in redeployment_options:
            candidates_by_role[opt["role"]].append(opt["employee_id"])
            
        summary_items = []
        # Group suggestions for summary text
        role_suggestions = {}
        for opt in redeployment_options[:5]:  # limit to top 5 recommendations in summary text
            role_suggestions.setdefault(opt["role"], []).append(
                f"{opt['employee_id']} after Project {opt['current_project_id']} completes"
            )
            
        for role, suggestions in role_suggestions.items():
            summary_items.append(f"{role.replace('_', ' ').title()}: redeploy " + ", ".join(suggestions))
            
        summary = "Redeployment opportunities: " + "; ".join(summary_items) if summary_items else "No immediate internal redeployment candidates found near start date."
        
        return {
            "redeployment_options": redeployment_options,
            "candidates_by_role": candidates_by_role,
            "summary": summary
        }
