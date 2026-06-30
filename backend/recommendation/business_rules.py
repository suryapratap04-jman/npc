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

    def filter_candidates(
        self, 
        candidates: List[Dict[str, Any]], 
        required_skills: List[str], 
        project_start_date_str: str,
        department: str = "all",
        experience_range: str = "all",
        availability_window: str = "all",
        location: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Applies rules configuration to discard disqualified resources, and filters by manager selections.
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

            # Rule 3: High utilization checks (e.g. >= 100%)
            # Genuine unavailability is defined as 100% or more allocated during the project window
            if cand["utilization"] >= 100.0:
                logger.debug(f"Rejecting candidate {emp_id}: utilization {cand['utilization']}% is 100% or more.")
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
            # If they have active allocations that end after the project starts, and their utilization makes them genuinely unavailable (>= 100%)
            is_unavailable = False
            for alloc in cand["allocations"]:
                if alloc.is_allocation_active == 1 and alloc.allocated_end_date:
                    # If current allocation goes past project start date
                    if alloc.allocated_end_date > proj_start:
                        # If their utilization leaves them with zero capacity
                        if cand["utilization"] >= 100.0:
                            is_unavailable = True
                            break
            
            if is_unavailable:
                logger.debug(f"Rejecting candidate {emp_id}: locked in projects past start date {proj_start}.")
                continue

            # --- REDESIGNED ACTIVE FILTERS ---
            
            # Department filter
            if department and department.lower().strip() != "all":
                dept_lower = department.lower().strip()
                emp_dept = (emp.department_name or "").lower().strip()
                # Handle Quality Assurance and QA mapping
                if dept_lower == "qa" and "quality assurance" in emp_dept:
                    pass
                elif dept_lower in emp_dept:
                    pass
                else:
                    logger.debug(f"Rejecting candidate {emp_id}: department {emp_dept} does not match filter {department}.")
                    continue

            # Location filter
            if location and location.lower().strip() != "all":
                loc_lower = location.lower().strip()
                emp_loc = (emp.location or "").lower().strip()
                if loc_lower not in emp_loc:
                    logger.debug(f"Rejecting candidate {emp_id}: location {emp_loc} does not match filter {location}.")
                    continue

            # Experience years calculation
            exp_years = 0.0
            for s in cand["skills"]:
                if s.experience_numeric is not None:
                    exp_years = max(exp_years, float(s.experience_numeric))
            if exp_years == 0.0:
                exp_years = 4.0 # default baseline fallback

            # Experience range filter
            if experience_range and experience_range.lower().strip() != "all":
                exp_rng = experience_range.lower().strip()
                if exp_rng == "senior" and exp_years < 5.0:
                    logger.debug(f"Rejecting candidate {emp_id}: experience {exp_years} yrs < 5 yrs (Senior).")
                    continue
                elif exp_rng == "mid" and not (3.0 <= exp_years <= 5.0):
                    logger.debug(f"Rejecting candidate {emp_id}: experience {exp_years} yrs not in 3-5 yrs (Mid).")
                    continue
                elif exp_rng == "junior" and exp_years >= 3.0:
                    logger.debug(f"Rejecting candidate {emp_id}: experience {exp_years} yrs >= 3 yrs (Junior).")
                    continue

            # Availability window filter
            if availability_window and availability_window.lower().strip() != "all":
                avail_win = availability_window.lower().strip()
                # Find maximum end date of current allocations
                max_end = None
                for alloc in cand["allocations"]:
                    if alloc.is_allocation_active == 1 and alloc.allocated_end_date:
                        if max_end is None or alloc.allocated_end_date > max_end:
                            max_end = alloc.allocated_end_date

                if avail_win in ("available now", "bench resources"):
                    # Bench or immediately available: utilization must be 0
                    if cand["utilization"] > 0.0:
                        logger.debug(f"Rejecting candidate {emp_id}: not immediately available (utilization {cand['utilization']}%).")
                        continue
                elif avail_win == "available within 2 weeks":
                    limit_date = proj_start + datetime.timedelta(days=14)
                    if max_end and max_end > limit_date and cand["utilization"] >= 50.0:
                        logger.debug(f"Rejecting candidate {emp_id}: allocated past 2-week window (ends {max_end}).")
                        continue
                elif avail_win == "available within 30 days":
                    limit_date = proj_start + datetime.timedelta(days=30)
                    if max_end and max_end > limit_date and cand["utilization"] >= 50.0:
                        logger.debug(f"Rejecting candidate {emp_id}: allocated past 30-day window (ends {max_end}).")
                        continue
                elif avail_win == "allocation <50%":
                    if cand["utilization"] >= 50.0:
                        logger.debug(f"Rejecting candidate {emp_id}: utilization {cand['utilization']}% >= 50%.")
                        continue

            filtered.append(cand)

        logger.info(f"Rules engine completed. Reduced candidate pool from {len(candidates)} to {len(filtered)} items.")
        return filtered
