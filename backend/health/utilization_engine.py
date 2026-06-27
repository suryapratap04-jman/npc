import logging
from typing import Dict, Any

logger = logging.getLogger("health_utilization_engine")

class UtilizationEngine:
    def __init__(self):
        pass

    def analyze_utilization(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes project capacity utilization metrics.
        """
        average = float(features.get("average_allocation", 0.0))
        peak = float(features.get("maximum_allocation", 0.0))
        overallocated = int(features.get("overallocated_count", 0))
        underutilized = int(features.get("underutilized_count", 0))

        # Idle Capacity (percent of unutilized allocation)
        idle_capacity = max(0.0, 100.0 - average)

        # Capacity that can be released (ratio of underutilized resources)
        team_size = int(features.get("team_size", 0))
        releasable = 0.0
        if team_size > 0:
            releasable = (underutilized / team_size) * 100.0

        return {
            "average": round(average, 2),
            "peak": round(peak, 2),
            "overallocated_count": overallocated,
            "underutilized_count": underutilized,
            "idle_capacity_percentage": round(idle_capacity, 2),
            "releasable_capacity_percentage": round(releasable, 2)
        }
