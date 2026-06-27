import logging
from typing import Dict, Any, List, Optional
from backend.llm import get_llm_provider

logger = logging.getLogger("explanation_engine")

class ExplanationEngine:
    def __init__(self):
        try:
            self.llm = get_llm_provider()
        except Exception:
            self.llm = None

    def generate_explanation(self, 
                             project_type: str, 
                             expected_start_date: str,
                             duration: int, 
                             team_rec: Dict[str, int], 
                             hiring_summary: str, 
                             redeploy_summary: str,
                             sample_size: int,
                             avg_team_size: float,
                             avg_duration: float) -> str:
        """
        Generates a context-supported explanation for forecasting recommendations.
        Tries to use local Ollama to polish the narrative, otherwise falls back to a clean rule-based layout.
        """
        # Formulate detailed fact sheet
        facts = []
        facts.append(f"Project Type: {project_type}")
        facts.append(f"Expected Start Date: {expected_start_date}")
        facts.append(f"Estimated Project Duration: {duration} months")
        
        team_str = ", ".join([f"{count} {role.replace('_', ' ').title()}" for role, count in team_rec.items() if count > 0])
        facts.append(f"Recommended Team: {team_str}")
        
        facts.append(f"Hiring Decisions: {hiring_summary}")
        facts.append(f"Redeployment Strategy: {redeploy_summary}")
        
        if sample_size > 0:
            facts.append(f"Historical Evidence: Based on {sample_size} past '{project_type}' projects which averaged a team size of {avg_team_size} and duration of {avg_duration} months.")
        else:
            facts.append("Historical Evidence: No exact matching projects found. Reverting to configurable baseline templates.")
            
        facts_block = "\n".join([f"- {fact}" for fact in facts])
        
        prompt = f"""
You are a Senior Resource Manager. Summarize the following staffing recommendation facts into a professional, human-like narrative explanation for the leadership team. Keep it under 150 words.

### Staffing Recommendation Facts:
{facts_block}

### Executive Narrative Summary:
"""
        # Try local LLM
        if self.llm:
            try:
                system_prompt = "You are a professional resource management AI assistant."
                response = self.llm.generate(prompt=prompt, system_prompt=system_prompt)
                # If there's an error message or blank, fallback
                if response and "Error communicating" not in response and len(response.strip()) > 30:
                    return response.strip()
            except Exception as e:
                logger.warning(f"Failed to query LLM for forecast explanation: {e}")
                
        # Structured rule-based fallback
        fallback = f"### Resource Allocation Analysis\n\n"
        fallback += f"To execute the upcoming **{project_type}** project starting on **{expected_start_date}**, the organization requires a team of **{team_str}** for an expected duration of **{duration} months**.\n\n"
        
        fallback += f"**Hiring & Redeployment Plan:**\n"
        fallback += f"* {hiring_summary}\n"
        fallback += f"* {redeploy_summary}\n\n"
        
        if sample_size > 0:
            fallback += f"**Historical Justification:** This allocation is backed by **{sample_size}** matching historical projects of type **{project_type}**, which averaged **{avg_team_size} resources** and **{avg_duration} months** in duration. This supports our recommended resource mix and indicates a { 'High' if sample_size >= 5 else 'Medium' } forecasting confidence."
        else:
            fallback += "**Historical Justification:** No exact historical matches are available in the database. Staffing is based on pre-configured team templates designed for this technology."
            
        return fallback
