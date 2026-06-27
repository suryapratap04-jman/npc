import logging
from typing import List, Dict, Any

logger = logging.getLogger("diversity_engine")

class DiversityEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.div_cfg = config.get("diversity", {})
        self.enabled = self.div_cfg.get("enable_diversity", True)
        self.max_per_dept = self.div_cfg.get("max_per_department", 2)
        self.max_per_mgr = self.div_cfg.get("max_per_manager", 2)

    def apply_diversity_filter(self, scored_candidates: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Filters ranked candidates list to cap occurrences of the same department or manager.
        scored_candidates should be sorted by score descending.
        """
        if not self.enabled or not scored_candidates:
            return scored_candidates[:top_n]

        filtered_results = []
        dept_counts = {}
        mgr_counts = {}

        for item in scored_candidates:
            cand = item["candidate"]
            emp = cand["employee"]
            dept = (emp.department_name or "N/A").lower().strip()
            mgr = (emp.manager_id or "N/A").lower().strip()

            dept_count = dept_counts.get(dept, 0)
            mgr_count = mgr_counts.get(mgr, 0)

            if dept_count >= self.max_per_dept:
                logger.debug(f"Skipping candidate {emp.employee_id} due to department limit ({dept}).")
                continue

            if mgr_count >= self.max_per_mgr:
                logger.debug(f"Skipping candidate {emp.employee_id} due to manager limit ({mgr}).")
                continue

            # Increment counts
            dept_counts[dept] = dept_count + 1
            mgr_counts[mgr] = mgr_count + 1
            filtered_results.append(item)

            if len(filtered_results) >= top_n:
                break

        return filtered_results
