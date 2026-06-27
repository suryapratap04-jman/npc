import logging
from typing import Dict, Any, List
from backend.recommendation.utils import load_recommendation_config
from backend.llm import get_llm_provider

logger = logging.getLogger("health_explanation_engine")

class ExplanationEngine:
    def __init__(self):
        self.config = load_recommendation_config()
        self._provider = None

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_llm_provider()
        return self._provider

    def generate_explanation(
        self,
        project_id: str,
        risk_analysis: Dict[str, Any],
        utilization_analysis: Dict[str, Any],
        billability_analysis: Dict[str, Any],
        rampdown_analysis: Dict[str, Any],
        actions: List[str]
    ) -> str:
        """
        Uses LLM or deterministic fallback to explain project risks and capacity decisions.
        """
        enable_explanations = self.config.get("llm", {}).get("enable_explanations", True)
        
        # Build deterministic fallback explanation text
        overall_health = risk_analysis.get("overall_health", "Green")
        risk_level = risk_analysis.get("risk_level", "Low")
        risk_score = risk_analysis.get("risk_score", 0.0)
        
        fallback_text = f"### Health Analysis for Project {project_id}\n"
        fallback_text += f"- **Overall Health Indicator**: {overall_health} ({risk_level} Risk Level, Score: {risk_score}/100)\n"
        fallback_text += f"- **Allocation Workload**: Average utilization is {utilization_analysis.get('average', 0.0)}% with {utilization_analysis.get('overallocated_count', 0)} overallocated resources.\n"
        fallback_text += f"- **Cost Recovery**: Billability is at {billability_analysis.get('percentage', 100.0)}% with {billability_analysis.get('shadow_resources_count', 0)} shadow resources.\n"
        
        if rampdown_analysis.get("is_suitable", False):
            fallback_text += f"- **Ramp-Down status**: Eligible for release of {rampdown_analysis.get('estimated_release_count', 0)} resources on {rampdown_analysis.get('earliest_release_date')}.\n"
        else:
            fallback_text += "- **Ramp-Down status**: Not eligible for ramp-down due to stable/active project workload.\n"

        if not enable_explanations:
            logger.info("LLM explanations disabled. Returning deterministic fallback.")
            return fallback_text

        # LLM Generation
        try:
            prompt = f"""
You are an expert Resource Operations Director and Project Delivery Architect.
Provide a clear, context-aware executive summary explaining the health status, utilization, and capacity risks of the project based on the data below.

### Project Data:
- Project: {project_id}
- Health: {overall_health}
- Risk Level: {risk_level} (Score: {risk_score}/100)
- Average Utilization: {utilization_analysis.get('average', 0.0)}%
- Peak Utilization: {utilization_analysis.get('peak', 0.0)}%
- Overallocated Team Members: {utilization_analysis.get('overallocated_count', 0)}
- Underutilized Team Members: {utilization_analysis.get('underutilized_count', 0)}
- Billability percentage: {billability_analysis.get('percentage', 100.0)}%
- Shadow Resources count: {billability_analysis.get('shadow_resources_count', 0)}
- Rampdown Suitable: {rampdown_analysis.get('is_suitable', False)}
- Action Recommendations: {", ".join(actions)}

Format your response in a professional executive tone using bullet points. Focus on risk mitigation and resource optimization.
"""
            system_prompt = "You are an AI operations assistant designed to explain project delivery and resource allocation metrics."
            return self.provider.generate(prompt=prompt, system_prompt=system_prompt)
        except Exception as e:
            logger.error(f"Failed to generate LLM project health explanation: {e}")
            return fallback_text
