import logging
from typing import Dict, Any

logger = logging.getLogger("health_risk_engine")

class RiskEngine:
    def __init__(self):
        pass

    def calculate_risk(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the numeric risk score (0-100) and risk level for a project.
        """
        score = 0.0

        # 1. Weekly Status checks
        status_cols = ["scope_status", "schedule_status", "quality_status", "csat_status"]
        for col in status_cols:
            val = str(features.get(col, "Green")).upper().strip()
            if "RED" in val:
                score += 20.0
            elif "AMBER" in val or "YELLOW" in val:
                score += 10.0

        # 2. Overdue project check
        days_rem = features.get("days_remaining", 0)
        proj_status = str(features.get("project_status", "ACTIVE")).upper().strip()
        if days_rem < 0 and proj_status not in ["CLOSED", "COMPLETE", "DEAL LOST"]:
            score += 15.0

        # 3. Schedule delay check
        delay_days = features.get("delay_days", 0)
        if delay_days > 14:
            score += 10.0
        elif delay_days > 0:
            score += 5.0

        # 4. Overallocated resources check
        over_cnt = features.get("overallocated_count", 0)
        if over_cnt > 0:
            score += 10.0

        # 5. Team imbalance check
        under_cnt = features.get("underutilized_count", 0)
        if under_cnt > 0:
            score += 5.0

        # 6. Timesheet missing logs check
        missing = features.get("missing_submissions", 0)
        team_size = features.get("team_size", 0)
        if team_size > 0 and missing > (team_size / 2):
            score += 5.0

        # Bound score between 0 and 100
        risk_score = round(max(0.0, min(100.0, score)), 2)

        # Classify risk level
        if risk_score >= 75.0:
            risk_level = "Critical"
            overall_health = "Red"
        elif risk_score >= 50.0:
            risk_level = "High"
            overall_health = "Red"
        elif risk_score >= 25.0:
            risk_level = "Medium"
            overall_health = "Amber"
        else:
            risk_level = "Low"
            overall_health = "Green"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "overall_health": overall_health
        }
