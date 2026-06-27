import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("hiring_engine")

class HiringEngine:
    def __init__(self):
        pass

    def evaluate_hiring_needs(self, 
                              team_recommendation: Dict[str, int], 
                              capacity_projections: Dict[str, Any], 
                              redeployment_recommendations: Dict[str, List[str]],
                              project_start_offset_days: int = 0) -> Dict[str, Any]:
        """
        Determines external hiring needs by comparing required headcount to available capacity,
        net of planned redeployments.
        """
        # Determine capacity horizon index based on start date
        if project_start_offset_days >= 90:
            horizon_key = "available_90_days"
        elif project_start_offset_days >= 60:
            horizon_key = "available_60_days"
        elif project_start_offset_days >= 30:
            horizon_key = "available_30_days"
        else:
            horizon_key = "available_now"
            
        role_breakdown = capacity_projections.get("role_breakdown", {})
        hiring_needs = []
        
        for role, needed_count in team_recommendation.items():
            if needed_count <= 0:
                continue
                
            # Get available capacity (FTE) at target horizon
            avail_fte = role_breakdown.get(role, {}).get(horizon_key, 0.0)
            
            # Count how many employees can be redeployed
            redeploy_list = redeployment_recommendations.get(role, [])
            redeploy_count = len(redeploy_list)
            
            # Net capacity deficit
            deficit = needed_count - avail_fte
            hiring_count = max(0, round(deficit - redeploy_count))
            
            if hiring_count > 0:
                priority = "High" if hiring_count >= 2 else "Medium"
                # If project starts immediately and deficit is high, make it critical
                if horizon_key == "available_now" and hiring_count >= 2:
                    priority = "Critical"
                    
                reason = f"Required: {needed_count}, Available Capacity: {avail_fte} FTE. "
                if redeploy_count > 0:
                    reason += f"We can redeploy {redeploy_count} employee(s), leaving a net deficit of {hiring_count} external hire(s)."
                else:
                    reason += f"No redeployment candidates identified, requiring {hiring_count} external hire(s)."
                    
                hiring_needs.append({
                    "role": role.replace("_", " ").title(),
                    "count_needed": hiring_count,
                    "priority": priority,
                    "reason": reason
                })
                
        # Generate clean text summary
        if hiring_needs:
            summary = "External hiring is recommended for: " + ", ".join(
                [f"{hn['count_needed']} {hn['role']} ({hn['priority']} Priority)" for hn in hiring_needs]
            )
        else:
            summary = "No external hiring is required. Existing capacity and scheduled ramp-downs are sufficient."
            
        return {
            "hiring_needs": hiring_needs,
            "summary": summary
        }
