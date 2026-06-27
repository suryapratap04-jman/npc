import logging
from typing import Dict, Any

logger = logging.getLogger("scoring_engine")

class ScoringEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.weights = config.get("weights", {
            "skill_match": 0.40,
            "competency_match": 0.20,
            "project_experience": 0.15,
            "availability": 0.15,
            "project_similarity": 0.10
        })
        
        # Verify and normalize weights to sum to 1.0
        total = sum(self.weights.values())
        if total <= 0:
            logger.warning("Scoring weights sum to 0 or negative. Reverting to default weights.")
            self.weights = {
                "skill_match": 0.40,
                "competency_match": 0.20,
                "project_experience": 0.15,
                "availability": 0.15,
                "project_similarity": 0.10
            }
        elif abs(total - 1.0) > 1e-5:
            logger.info(f"Normalizing recommendation scoring weights to sum to 1.0 (current sum: {total})")
            self.weights = {k: v / total for k, v in self.weights.items()}

    def calculate_score(self, normalized_features: Dict[str, float]) -> Dict[str, Any]:
        """
        Computes the overall score and includes category breakdown.
        """
        breakdown = {}
        overall_score = 0.0

        for key, weight in self.weights.items():
            feat_val = normalized_features.get(key, 0.0)
            weighted_val = feat_val * weight
            breakdown[key] = round(feat_val, 2)
            overall_score += weighted_val

        return {
            "final_score": round(overall_score, 2),
            "category_scores": breakdown
        }
