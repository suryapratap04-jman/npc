import os
import yaml
from pathlib import Path
from typing import Dict, Any

def get_config_path() -> Path:
    """Returns the absolute path to the recommendation config.yaml file."""
    return Path(__file__).parent / "config.yaml"

def load_recommendation_config() -> Dict[str, Any]:
    """Loads configuration parameters from config.yaml."""
    cfg_path = get_config_path()
    if not cfg_path.exists():
        # Fallback dictionary defaults if config does not exist
        return {
            "weights": {
                "skill_match": 0.40,
                "competency_match": 0.20,
                "project_experience": 0.15,
                "availability": 0.15,
                "project_similarity": 0.10
            },
            "thresholds": {
                "utilization_threshold": 0.90,
                "similarity_threshold": 0.40,
                "require_mandatory_skills": True
            },
            "normalization": {
                "max_experience_years": 15.0,
                "max_projects_completed": 10.0
            },
            "defaults": {
                "top_n": 10
            }
        }
        
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)
