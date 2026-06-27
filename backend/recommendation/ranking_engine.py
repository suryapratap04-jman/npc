import logging
import datetime
from typing import List, Dict, Any

logger = logging.getLogger("ranking_engine")

class RankingEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_top_n = config.get("defaults", {}).get("top_n", 10)

    def rank_candidates(self, scored_candidates: List[Dict[str, Any]], required_skills: List[str], top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Sorts the scored candidates list and returns the top_n items formatted.
        """
        if not top_n:
            top_n = self.default_top_n

        # Sort by final score descending
        sorted_cands = sorted(scored_candidates, key=lambda x: x["final_score"], reverse=True)
        top_cands = sorted_cands[:top_n]

        ranked_results = []
        for idx, item in enumerate(top_cands):
            cand = item["candidate"]
            emp = cand["employee"]
            emp_id = emp.employee_id
            
            # Formulate Availability Date string
            availability_date = "Immediate"
            if cand["utilization"] > 0:
                max_end = None
                for a in cand["allocations"]:
                    if a.is_allocation_active == 1 and a.allocated_end_date:
                        if max_end is None or a.allocated_end_date > max_end:
                            max_end = a.allocated_end_date
                if max_end:
                    availability_date = max_end.strftime("%Y-%m-%d")

            # Extract matching skills
            emp_skills_lower = {s.skill.lower().strip() for s in cand["skills"] if s.skill}
            matching_skills = [req for req in required_skills if req.lower().strip() in emp_skills_lower]

            ranked_results.append({
                "employee_id": emp_id,
                "job_name": emp.job_name or "N/A",
                "department_name": emp.department_name or "N/A",
                "final_score": float(item["final_score"]),
                "rank": idx + 1,
                "category_scores": item["category_scores"],
                "availability_date": availability_date,
                "utilization_percentage": float(cand["utilization"]),
                "matching_skills": matching_skills
            })

        logger.info(f"Ranking engine sorted and returned top {len(ranked_results)} recommendations.")
        return ranked_results
