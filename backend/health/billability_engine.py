import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.database.models import Timesheet

logger = logging.getLogger("health_billability_engine")

class BillabilityEngine:
    def __init__(self, db: Session):
        self.db = db

    def analyze_billability(self, project_id: str, team_employee_ids: List[str]) -> Dict[str, Any]:
        """
        Calculates billable vs non-billable timesheet stats, flags shadow resources, and checks cost recovery.
        """
        # 1. Fetch timesheets
        timesheets = self.db.query(Timesheet).filter(Timesheet.project_id == project_id).all()
        
        billable_hours = sum(float(t.time or 0.0) for t in timesheets if t.is_billable)
        non_billable_hours = sum(float(t.time or 0.0) for t in timesheets if not t.is_billable)
        total_hours = billable_hours + non_billable_hours

        # Billability percentage
        billability_pct = 100.0
        if total_hours > 0.0:
            billability_pct = (billable_hours / total_hours) * 100.0

        # Cost recovery status
        if billability_pct >= 90.0:
            cost_recovery = "Good"
        elif billability_pct >= 70.0:
            cost_recovery = "Degraded"
        else:
            cost_recovery = "Poor"

        # 2. Shadow resources: active team members on this project who have logged 0 billable hours in last 14 days
        shadow_count = 0
        if team_employee_ids:
            import datetime
            cutoff = datetime.date.today() - datetime.timedelta(days=14)
            
            # Query billable timesheets for team in last 14 days
            recent_billable = self.db.query(Timesheet.employee_id).filter(
                Timesheet.project_id == project_id,
                Timesheet.employee_id.in_(team_employee_ids),
                Timesheet.is_billable == True,
                Timesheet.date >= cutoff
            ).all()
            
            active_billable_emp_ids = {r[0] for r in recent_billable}
            shadow_count = len(set(team_employee_ids) - active_billable_emp_ids)

        # 3. Billability trend (last 4 weeks)
        today = datetime.date.today()
        weekly_billable = [0.0, 0.0, 0.0, 0.0]
        weekly_total = [0.0, 0.0, 0.0, 0.0]
        
        for t in timesheets:
            if t.date:
                days_ago = (today - t.date).days
                week_idx = -1
                if days_ago < 7:
                    week_idx = 3
                elif days_ago < 14:
                    week_idx = 2
                elif days_ago < 21:
                    week_idx = 1
                elif days_ago < 28:
                    week_idx = 0
                
                if week_idx >= 0:
                    weekly_total[week_idx] += float(t.time or 0.0)
                    if t.is_billable:
                        weekly_billable[week_idx] += float(t.time or 0.0)

        # Compute billability % per week
        weekly_pct = [100.0, 100.0, 100.0, 100.0]
        for i in range(4):
            if weekly_total[i] > 0.0:
                weekly_pct[i] = (weekly_billable[i] / weekly_total[i]) * 100.0

        if weekly_pct[3] > weekly_pct[0] + 5.0:
            trend = "Improving"
        elif weekly_pct[3] < weekly_pct[0] - 5.0:
            trend = "Declining"
        else:
            trend = "Stable"

        return {
            "percentage": round(billability_pct, 2),
            "billable_hours": round(billable_hours, 2),
            "non_billable_hours": round(non_billable_hours, 2),
            "shadow_resources_count": shadow_count,
            "billability_trend": trend,
            "cost_recovery_status": cost_recovery
        }
