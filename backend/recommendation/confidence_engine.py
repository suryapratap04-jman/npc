import logging
from typing import List, Dict, Any

logger = logging.getLogger("confidence_engine")

class ConfidenceEngine:
    def __init__(self):
        pass

    def calculate_confidence(self, matching_skills: List[str], required_skills: List[str], qdrant_score: float, has_hist: bool, final_score: float) -> str:
        """
        Heuristically calculates recommendation confidence (High, Medium, Low).
        """
        # 1. Skill coverage ratio
        skills_ratio = len(matching_skills) / len(required_skills) if required_skills else 1.0

        # 2. Embedding similarity score (typically 0.0 to 1.0)
        similarity = float(qdrant_score)

        # 3. Historical evidence (1.0 if worked on similar projects, else 0.0)
        hist_val = 1.0 if has_hist else 0.0

        # 4. Final Score contribution
        score_val = final_score / 100.0

        # Weighted combination out of 100
        conf_value = (
            30.0 * skills_ratio +
            30.0 * similarity +
            20.0 * hist_val +
            20.0 * score_val
        )

        if conf_value >= 75.0:
            return "High"
        elif conf_value >= 50.0:
            return "Medium"
        else:
            return "Low"
