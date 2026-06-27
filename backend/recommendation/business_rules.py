import logging
import datetime
from typing import List, Dict, Any

logger = logging.getLogger("business_rules")

class BusinessRulesEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules_cfg = config.get("thresholds", {})
        self.util_limit = self.rules_cfg.get("utilization_threshold", 0.90) * 100.0 # convert to percentage
        self.require_mandatory = self.rules_cfg.get("require_mandatory_skills", True)

    def filter_candidates(self, candidates: List[Dict[str, Any]], required_skills: List[str], project_start_date_str: str) -> List[Dict[str, Any]]:
        """
        Applies rules configuration to discard disqualified resources.
        """
        filtered = []
        today = datetime.date.today()
        
        # Parse project start date
        try:
            proj_start = datetime.datetime.strptime(project_start_date_str, "%Y-%m-%d").date()
        except Exception:
            proj_start = today + datetime.timedelta(days=30) # default to 30 days out

        for cand in candidates:
            emp = cand["employee"]
            emp_id = emp.employee_id
            
            # Rule 1: Account status checks (Account Status and Active version flags)
            if emp.account_status != 1 or emp.is_active_version != 1:
                logger.debug(f"Rejecting candidate {emp_id}: account inactive or outdated version.")
                continue

            # Rule 2: Resignation checks
            if emp.date_of_resignation and emp.date_of_resignation <= today:
                logger.debug(f"Rejecting candidate {emp_id}: employee has resigned as of {emp.date_of_resignation}.")
                continue

            # Rule 3: High utilization checks (e.g. >= 90%)
            if cand["utilization"] >= self.util_limit:
                logger.debug(f"Rejecting candidate {emp_id}: utilization {cand['utilization']}% exceeds threshold {self.util_limit}%.")
                continue

            # Rule 4: Mandatory skills validation
            if self.require_mandatory and required_skills:
                emp_skill_names = set()
                for s in cand["skills"]:
                    if s.skill:
                        emp_skill_names.add(s.skill.lower().strip())
                    if s.subskill:
                        emp_skill_names.add(s.subskill.lower().strip())
                        
                missing_skills = [req.lower().strip() for req in required_skills if req.lower().strip() not in emp_skill_names]
                if missing_skills:
                    logger.debug(f"Rejecting candidate {emp_id}: missing mandatory skills {missing_skills}.")
                    continue

            # Rule 5: Unavailable before start date
            # If they have active allocations that end after the project starts, and their utilization makes them too busy
            is_unavailable = False
            for alloc in cand["allocations"]:
                if alloc.is_allocation_active == 1 and alloc.allocated_end_date:
                    # If current allocation goes past project start date
                    if alloc.allocated_end_date > proj_start:
                        # If their utilization leaves them with zero capacity
                        if cand["utilization"] >= self.util_limit:
                            is_unavailable = True
                            break
            
            if is_unavailable:
                logger.debug(f"Rejecting candidate {emp_id}: locked in projects past start date {proj_start}.")
                continue

            filtered.append(cand)

        logger.info(f"Rules engine completed. Reduced candidate pool from {len(candidates)} to {len(filtered)} items.")
        return filtered
