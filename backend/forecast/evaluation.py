import csv
import time
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("forecast_evaluation")

class ForecastEvaluator:
    def __init__(self):
        pass

    def evaluate_and_log(self, details: Dict[str, Any]):
        """
        Appends forecasting metrics to experiments/forecast_metrics.csv.
        """
        project_root = Path(__file__).parent.parent.parent
        experiments_dir = project_root / "experiments"
        experiments_dir.mkdir(parents=True, exist_ok=True)
        csv_path = experiments_dir / "forecast_metrics.csv"

        headers = [
            "timestamp", "forecast_accuracy", "avg_projected_utilization", 
            "capacity_surplus", "capacity_deficit", "hiring_recommendations", 
            "redeployment_recommendations", "api_latency"
        ]

        file_exists = csv_path.exists()
        try:
            with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    "timestamp": time.time(),
                    "forecast_accuracy": round(details.get("forecast_accuracy", 1.0), 2),
                    "avg_projected_utilization": round(details.get("avg_projected_utilization", 80.0), 2),
                    "capacity_surplus": int(details.get("capacity_surplus", 0)),
                    "capacity_deficit": int(details.get("capacity_deficit", 0)),
                    "hiring_recommendations": int(details.get("hiring_recommendations_count", 0)),
                    "redeployment_recommendations": int(details.get("redeployment_recommendations_count", 0)),
                    "api_latency": round(details.get("api_latency_ms", 0.0), 2)
                })
            logger.info(f"Forecast evaluation metrics logged to {csv_path}")
        except Exception as e:
            logger.error(f"Failed to log forecast evaluation to CSV: {e}")
