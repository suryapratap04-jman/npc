import logging
from typing import Dict, Any, List, Optional
from backend.forecast.role_mix_engine import RoleMixEngine

logger = logging.getLogger("demand_forecast_engine")

# Hourly/monthly internal cost rates in USD per role for cost estimation
ROLE_MONTHLY_RATES = {
    "architect": 15000.0,
    "consultant": 10000.0,
    "backend": 8000.0,
    "frontend": 8000.0,
    "data_engineer": 9500.0,
    "data_scientist": 11000.0,
    "qa": 6500.0,
    "devops": 9000.0
}

class DemandForecastEngine:
    def __init__(self, role_mix_engine: RoleMixEngine):
        self.role_mix_engine = role_mix_engine

    def forecast_project_demand(self, 
                                project_type: str, 
                                expected_duration_months: Optional[int], 
                                required_skills: List[str], 
                                expected_team_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Estimates staffing requirements, project duration, resource mix,
        and cost estimates for a proposed project.
        """
        # Derive role mix
        mix_data = self.role_mix_engine.derive_role_mix(
            project_type=project_type,
            required_skills=required_skills,
            expected_team_size=expected_team_size
        )
        
        team_rec = mix_data["team_recommendation"]
        confidence = mix_data["confidence"]
        
        # Determine duration
        duration = expected_duration_months
        if not duration or duration <= 0:
            duration = max(1, round(mix_data["avg_duration"]))
            
        # Calculate FTE and Cost
        # Assuming 1.0 FTE per recommended resource slot
        total_fte = sum(team_rec.values())
        
        monthly_cost = 0.0
        for role, count in team_rec.items():
            rate = ROLE_MONTHLY_RATES.get(role, 8000.0)
            monthly_cost += count * rate
            
        total_cost = monthly_cost * duration
        
        return {
            "project_type": project_type,
            "team_recommendation": team_rec,
            "estimated_fte": float(total_fte),
            "estimated_cost": round(total_cost, 2),
            "expected_duration": duration,
            "confidence": confidence,
            "source": mix_data["source"]
        }
