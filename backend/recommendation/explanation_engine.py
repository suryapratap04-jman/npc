import logging
from typing import List, Dict, Any
from backend.llm import get_llm_provider

logger = logging.getLogger("explanation_engine")

class ExplanationEngine:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        # Instantiate LLM provider lazily
        self._provider = None

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_llm_provider()
        return self._provider

    def generate_explanation(self, project_info: Dict[str, Any], top_recommendations: List[Dict[str, Any]]) -> str:
        """
        Queries the LLM provider to construct a detailed natural language explanation.
        """
        if not top_recommendations:
            return "No candidates met the minimum criteria; cannot formulate explanations."

        if not self.config.get("llm", {}).get("enable_explanations", True):
            logger.info("LLM explanations disabled in config. Using deterministic fallback.")
            return self._build_deterministic_explanation(top_recommendations)

        # Check if explanations are disabled in YAML config
        llm_cfg = self.config.get("llm", {})
        if not llm_cfg.get("enable_explanations", True):
            logger.info("LLM explanations are disabled in configuration. Returning deterministic fallback.")
            return self._build_deterministic_explanation(top_recommendations)

        # Grab the top candidate details
        top_candidate = top_recommendations[0]
        
        # Build prompt context detailing the structured parameters
        candidate_summary_lines = []
        for cand in top_recommendations[:3]: # explain top 3 candidates
            category_scores_str = ", ".join([f"{k}: {v}/100" for k, v in cand["category_scores"].items()])
            candidate_summary_lines.append(
                f"- Employee ID: {cand['employee_id']}\n"
                f"  Designation/Job: {cand['job_name']} ({cand['department_name']})\n"
                f"  Final Score: {cand['final_score']}/100 (Rank {cand['rank']})\n"
                f"  Category Scores: {category_scores_str}\n"
                f"  Utilization: {cand['utilization_percentage']}%\n"
                f"  Availability: {cand['availability_date']}\n"
                f"  Matching Skills: {', '.join(cand['matching_skills'])}\n"
            )
        
        candidates_context = "\n".join(candidate_summary_lines)

        prompt = f"""
You are an expert AI Resource Allocator and Senior Project EM.
Review the following resource recommendations compiled by our scoring engine for a project request.

PROJECT REQUIREMENT:
- Required Skills: {', '.join(project_info.get('required_skills', []))}
- Project Type/CoE: {project_info.get('project_type', 'N/A')}
- Target Start Date: {project_info.get('project_start_date', 'N/A')}
- Requested Competencies: {', '.join(project_info.get('required_competencies', []))}

TOP RECOMMENDED CANDIDATES SUMMARY (Scored by Engine):
{candidates_context}

Write a detailed natural-language Recommendation Explanation.
You MUST follow this structure strictly:

### Recommendation Summary
[Write 2-3 sentences summarizing the overall search matching results and who the top match is.]

### Why Recommended:
For each of the top candidates (up to 2), write 3-4 bullet points detailing:
- Skill alignment (referencing the matching skills and final score).
- Utilization & Capacity (referencing their current utilization and available date).
- Competencies & experience match.

### Potential Risks:
- List 1-2 realistic structural risks (e.g., matching skills coverage limits or utilization tight margins).

### Recommendation Confidence:
[High / Medium / Low] (Brief 1-sentence justification).

CRITICAL RULE: Refer ONLY to the structured candidate details provided above. Do not invent any name, project count, skill, or numeric value that is not explicitly present in the context.
"""
        try:
            logger.info("Requesting natural-language explanation from local LLM...")
            explanation = self.provider.generate(prompt)
            return explanation.strip()
        except Exception as e:
            logger.error(f"Failed to generate LLM explanation: {e}")
            # Fallback text explanation if LLM service is offline or slow
            return self._build_deterministic_explanation(top_recommendations)

    def _build_deterministic_explanation(self, top_recommendations: List[Dict[str, Any]]) -> str:
        """Fallback rule-based text generator if Ollama is unreachable."""
        top = top_recommendations[0]
        return f"""### Recommendation Summary (Deterministic Fallback)
The scoring engine recommends candidate {top['employee_id']} as the top match with a score of {top['final_score']}/100.

### Why Recommended:
- Possesses matching capabilities: {', '.join(top['matching_skills'])}.
- Current utilization is {top['utilization_percentage']}%, with availability status marked as '{top['availability_date']}'.
- Category Breakdown: Skill Match {top['category_scores'].get('skill_match')}/100, Competency Match {top['category_scores'].get('competency_match')}/100.

### Potential Risks:
- Baseline evaluations depend on self-reported capability descriptions in database profiles.

### Recommendation Confidence:
High (Derived mathematically from weight metrics)."""
