import logging
from typing import List, Dict, Any

logger = logging.getLogger("feature_builder")

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

class FeatureBuilder:
    def __init__(self, config: Dict[str, Any], skills_rarity: Dict[str, float], default_idf: float = 1.0):
        self.config = config
        self.skills_rarity = skills_rarity
        self.default_idf = default_idf
        self.norm_cfg = config.get("normalization", {})
        self.max_exp_years = self.norm_cfg.get("max_experience_years", 15.0)
        self.max_projects = self.norm_cfg.get("max_projects_completed", 10.0)

    def build_features(self, cand: Dict[str, Any], required_skills: List[str], required_competencies: List[str]) -> Dict[str, float]:
        """
        Extracts raw features for a candidate and normalizes them to a 0-100 scale.
        Returns a dictionary of normalized feature values.
        """
        emp = cand["employee"]
        skills = cand["skills"]
        comp = cand["competency"]
        allocs = cand["allocations"]
        utilization = cand["utilization"]
        qdrant_score = cand.get("qdrant_score", 0.0)

        # --- 1. SKILL FEATURES ---
        emp_skills_lower = set()
        for s in skills:
            if s.skill:
                emp_skills_lower.add(s.skill.lower().strip())
            if s.subskill:
                emp_skills_lower.add(s.subskill.lower().strip())
        
        # Skill Match Score based on IDF weights
        sum_matching_idf = 0.0
        sum_required_idf = 0.0
        for req in required_skills:
            req_l = req.lower().strip()
            idf = self.skills_rarity.get(req_l, self.default_idf)
            sum_required_idf += idf
            if req_l in emp_skills_lower:
                sum_matching_idf += idf
                
        s_skill = (sum_matching_idf / sum_required_idf) * 100.0 if sum_required_idf > 0.0 else 100.0

        # --- 2. COMPETENCY FEATURES ---
        comp_scores = []
        if required_competencies:
            for rc in required_competencies:
                rc_l = rc.lower().strip()
                col_name = COMPETENCY_FIELD_MAP.get(rc_l)
                val = 3.0 # neutral default if not found
                if comp and col_name:
                    db_val = getattr(comp, col_name, None)
                    if db_val is not None:
                        val = float(db_val)
                # Normalize 1-5 scale to 0-100
                comp_scores.append((val / 5.0) * 100.0)
        
        # If no specific competencies requested, fallback to average of all registered scores
        if not comp_scores and comp:
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
                
        s_competency = sum(comp_scores) / len(comp_scores) if comp_scores else 70.0 # neutral 70% if empty

        # --- 3. EXPERIENCE FEATURES ---
        # Years of experience: max experience_numeric from skills
        exp_years = 0.0
        for s in skills:
            if s.experience_numeric is not None:
                exp_years = max(exp_years, float(s.experience_numeric))
        
        normalized_years = min(exp_years / self.max_exp_years, 1.0) * 100.0
        
        # Similar projects count: count matching allocation projects
        projects_count = len({a.project_id for a in allocs if a.project_id})
        # If they had matching similar project allocations from candidate_retriever
        if cand.get("has_similar_proj_experience"):
            projects_count += 2 # boost count slightly to reflect historical matches
            
        normalized_projects = min(projects_count / self.max_projects, 1.0) * 100.0
        
        s_experience = (normalized_years * 0.5) + (normalized_projects * 0.5)

        # --- 4. AVAILABILITY FEATURES ---
        # Utilization score: 100 - utilization (lower utilization = higher availability score)
        utilization_score = max(0.0, 100.0 - utilization)
        
        # Allocation active status (0-100 index)
        # If currently allocated but project finishes soon, they are partially available
        s_availability = utilization_score

        # --- 5. PROJECT SIMILARITY FEATURES ---
        # Map Qdrant cosine similarity (0.0 to 1.0) to 0-100
        s_similarity = float(qdrant_score) * 100.0

        return {
            "skill_match": s_skill,
            "competency_match": s_competency,
            "project_experience": s_experience,
            "availability": s_availability,
            "project_similarity": s_similarity
        }
