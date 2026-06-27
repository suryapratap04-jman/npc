import logging
import datetime
from typing import Dict, Any

logger = logging.getLogger("availability_engine")

class AvailabilityEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def calculate_score(self, cand: Dict[str, Any], project_start_date_str: str) -> float:
        """
        Computes the availability score (0-100) based on utilization and project transition delays.
        """
        utilization = float(cand.get("utilization", 0.0))
        
        # 1. Utilization component (higher score for lower utilization)
        utilization_score = max(0.0, 100.0 - utilization)

        # 2. Parse target project start date
        today = datetime.date.today()
        try:
            proj_start = datetime.datetime.strptime(project_start_date_str, "%Y-%m-%d").date()
        except Exception:
            proj_start = today + datetime.timedelta(days=30) # default to 30 days out

        # 3. Transition delay component
        max_end = None
        for a in cand.get("allocations", []):
            if a.is_allocation_active == 1 and a.allocated_end_date:
                if max_end is None or a.allocated_end_date > max_end:
                    max_end = a.allocated_end_date

        if max_end is None or max_end <= proj_start:
            delay_days = 0
        else:
            delay_days = (max_end - proj_start).days

        # Deduct 2 points per day of delay
        delay_score = max(0.0, 100.0 - (delay_days * 2.0))

        # Overall Availability Score: average of utilization score and delay score
        score = 0.5 * utilization_score + 0.5 * delay_score
        return round(max(0.0, min(100.0, score)), 2)
