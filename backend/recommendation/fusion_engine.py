import logging
from typing import Dict, Any

logger = logging.getLogger("fusion_engine")

class FusionEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fusion_weights = config.get("fusion_weights", {
            "rule_based_v1": 0.40,
            "semantic_only": 0.20,
            "historical_only": 0.15,
            "availability_only": 0.15,
            "competency_only": 0.10
        })

        # Normalize weights to sum to exactly 1.0
        total = sum(self.fusion_weights.values())
        if total <= 0:
            logger.warning("Strategy fusion weights sum to 0 or negative. Using defaults.")
            self.fusion_weights = {
                "rule_based_v1": 0.40,
                "semantic_only": 0.20,
                "historical_only": 0.15,
                "availability_only": 0.15,
                "competency_only": 0.10
            }
        elif abs(total - 1.0) > 1e-5:
            logger.info(f"Normalizing strategy fusion weights to sum to 1.0 (current sum: {total})")
            self.fusion_weights = {k: v / total for k, v in self.fusion_weights.items()}

    def calculate_hybrid_score(self, strategy_scores: Dict[str, float]) -> float:
        """
        Calculates the ensembled hybrid score (0-100) using the configuration weights.
        """
        hybrid_score = 0.0
        for strategy, weight in self.fusion_weights.items():
            score = strategy_scores.get(strategy, 0.0)
            hybrid_score += score * weight
        return round(max(0.0, min(100.0, hybrid_score)), 2)
