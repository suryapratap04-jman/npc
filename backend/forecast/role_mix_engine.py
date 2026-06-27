import logging
from typing import Dict, List, Any, Optional, Tuple

from backend.forecast.demand_feature_builder import DemandFeatureBuilder

logger = logging.getLogger("role_mix_engine")

FALLBACK_TEMPLATES = {
    "AI": {
        "architect": 1,
        "data_scientist": 1,
        "data_engineer": 2,
        "backend": 2,
        "qa": 1,
        "frontend": 1,
        "devops": 1
    },
    "Data Engineering": {
        "architect": 1,
        "data_engineer": 3,
        "backend": 1,
        "qa": 1,
        "devops": 1
    },
    "BI": {
        "consultant": 2,
        "frontend": 1,
        "qa": 1
    },
    "Software Development": {
        "architect": 1,
        "backend": 2,
        "frontend": 1,
        "qa": 1,
        "devops": 1
    },
    "Default": {
        "architect": 1,
        "consultant": 1,
        "backend": 1,
        "frontend": 1,
        "qa": 1
    }
}

class RoleMixEngine:
    def __init__(self, feature_builder: DemandFeatureBuilder):
        self.feature_builder = feature_builder

    def get_template_by_skills(self, skills: List[str], project_type: str) -> Tuple[str, Dict[str, int]]:
        """Determines the best fallback template based on project metadata."""
        skills_lower = [s.lower() for s in skills]
        
        # Check for AI / Gen AI skills
        if any(any(kw in s for kw in ["ai", "llm", "gpt", "nlp", "learning", "python"]) for s in skills_lower) or "ai" in project_type.lower():
            return "AI", FALLBACK_TEMPLATES["AI"]
            
        # Check for Data Engineering skills
        if any(any(kw in s for kw in ["spark", "databricks", "snowflake", "pipeline", "etl", "sql"]) for s in skills_lower) or "data" in project_type.lower():
            return "Data Engineering", FALLBACK_TEMPLATES["Data Engineering"]
            
        # Check for BI / Reporting
        if any(any(kw in s for kw in ["bi", "power bi", "dashboard", "report", "tableau"]) for s in skills_lower):
            return "BI", FALLBACK_TEMPLATES["BI"]
            
        return "Default", FALLBACK_TEMPLATES["Default"]

    def derive_role_mix(self, 
                        project_type: str, 
                        required_skills: List[str], 
                        expected_team_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Derives the recommended resource mix for a project category using historical data
        with fallback options. Returns the recommendation, confidence, and source.
        """
        # Map technology category
        tech_category = None
        skills_lower = [s.lower() for s in required_skills]
        if any(any(kw in s for kw in ["ai", "llm", "gpt"]) for s in skills_lower):
            tech_category = "Gen AI"
        elif any(any(kw in s for kw in ["spark", "databricks", "snowflake"]) for s in skills_lower):
            tech_category = "Data Engineering"
            
        # Query historical aggregates
        history = self.feature_builder.get_historical_aggregates(
            project_type=project_type,
            technology=tech_category
        )
        
        sample_size = history.get("sample_size", 0)
        team_rec = {}
        confidence = "Low"
        source = "Configurable Template"
        
        if sample_size >= 5:
            confidence = "High"
            source = "Historical Data"
            raw_mix = history["avg_role_mix"]
            # Convert roles to schema keys
            team_rec = self._normalize_role_mix(raw_mix)
        elif sample_size > 0:
            confidence = "Medium"
            source = "Historical Data (Small Sample)"
            raw_mix = history["avg_role_mix"]
            team_rec = self._normalize_role_mix(raw_mix)
        else:
            # Fallback to templates
            template_name, template = self.get_template_by_skills(required_skills, project_type)
            team_rec = template.copy()
            source = f"Fallback Template ({template_name})"
            
        # Adjust recommendation if expected team size is explicitly specified
        if expected_team_size and expected_team_size > 0:
            current_total = sum(team_rec.values())
            if current_total > 0:
                scaling_factor = expected_team_size / current_total
                adjusted_rec = {}
                for role, count in team_rec.items():
                    adjusted_count = round(count * scaling_factor)
                    if adjusted_count > 0:
                        adjusted_rec[role] = adjusted_count
                # Make sure the sum matches expected team size exactly by adjusting the largest category
                diff = expected_team_size - sum(adjusted_rec.values())
                if diff != 0 and adjusted_rec:
                    largest_role = max(adjusted_rec, key=adjusted_rec.get)
                    adjusted_rec[largest_role] = max(1, adjusted_rec[largest_role] + diff)
                team_rec = adjusted_rec

        # Fill in zero for all schema roles
        all_roles = ["architect", "consultant", "backend", "frontend", "data_engineer", "data_scientist", "qa", "devops"]
        final_team = {r: team_rec.get(r, 0) for r in all_roles}
        
        return {
            "team_recommendation": final_team,
            "confidence": confidence,
            "source": source,
            "sample_size": sample_size,
            "avg_duration": history.get("avg_duration_months", 6.0)
        }

    def _normalize_role_mix(self, raw_mix: Dict[str, float]) -> Dict[str, int]:
        """Converts database role strings to lowercase schema keys and rounds values."""
        key_map = {
            "Architect": "architect",
            "Consultant": "consultant",
            "Backend Engineer": "backend",
            "Frontend Engineer": "frontend",
            "Data Engineer": "data_engineer",
            "Data Scientist": "data_scientist",
            "QA": "qa",
            "DevOps": "devops"
        }
        normalized = {}
        for role, count in raw_mix.items():
            key = key_map.get(role)
            if key:
                # We round to nearest integer, keeping minimum of 1 if it is > 0.1
                rounded = max(1, round(count)) if count > 0.1 else 0
                if rounded > 0:
                    normalized[key] = rounded
        return normalized
