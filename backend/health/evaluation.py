import csv
import time
import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger("health_evaluation")

class HealthEvaluator:
    def __init__(self):
        pass

    def evaluate_and_log(self, details: List[Dict[str, Any]], elapsed_time_ms: float):
        """
        Calculates project health aggregation statistics and appends to experiments/project_health_metrics.csv.
        """
        total_projects = len(details)
        if total_projects == 0:
            return

        risk_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
        total_risk_score = 0.0
        total_utilization = 0.0
        total_billability = 0.0
        potential_release_count = 0

        for d in details:
            risk_lvl = d.get("risk_level", "Low")
            risk_counts[risk_lvl] = risk_counts.get(risk_lvl, 0) + 1
            total_risk_score += d.get("risk_score", 0.0)
            total_utilization += d.get("utilization", {}).get("average", 0.0)
            total_billability += d.get("billability", {}).get("percentage", 100.0)
            potential_release_count += d.get("utilization", {}).get("underutilized_count", 0)

        avg_risk_score = total_risk_score / total_projects
        avg_utilization = total_utilization / total_projects
        avg_billability = total_billability / total_projects

        project_root = Path(__file__).parent.parent.parent
        experiments_dir = project_root / "experiments"
        experiments_dir.mkdir(parents=True, exist_ok=True)
        csv_path = experiments_dir / "project_health_metrics.csv"

        headers = [
            "timestamp", "total_projects", "risk_low_count", "risk_med_count",
            "risk_high_count", "risk_crit_count", "avg_utilization",
            "avg_billability", "potential_release_count", "avg_risk_score",
            "response_time_ms"
        ]

        file_exists = csv_path.exists()
        try:
            with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    "timestamp": time.time(),
                    "total_projects": total_projects,
                    "risk_low_count": risk_counts["Low"],
                    "risk_med_count": risk_counts["Medium"],
                    "risk_high_count": risk_counts["High"],
                    "risk_crit_count": risk_counts["Critical"],
                    "avg_utilization": round(avg_utilization, 2),
                    "avg_billability": round(avg_billability, 2),
                    "potential_release_count": potential_release_count,
                    "avg_risk_score": round(avg_risk_score, 2),
                    "response_time_ms": round(elapsed_time_ms, 2)
                })
            logger.info(f"Health evaluation metrics logged to {csv_path}")
        except Exception as e:
            logger.error(f"Failed to log health evaluation to CSV: {e}")
