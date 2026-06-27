import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.database.models import Skill

logger = logging.getLogger("health_rampdown_engine")

class RampdownEngine:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_rampdown(self, project_id: str, features: Dict[str, Any], team_employee_ids: List[str]) -> Dict[str, Any]:
        """
        Determines if a project is suitable for ramp-down, and extracts release details.
        """
        days_rem = features.get("days_remaining", 999)
        avg_util = features.get("average_allocation", 100.0)
        weekly_trend = features.get("weekly_trend", "Stable")
        
        scope = str(features.get("scope_status", "Green")).upper().strip()
        schedule = str(features.get("schedule_status", "Green")).upper().strip()
        
        # Ramp-down criteria
        is_suitable = False
        if ("RED" not in scope) and ("RED" not in schedule):
            if (0 <= days_rem <= 30) or (avg_util < 60.0) or (weekly_trend == "Declining"):
                is_suitable = True

        estimated_release_count = 0
        earliest_release_date = None
        skills_released = []

        if is_suitable and team_employee_ids:
            under_cnt = int(features.get("underutilized_count", 0))
            if days_rem <= 14:
                estimated_release_count = len(team_employee_ids)
            elif under_cnt > 0:
                estimated_release_count = under_cnt
            else:
                estimated_release_count = min(1, len(team_employee_ids))

            import datetime
            today = datetime.date.today()
            if 0 <= days_rem <= 14:
                release_dt = today + datetime.timedelta(days=days_rem)
            else:
                release_dt = today
            earliest_release_date = release_dt.strftime("%Y-%m-%d")

            # Extract unique skills of the team members
            skills_query = self.db.query(Skill.skill).filter(
                Skill.employee_id.in_(team_employee_ids)
            ).distinct().all()
            skills_released = [s[0] for s in skills_query if s[0]][:5]

        return {
            "project_id": project_id,
            "is_suitable": is_suitable,
            "estimated_release_count": estimated_release_count,
            "earliest_release_date": earliest_release_date,
            "skills_released": skills_released
        }
