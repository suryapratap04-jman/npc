import logging
import datetime
from collections import defaultdict
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.database.models import Employee, Project, Allocation, Timesheet, WeeklyStatus

logger = logging.getLogger("health_feature_builder")

class HealthFeatureBuilder:
    def __init__(self, db: Session):
        self.db = db

    def build_project_features(self, project_id: str) -> Dict[str, Any]:
        """
        Gathers timeline, allocation, timesheet, and weekly status metrics for a project.
        """
        logger.info(f"Building features for project {project_id}")
        today = datetime.date.today()

        # 1. Fetch project master data
        project = self.db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise ValueError(f"Project ID {project_id} not found in database.")

        # --- SCHEDULE FEATURES ---
        planned_dur = 0
        actual_dur = 0
        delay_days = 0
        days_remaining = 0
        
        if project.project_start_date and project.project_end_date:
            planned_dur = (project.project_end_date - project.project_start_date).days
            
            if today >= project.project_start_date:
                actual_dur = (today - project.project_start_date).days
            else:
                actual_dur = 0

            days_remaining = (project.project_end_date - today).days
            
            # If overdue and status not complete/closed
            if today > project.project_end_date and project.project_status not in ["CLOSED", "COMPLETE", "DEAL LOST"]:
                delay_days = (today - project.project_end_date).days
            else:
                delay_days = 0

        # --- ALLOCATION FEATURES ---
        allocs = self.db.query(Allocation).filter(
            Allocation.project_id == project_id,
            Allocation.is_allocation_active == 1
        ).all()

        team_size = len({a.employee_id for a in allocs if a.employee_id})
        active_allocations_count = len(allocs)

        alloc_pcts = [float(a.allocation_by_percentage or 0.0) for a in allocs]
        avg_alloc_pct = sum(alloc_pcts) / len(alloc_pcts) if alloc_pcts else 0.0
        max_alloc_pct = max(alloc_pcts) if alloc_pcts else 0.0

        # Calculate overallocation / underutilization counts (across ALL active projects)
        overallocated_count = 0
        underutilized_count = 0
        
        emp_ids = [a.employee_id for a in allocs if a.employee_id]
        if emp_ids:
            # Query all active allocations for these employees globally
            global_allocs = self.db.query(Allocation).filter(
                Allocation.employee_id.in_(emp_ids),
                Allocation.is_allocation_active == 1
            ).all()

            global_util = defaultdict(float)
            for ga in global_allocs:
                global_util[ga.employee_id] += float(ga.allocation_by_percentage or 0.0)

            for emp_id in emp_ids:
                total_util = global_util[emp_id]
                if total_util > 100.0:
                    overallocated_count += 1
                elif total_util < 40.0:
                    underutilized_count += 1

        # Extensions count: allocations whose end date is past the project end date
        extension_count = 0
        if project.project_end_date:
            extension_count = sum(
                1 for a in allocs 
                if a.allocated_end_date and a.allocated_end_date > project.project_end_date
            )

        # --- TIMESHEET FEATURES ---
        timesheets = self.db.query(Timesheet).filter(Timesheet.project_id == project_id).all()
        total_hours = sum(float(t.time or 0.0) for t in timesheets)

        # Calculate weekly trend (last 4 weeks)
        weekly_hours = [0.0, 0.0, 0.0, 0.0]
        for t in timesheets:
            if t.date:
                days_ago = (today - t.date).days
                if days_ago < 7:
                    weekly_hours[3] += float(t.time or 0.0)
                elif days_ago < 14:
                    weekly_hours[2] += float(t.time or 0.0)
                elif days_ago < 21:
                    weekly_hours[1] += float(t.time or 0.0)
                elif days_ago < 28:
                    weekly_hours[0] += float(t.time or 0.0)

        # Trend label
        if weekly_hours[3] > weekly_hours[0] + 5.0:
            weekly_trend = "Improving"
        elif weekly_hours[3] < weekly_hours[0] - 5.0:
            weekly_trend = "Declining"
        else:
            weekly_trend = "Stable"

        # Missing submissions in current week
        missing_submissions = 0
        if emp_ids:
            submitted_emp_ids = {
                t.employee_id for t in timesheets 
                if t.date and (today - t.date).days < 7
            }
            missing_submissions = len(set(emp_ids) - submitted_emp_ids)

        # Average utilization in timesheets (hours logged vs expected 40h)
        avg_logged_util = 0.0
        if team_size > 0:
            # Look at past 4 weeks logs
            avg_logged_util = (sum(weekly_hours) / 4.0) / (team_size * 40.0) * 100.0

        # --- WEEKLY STATUS FEATURES ---
        # Note: project_id_masked is the project ID column in weekly_status
        wsr = self.db.query(WeeklyStatus).filter(
            WeeklyStatus.project_id_masked == project_id
        ).order_by(WeeklyStatus.week_end_date.desc()).first()

        scope_status = wsr.scope_status if wsr and wsr.scope_status else "Green"
        schedule_status = wsr.schedule_status if wsr and wsr.schedule_status else "Green"
        quality_status = wsr.quality_status if wsr and wsr.quality_status else "Green"
        csat_status = wsr.csat_status if wsr and wsr.csat_status else "Green"

        return {
            "project_id": project_id,
            "project_key": project.project_key,
            "project_status": project.project_status,
            "planned_duration": planned_dur,
            "actual_duration": actual_dur,
            "delay_days": delay_days,
            "days_remaining": days_remaining,
            "extension_count": extension_count,
            "team_size": team_size,
            "active_allocations": active_allocations_count,
            "average_allocation": avg_alloc_pct,
            "maximum_allocation": max_alloc_pct,
            "overallocated_count": overallocated_count,
            "underutilized_count": underutilized_count,
            "total_hours": total_hours,
            "weekly_trend": weekly_trend,
            "missing_submissions": missing_submissions,
            "average_logged_utilization": round(avg_logged_util, 2),
            "scope_status": scope_status,
            "schedule_status": schedule_status,
            "quality_status": quality_status,
            "csat_status": csat_status
        }
