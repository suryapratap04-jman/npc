import os
import json
import time
import logging
from typing import List, Dict, Any, Set
from sqlalchemy.orm import Session
from backend.database.models import Allocation

logger = logging.getLogger("recommendation_evaluation")

class RecommendationEvaluator:
    def __init__(self, db: Session, metrics_log_path: str = None):
        self.db = db
        if metrics_log_path is None:
            # Save runs logs inside the recommendation directory
            from pathlib import Path
            self.metrics_log_path = str(Path(__file__).parent / "eval_registry.jsonl")
        else:
            self.metrics_log_path = metrics_log_path

    def get_ground_truth(self, project_id: str) -> Set[str]:
        """
        Retrieves the set of employee IDs historically allocated to a project.
        """
        if not project_id:
            return set()
            
        allocations = self.db.query(Allocation).filter(
            Allocation.project_id == project_id
        ).all()
        
        return {a.employee_id for a in allocations if a.employee_id}

    def evaluate(self, project_id: str, recommendations: List[Dict[str, Any]], elapsed_time_ms: float) -> Dict[str, Any]:
        """
        Calculates Precision@5, Precision@10, Recall@10, and Mean Reciprocal Rank (MRR).
        Saves results to eval_registry.jsonl.
        """
        ground_truth = self.get_ground_truth(project_id)
        total_relevant = len(ground_truth)
        
        logger.info(f"Evaluation for project {project_id}: {total_relevant} historical relevant allocations found.")

        rec_ids = [r["employee_id"] for r in recommendations]
        
        # Calculate Precision@5
        top_5_ids = rec_ids[:5]
        hits_5 = sum(1 for rid in top_5_ids if rid in ground_truth)
        precision_5 = hits_5 / 5.0 if len(top_5_ids) >= 5 else (hits_5 / len(top_5_ids) if top_5_ids else 0.0)

        # Calculate Precision@10
        top_10_ids = rec_ids[:10]
        hits_10 = sum(1 for rid in top_10_ids if rid in ground_truth)
        precision_10 = hits_10 / 10.0 if len(top_10_ids) >= 10 else (hits_10 / len(top_10_ids) if top_10_ids else 0.0)

        # Calculate Recall@10
        recall_10 = 0.0
        if total_relevant > 0:
            recall_10 = hits_10 / float(total_relevant)

        # Calculate Mean Reciprocal Rank (MRR)
        mrr = 0.0
        for rank_idx, rid in enumerate(rec_ids):
            if rid in ground_truth:
                mrr = 1.0 / (rank_idx + 1)
                break

        # Calculate average recommendation score
        avg_score = 0.0
        if recommendations:
            avg_score = sum(r["final_score"] for r in recommendations) / len(recommendations)

        metrics = {
            "timestamp": time.time(),
            "project_id": project_id,
            "relevant_count": total_relevant,
            "precision_at_5": round(precision_5, 4),
            "precision_at_10": round(precision_10, 4),
            "recall_at_10": round(recall_10, 4),
            "mrr": round(mrr, 4),
            "average_recommendation_score": round(avg_score, 2),
            "response_time_ms": round(elapsed_time_ms, 2)
        }

        self._save_metrics_log(metrics)
        return metrics

    def _save_metrics_log(self, metrics: Dict[str, Any]):
        """Persists the metrics dict into a JSONL log file by appending a line."""
        try:
            with open(self.metrics_log_path, "a") as f:
                f.write(json.dumps(metrics) + "\n")
            logger.info(f"Evaluation metrics logged successfully to {self.metrics_log_path}")
        except Exception as e:
            logger.error(f"Could not write evaluation run metrics to file: {e}")

    def log_experiment(self, strategy: str, weights: Dict[str, float], metrics: Dict[str, Any]):
        """Logs the experiment run to experiments/strategy_comparison.csv."""
        import csv
        from pathlib import Path
        
        project_root = Path(__file__).parent.parent.parent
        experiments_dir = project_root / "experiments"
        experiments_dir.mkdir(parents=True, exist_ok=True)
        csv_path = experiments_dir / "strategy_comparison.csv"

        headers = [
            "timestamp", "project_id", "strategy", "weights", "response_time_ms",
            "relevant_count", "precision_at_5", "precision_at_10", "recall_at_10",
            "mrr", "average_recommendation_score"
        ]

        file_exists = csv_path.exists()
        try:
            with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                if not file_exists:
                    writer.writeheader()
                
                weights_str = ";".join([f"{k}:{v}" for k, v in weights.items()])
                
                writer.writerow({
                    "timestamp": metrics.get("timestamp", time.time()),
                    "project_id": metrics.get("project_id", "N/A"),
                    "strategy": strategy,
                    "weights": weights_str,
                    "response_time_ms": metrics.get("response_time_ms", 0.0),
                    "relevant_count": metrics.get("relevant_count", 0),
                    "precision_at_5": metrics.get("precision_at_5", 0.0),
                    "precision_at_10": metrics.get("precision_at_10", 0.0),
                    "recall_at_10": metrics.get("recall_at_10", 0.0),
                    "mrr": metrics.get("mrr", 0.0),
                    "average_recommendation_score": metrics.get("average_recommendation_score", 0.0)
                })
            logger.info(f"Experiment log saved to {csv_path}")
        except Exception as e:
            logger.error(f"Failed to log experiment run to CSV: {e}")
