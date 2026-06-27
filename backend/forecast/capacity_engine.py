import logging
from datetime import date, timedelta
from typing import Dict, List, Any, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database.models import Project, Allocation, Employee
from backend.forecast.demand_feature_builder import DemandFeatureBuilder
from backend.health.service import ProjectHealthService

logger = logging.getLogger("capacity_engine")

class CapacityEngine:
    def __init__(self, db: Session, feature_builder: DemandFeatureBuilder):
        self.db = db
        self.feature_builder = feature_builder

    def get_reference_date(self) -> date:
        """Returns the context reference date (June 27, 2026) or today's date."""
        return date(2026, 6, 27)

    def calculate_capacity_projections(self, reference_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Calculates projected available capacity (FTEs) per role and lists of available
        employees for 0, 30, 60, and 90 days horizons.
        """
        if not reference_date:
            reference_date = self.get_reference_date()
            
        emp_roles = self.feature_builder.load_employee_roles()
        
        # Horizons
        h0 = reference_date
        h30 = h0 + timedelta(days=30)
        h60 = h0 + timedelta(days=60)
        h90 = h0 + timedelta(days=90)
        horizons = [h0, h30, h60, h90]
        
        # 1. Fetch active employees (active account, not resigned before target date)
        employees = self.db.query(Employee).filter(
            Employee.is_active_version == 1,
            Employee.account_status == 1
        ).all()
        
        # 2. Query allocations
        allocations = self.db.query(Allocation).filter(
            Allocation.is_active_version == 1,
            Allocation.is_allocation_active == 1
        ).all()
        
        # 3. Check project health and ramp-downs to adjust release dates
        adjusted_release_dates: Dict[str, date] = {}
        try:
            health_service = ProjectHealthService(self.db)
            rampdowns = health_service.get_rampdown_candidates()
            for r in rampdowns:
                if r.is_suitable and r.earliest_release_date:
                    try:
                        # parse earliest release date
                        release_dt = date.fromisoformat(r.earliest_release_date)
                        adjusted_release_dates[r.project_id] = release_dt
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Could not load health rampdown candidates for capacity adjustments: {e}")
            
        # Also query project health to release red projects early
        try:
            health_service = ProjectHealthService(self.db)
            healths = health_service.get_projects_health()
            for h in healths:
                if h.overall_health == "Red":
                    # Assume RED project resources become available in 15 days
                    adjusted_release_dates[h.project_id] = h0 + timedelta(days=15)
        except Exception as e:
            logger.warning(f"Could not load health statuses: {e}")

        # Compute capacity for each horizon
        # Available capacity = 100% - allocated %
        all_roles = ['Architect', 'Consultant', 'Backend Engineer', 'Frontend Engineer', 'Data Engineer', 'Data Scientist', 'QA', 'DevOps']
        role_key_map = {
            "Architect": "architect",
            "Consultant": "consultant",
            "Backend Engineer": "backend",
            "Frontend Engineer": "frontend",
            "Data Engineer": "data_engineer",
            "Data Scientist": "data_scientist",
            "QA": "qa",
            "DevOps": "devops"
        }
        
        capacity_by_horizon: List[Dict[str, float]] = [{}, {}, {}, {}]  # index maps to h0, h30, h60, h90
        available_emps_by_horizon: List[Dict[str, List[str]]] = [{}, {}, {}, {}] # role -> list of employee_ids
        
        # Initialize capacity
        for idx in range(4):
            for role_name in role_key_map.values():
                capacity_by_horizon[idx][role_name] = 0.0
                available_emps_by_horizon[idx][role_name] = []
                
        for emp in employees:
            role = emp_roles.get(emp.employee_id)
            if role == "Non-Delivery" or not role:
                continue
                
            role_key = role_key_map.get(role)
            if not role_key:
                continue
                
            # Filter allocations for this employee
            emp_allocs = [a for a in allocations if a.employee_id == emp.employee_id]
            
            # Check availability for each horizon
            for idx, h_date in enumerate(horizons):
                # If employee resigned before or on this date, capacity is 0
                if emp.date_of_resignation and emp.date_of_resignation <= h_date:
                    continue
                    
                allocated_pct = 0.0
                for a in emp_allocs:
                    # Determine start/end date
                    a_start = a.allocated_start_date or date(2020, 1, 1)
                    a_end = a.allocated_end_date or date(2099, 12, 31)
                    
                    # Apply adjusted release date if any
                    if a.project_id in adjusted_release_dates:
                        a_end = adjusted_release_dates[a.project_id]
                        
                    # Check if allocation is active on h_date
                    if a_start <= h_date <= a_end:
                        allocated_pct += a.allocation_by_percentage or 100.0
                        
                available_pct = max(0.0, 100.0 - allocated_pct)
                available_fte = available_pct / 100.0
                
                capacity_by_horizon[idx][role_key] += available_fte
                
                # If employee has >= 50% availability, flag them as an available resource candidate
                if available_pct >= 50.0:
                    available_emps_by_horizon[idx][role_key].append(emp.employee_id)
                    
        # Total FTE capacities per horizon
        projections = {
            "available_now": round(sum(capacity_by_horizon[0].values())),
            "available_30_days": round(sum(capacity_by_horizon[1].values())),
            "available_60_days": round(sum(capacity_by_horizon[2].values())),
            "available_90_days": round(sum(capacity_by_horizon[3].values()))
        }
        
        # Details per role
        role_breakdown = {}
        for rk in role_key_map.values():
            role_breakdown[rk] = {
                "available_now": round(capacity_by_horizon[0][rk], 1),
                "available_30_days": round(capacity_by_horizon[1][rk], 1),
                "available_60_days": round(capacity_by_horizon[2][rk], 1),
                "available_90_days": round(capacity_by_horizon[3][rk], 1)
            }
            
        return {
            "capacity_projections": projections,
            "role_breakdown": role_breakdown,
            "available_employees_by_role": available_emps_by_horizon[0], # today's list
            "available_employees_by_role_h30": available_emps_by_horizon[1],
            "available_employees_by_role_h60": available_emps_by_horizon[2],
            "available_employees_by_role_h90": available_emps_by_horizon[3],
            "raw_capacities": capacity_by_horizon
        }
