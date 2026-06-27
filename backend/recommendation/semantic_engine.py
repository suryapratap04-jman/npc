import logging
from typing import Dict, Any, List

logger = logging.getLogger("semantic_engine")

class SemanticEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def calculate_score(self, cand: Dict[str, Any]) -> float:
        """
        Computes the semantic match score (0-100) based on Qdrant similarity scores.
        """
        qdrant_score = cand.get("qdrant_score", 0.0)
        # Cosine similarity typically falls in [0, 1] for these embedding queries
        score = float(qdrant_score) * 100.0
        return round(max(0.0, min(100.0, score)), 2)
