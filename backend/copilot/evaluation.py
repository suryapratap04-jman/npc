import csv
import time
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("copilot_evaluation")

class CopilotEvaluator:
    def __init__(self):
        pass

    def evaluate_and_log(self, details: Dict[str, Any]):
        """
        Logs conversational metrics to experiments/copilot_metrics.csv.
        """
        project_root = Path(__file__).parent.parent.parent
        experiments_dir = project_root / "experiments"
        experiments_dir.mkdir(parents=True, exist_ok=True)
        csv_path = experiments_dir / "copilot_metrics.csv"

        headers = [
            "timestamp", "session_id", "intent_accuracy", "tool_execution_latency",
            "multi_tool_success_rate", "conversation_length", "api_latency"
        ]

        file_exists = csv_path.exists()
        try:
            with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    "timestamp": time.time(),
                    "session_id": details.get("session_id", "default"),
                    "intent_accuracy": round(details.get("intent_accuracy", 1.0), 2),
                    "tool_execution_latency": round(details.get("tool_execution_latency", 0.0), 2),
                    "multi_tool_success_rate": round(details.get("multi_tool_success_rate", 1.0), 2),
                    "conversation_length": int(details.get("conversation_length", 1)),
                    "api_latency": round(details.get("api_latency_ms", 0.0), 2)
                })
            logger.info(f"Copilot evaluation metrics logged to {csv_path}")
        except Exception as e:
            logger.error(f"Failed to log copilot evaluation to CSV: {e}")
