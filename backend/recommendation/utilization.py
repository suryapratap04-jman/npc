import datetime
from datetime import date
from typing import List, Dict, Any, Optional

def calculate_active_utilization(
    allocations: List[Any],
    projects_info: Dict[str, Any],
    target_start: Optional[date] = None,
    target_end: Optional[date] = None
) -> float:
    """
    Centralized, audited calculator for active employee utilization.
    Ignores historical, expired, and JMAN internal/BAU allocations.
    Caps total utilization at 100.0% to reflect standard capacity limits.
    """
    today = date.today()
    total_util = 0.0
    
    for a in allocations:
        # 1. Must be active allocation
        is_active = getattr(a, "is_allocation_active", 0)
        if isinstance(a, dict):
            is_active = a.get("is_allocation_active", 0)
        if is_active != 1:
            continue
            
        # 2. Get project details if mapped
        proj_id = getattr(a, "project_id", None)
        if isinstance(a, dict):
            proj_id = a.get("project_id", None)
            
        proj_info = projects_info.get(proj_id)
        
        # 3. Determine effective end date
        a_end = getattr(a, "allocated_end_date", None)
        if isinstance(a, dict):
            a_end = a.get("allocated_end_date", None)
            
        if isinstance(a_end, str):
            try:
                a_end = date.fromisoformat(a_end)
            except ValueError:
                a_end = None
                
        p_end = None
        if proj_info:
            p_end = proj_info.get("project_end_date") if isinstance(proj_info, dict) else getattr(proj_info, "project_end_date", None)
            if isinstance(p_end, str):
                try:
                    p_end = date.fromisoformat(p_end)
                except ValueError:
                    p_end = None
                    
        effective_end = a_end or p_end or date(2099, 12, 31)
        if isinstance(effective_end, str):
            try:
                effective_end = date.fromisoformat(effective_end)
            except ValueError:
                effective_end = date(2099, 12, 31)
        
        # 4. Ignore expired allocations (ended before today)
        if effective_end < today:
            continue
            
        # 5. Ignore JMAN internal/BAU allocations
        is_bau = False
        if proj_info:
            client_id = proj_info.get("client_id") if isinstance(proj_info, dict) else getattr(proj_info, "client_id", None)
            proj_type = proj_info.get("type_of_project") if isinstance(proj_info, dict) else getattr(proj_info, "type_of_project", None)
            if client_id == "CLIENT_127" or proj_type == "BAU Activity":
                is_bau = True
        else:
            if proj_id and proj_id.startswith("CLIENT_127"):
                is_bau = True
        if is_bau:
            continue
            
        # 6. Check overlap with target window if specified
        if target_start and target_end:
            a_start = getattr(a, "allocated_start_date", None)
            if isinstance(a, dict):
                a_start = a.get("allocated_start_date", None)
            if isinstance(a_start, str):
                try:
                    a_start = date.fromisoformat(a_start)
                except ValueError:
                    a_start = None
            if isinstance(a_start, datetime.datetime):
                a_start = a_start.date()
            if not a_start:
                a_start = date(2020, 1, 1)
                
            if effective_end < target_start or a_start > target_end:
                continue
                
        # 7. Add allocation percentage
        pct = getattr(a, "allocation_by_percentage", 100.0)
        if isinstance(a, dict):
            pct = a.get("allocation_by_percentage", 100.0)
        if pct is None:
            pct = 100.0
        total_util += float(pct)
        
    return min(total_util, 100.0)
