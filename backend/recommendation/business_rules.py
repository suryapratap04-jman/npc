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
        today = datetime.date.today()
        
        # Parse project start date
        try:
            proj_start = datetime.datetime.strptime(project_start_date_str, "%Y-%m-%d").date()
        except Exception:
            proj_start = today + datetime.timedelta(days=30) # default to 30 days out

        total_candidates = len(candidates)
        logger.info(f"[STAGE 1] Total Employees in pool: {total_candidates}")

        # Stage 2: Active status & Resignation Filter
        active_candidates = []
        for cand in candidates:
            emp = cand["employee"]
            emp_id = emp.employee_id
            
            # Rule 1: Account status checks (Account Status and Active version flags)
            account_status = getattr(emp, "account_status", None)
            is_active_version = getattr(emp, "is_active_version", None)
            
            if account_status != 1 or is_active_version != 1:
                logger.debug(f"Rejecting candidate {emp_id}: account inactive or outdated version.")
                continue

            # Rule 2: Resignation checks
            res_date = getattr(emp, "date_of_resignation", None)
            if isinstance(res_date, str):
                try:
                    res_date = datetime.date.fromisoformat(res_date)
                except ValueError:
                    res_date = None
            if res_date and res_date <= today:
                logger.debug(f"Rejecting candidate {emp_id}: employee has resigned as of {res_date}.")
                continue
                
            active_candidates.append(cand)
            
        active_count = len(active_candidates)
        logger.info(f"[STAGE 2] Active Employees remaining: {active_count} (Removed {total_candidates - active_count} inactive/resigned)")

        # Stage 3: Availability Filter
        avail_candidates = []
        for cand in active_candidates:
            emp = cand["employee"]
            emp_id = emp.employee_id
            
            # Rule 3: High utilization checks (e.g. >= 100%)
            if cand["utilization"] >= 100.0:
                logger.debug(f"Rejecting candidate {emp_id}: utilization {cand['utilization']}% is 100% or more.")
                continue

            # Rule 5: Unavailable before start date
            is_unavailable = False
            for alloc in cand["allocations"]:
                is_active = getattr(alloc, "is_allocation_active", 0)
                if is_active == 1:
                    a_end = getattr(alloc, "allocated_end_date", None)
                    if isinstance(a_end, str):
                        try:
                            a_end = datetime.date.fromisoformat(a_end)
                        except ValueError:
                            a_end = None
                    if a_end and a_end > proj_start:
                        if cand["utilization"] >= 100.0:
                            is_unavailable = True
                            break
            
            if is_unavailable:
                logger.debug(f"Rejecting candidate {emp_id}: locked in projects past start date {proj_start}.")
                continue
                
            avail_candidates.append(cand)
            
        avail_count = len(avail_candidates)
        logger.info(f"[STAGE 3] Availability Filter remaining: {avail_count} (Removed {active_count - avail_count} due to utilization >= 100%)")

        # Stage 4: Skill Filter
        skill_candidates = []
        for cand in avail_candidates:
            emp = cand["employee"]
            emp_id = emp.employee_id
            
            if self.require_mandatory and required_skills:
                emp_skill_names = set()
                for s in cand["skills"]:
                    if getattr(s, "score", 0.0) and float(s.score) > 0.0:
                        if s.skill:
                            emp_skill_names.add(s.skill.lower().strip())
                        if s.subskill:
                            emp_skill_names.add(s.subskill.lower().strip())
                        
                missing_skills = [req.lower().strip() for req in required_skills if req.lower().strip() not in emp_skill_names]
                if missing_skills:
                    logger.debug(f"Rejecting candidate {emp_id}: missing mandatory skills {missing_skills}.")
                    continue
                    
            skill_candidates.append(cand)
            
        skill_count = len(skill_candidates)
        logger.info(f"[STAGE 4] Skill Filter remaining: {skill_count} (Removed {avail_count - skill_count} due to missing mandatory skills)")

        # Stage 5: Experience Filter
        exp_candidates = []
        for cand in skill_candidates:
            emp = cand["employee"]
            emp_id = emp.employee_id
            
            # Experience years calculation
            exp_years = 0.0
            for s in cand["skills"]:
                if s.experience_numeric is not None:
                    exp_years = max(exp_years, float(s.experience_numeric))
            if exp_years == 0.0:
                exp_years = 4.0 # default baseline fallback

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
                    
            exp_candidates.append(cand)
            
        exp_count = len(exp_candidates)
        logger.info(f"[STAGE 5] Experience Filter remaining: {exp_count} (Removed {skill_count - exp_count} due to experience range constraints)")

        # Stage 6: Utilization Filter
        util_candidates = []
        for cand in exp_candidates:
            emp = cand["employee"]
            emp_id = emp.employee_id
            
            # Department filter
            if department and department.lower().strip() != "all":
                dept_lower = department.lower().strip()
                emp_dept = (emp.department_name or "").lower().strip()
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

            # Availability window filter
            if availability_window and availability_window.lower().strip() != "all":
                avail_win = availability_window.lower().strip()
                max_end = None
                for alloc in cand["allocations"]:
                    is_active = getattr(alloc, "is_allocation_active", 0)
                    if is_active == 1:
                        a_end = getattr(alloc, "allocated_end_date", None)
                        if isinstance(a_end, str):
                            try:
                                a_end = datetime.date.fromisoformat(a_end)
                            except ValueError:
                                a_end = None
                        if a_end:
                            if max_end is None or a_end > max_end:
                                max_end = a_end

                if avail_win in ("available now", "bench resources"):
                    if cand["utilization"] > 0.0:
                        logger.debug(f"Rejecting candidate {emp_id}: not immediately available.")
                        continue
                elif avail_win == "available within 2 weeks":
                    limit_date = proj_start + datetime.timedelta(days=14)
                    if max_end and max_end > limit_date and cand["utilization"] >= 50.0:
                        logger.debug(f"Rejecting candidate {emp_id}: allocated past 2-week window.")
                        continue
                elif avail_win == "available within 30 days":
                    limit_date = proj_start + datetime.timedelta(days=30)
                    if max_end and max_end > limit_date and cand["utilization"] >= 50.0:
                        logger.debug(f"Rejecting candidate {emp_id}: allocated past 30-day window.")
                        continue
                elif avail_win == "allocation <50%":
                    if cand["utilization"] >= 50.0:
                        logger.debug(f"Rejecting candidate {emp_id}: utilization >= 50%.")
                        continue
                        
            util_candidates.append(cand)
            
        util_count = len(util_candidates)
        logger.info(f"[STAGE 6] Utilization/Window/Location/Dept Filters remaining: {util_count} (Removed {exp_count - util_count} due to custom rules)")

        # Stage 7: Competency Filter
        comp_count = util_count
        logger.info(f"[STAGE 7] Competency Filter remaining: {comp_count} (0 competency constraints applied)")

        return util_candidates
