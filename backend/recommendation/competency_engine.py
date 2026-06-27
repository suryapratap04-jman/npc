import logging
from typing import Dict, Any, List

logger = logging.getLogger("competency_engine")

COMPETENCY_FIELD_MAP = {
    "stakeholder management": "stakeholder_management_score",
    "consultative guidance": "consultative_guidance_score",
    "techno-functional expertise": "techno_functional_score",
    "communication skills": "communication_score",
    "communication": "communication_score",
    "ambiguity navigation": "ambiguity_navigation_score",
    "capabilities articulation": "capabilities_articulation_score",
    "solution architecture": "solution_architecture_score",
    "project planning": "project_planning_score"
}

class CompetencyEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def calculate_score(self, cand: Dict[str, Any], required_competencies: List[str]) -> float:
        """
        Computes the competency score (0-100) based on employee competency ratings.
        """
        comp = cand.get("competency")
        
        # Soft fallback if no competency record is available in DB
        if not comp:
            return 70.0

        comp_scores = []
        if required_competencies:
            for rc in required_competencies:
                rc_l = rc.lower().strip()
                col_name = COMPETENCY_FIELD_MAP.get(rc_l)
                val = 3.0  # default rating if not found
                if col_name:
                    db_val = getattr(comp, col_name, None)
                    if db_val is not None:
                        val = float(db_val)
                # Normalize 1-5 scale to 0-100
                comp_scores.append((val / 5.0) * 100.0)

        # Fallback to average of all registered ratings if no specific competencies are requested
        if not comp_scores:
            all_fields = [
                comp.stakeholder_management_score,
                comp.consultative_guidance_score,
                comp.techno_functional_score,
                comp.communication_score,
                comp.ambiguity_navigation_score,
                comp.capabilities_articulation_score,
                comp.solution_architecture_score,
                comp.project_planning_score
            ]
            valid_scores = [float(val) for val in all_fields if val is not None]
            if valid_scores:
                comp_scores = [(v / 5.0) * 100.0 for v in valid_scores]

        score = sum(comp_scores) / len(comp_scores) if comp_scores else 70.0
        return round(max(0.0, min(100.0, score)), 2)
