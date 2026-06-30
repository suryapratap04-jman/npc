import logging
import datetime
from collections import defaultdict, Counter
from sqlalchemy.orm import Session

from backend.database.models import Employee, Project, Allocation, Pipeline, Skill
from backend.forecast.demand_feature_builder import DemandFeatureBuilder
from backend.forecast.service import ForecastService
from backend.health.service import ProjectHealthService

logger = logging.getLogger("dashboard_service")

# Mapping of CRM pipeline resource descriptions to standard target roles
RESOURCE_TO_ROLE = {
    'SAC': 'Architect', 'SAC/AC': 'Architect', 'SAC - C': 'Architect', 'SAC or AC': 'Architect', 'GTM Architect': 'Architect',
    'C': 'Consultant', 'C ': 'Consultant', 'C  ': 'Consultant', 'AC': 'Consultant', 'AC ': 'Consultant', 'AC (UK)': 'Consultant',
    'SC': 'Consultant', 'SC  ': 'Consultant', 'SC (EM)': 'Consultant', 'SC or C - EM': 'Consultant', 'Sol Con': 'Consultant',
    'Sol Con ': 'Consultant', 'Sol Con  ': 'Consultant', 'Sr Sol Con': 'Consultant', 'Snr Sol Con': 'Consultant',
    'EM': 'Consultant', 'M': 'Consultant',
    'SSE': 'Backend Engineer', 'SSE  ': 'Backend Engineer', 'SSE ': 'Backend Engineer', 'SSE  or SE': 'Backend Engineer',
    'SE': 'Backend Engineer', 'SE ': 'Backend Engineer', 'SE  ': 'Backend Engineer',
    'Enabler': 'DevOps', 'Enabler ': 'DevOps', 'Enabler  ': 'DevOps',
    'Sr DS SME': 'Data Scientist', 'Data Scientist': 'Data Scientist',
    'PA': 'Non-Delivery', 'PA  ': 'Non-Delivery', 'AP': 'Non-Delivery', 'AP/P': 'Non-Delivery', 'AP ': 'Non-Delivery',
    'P': 'Non-Delivery', 'P ': 'Non-Delivery'
}

def map_pipeline_resource_to_role(req_str: str) -> str:
    """Parses pipeline resource requested and maps to target business role."""
    clean_req = (req_str or "").strip()
    if not clean_req:
        return 'Consultant'
    
    # Try direct mapping
    if clean_req in RESOURCE_TO_ROLE:
        return RESOURCE_TO_ROLE[clean_req]
        
    req_lower = clean_req.lower()
    if 'architect' in req_lower:
        return 'Architect'
    elif 'devops' in req_lower or 'enabler' in req_lower:
        return 'DevOps'
    elif 'qa' in req_lower or 'test' in req_lower:
        return 'QA'
    elif 'data scientist' in req_lower or 'ds' in req_lower or 'scientist' in req_lower:
        return 'Data Scientist'
    elif 'data engineer' in req_lower:
        return 'Data Engineer'
    elif 'frontend' in req_lower:
        return 'Frontend Engineer'
    elif 'backend' in req_lower or 'software engineer' in req_lower or 'se' in req_lower or 'developer' in req_lower:
        return 'Backend Engineer'
    
    return 'Consultant'


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.feature_builder = DemandFeatureBuilder(db)
        self.forecast_service = ForecastService(db)
        self.health_service = ProjectHealthService(db)

    def get_dashboard_overview(self) -> dict:
        """
        Calculates and returns consolidated dashboard KPI cards, charts, summaries, 
        and timeline lists from the relational database using business logic.
        """
        ref_date = self.forecast_service.get_reference_date()
        limit_date = ref_date + datetime.timedelta(days=30)
        
        # Load active employee roles using feature builder cache
        emp_roles = self.feature_builder.load_employee_roles()
        
        # 1. Fetch active employees (joined before reference date and not resigned before reference date)
        active_employees_all = self.db.query(Employee).filter(
            Employee.is_active_version == 1,
            Employee.account_status == 1
        ).all()
        
        employees = []
        for emp in active_employees_all:
            joined = emp.date_of_join or datetime.date(2020, 1, 1)
            resigned = emp.date_of_resignation
            if joined <= ref_date:
                if not resigned or resigned >= ref_date:
                    employees.append(emp)
                    
        total_active_count = len(employees)
        
        # 2. Fetch active allocations today
        allocations = self.db.query(Allocation).join(Project, Project.project_id == Allocation.project_id).filter(
            Allocation.is_active_version == 1,
            Allocation.is_allocation_active == 1,
            Allocation.impossible_value_flag == 0,
            Allocation.employee_id != 'VACANT_ROLE',
            Project.is_active_version == 1,
            ~Project.project_status.in_(['CLOSED', 'COMPLETE', 'DEAL LOST']),
            Allocation.allocated_start_date <= ref_date,
            Allocation.allocated_end_date >= ref_date
        ).all()
        
        # 3. Compute utilization stats
        emp_util = defaultdict(float)
        for a in allocations:
            emp_util[a.employee_id] += float(a.allocation_by_percentage or 0.0)
            
        capped_utils = []
        overallocated_count = 0
        underutilized_count = 0
        bench_count = 0
        target_count = 0
        
        for emp in employees:
            util = emp_util[emp.employee_id]
            if util > 100.0:
                overallocated_count += 1
            elif util < 50.0:
                underutilized_count += 1
                if util == 0.0:
                    bench_count += 1
            if 80.0 <= util <= 100.0:
                target_count += 1
                
            capped_utils.append(min(100.0, util))
            
        avg_util = sum(capped_utils) / max(1, total_active_count)
        
        # Calculate median utilization
        sorted_utils = sorted(capped_utils)
        if total_active_count == 0:
            median_util = 0.0
        elif total_active_count % 2 == 1:
            median_util = sorted_utils[total_active_count // 2]
        else:
            median_util = (sorted_utils[(total_active_count // 2) - 1] + sorted_utils[total_active_count // 2]) / 2.0
            
        bench_pct = (bench_count / max(1, total_active_count)) * 100.0
        overallocated_pct = (overallocated_count / max(1, total_active_count)) * 100.0
        
        # 4. Fetch project health breakdown
        healths = self.health_service.get_projects_health()
        redCount = sum(1 for h in healths if h.overall_health == "Red")
        amberCount = sum(1 for h in healths if h.overall_health == "Amber")
        greenCount = sum(1 for h in healths if h.overall_health == "Green")
        
        red_project_ids = [h.project_id for h in healths if h.overall_health == "Red"]
        
        # 5. Role-based Hiring Needed (calculated per role)
        # Find bench by role today
        bench_by_role = defaultdict(int)
        for emp in employees:
            if emp_util[emp.employee_id] == 0.0:
                r = emp_roles.get(emp.employee_id, 'Consultant')
                bench_by_role[r] += 1
                
        # Find pipeline demand in next 30 days
        pipeline_deals_30d = self.db.query(Pipeline).filter(
            Pipeline.likely_start_date >= ref_date,
            Pipeline.likely_start_date <= limit_date
        ).all()
        
        demand_by_role = defaultdict(int)
        for deal in pipeline_deals_30d:
            role = map_pipeline_resource_to_role(deal.resources_requested)
            demand_by_role[role] += 1
            
        # Find expected roll-offs in next 30 days
        rolloffs_30d = self.db.query(Allocation).join(Project, Project.project_id == Allocation.project_id).filter(
            Allocation.is_active_version == 1,
            Allocation.is_allocation_active == 1,
            Allocation.impossible_value_flag == 0,
            Allocation.employee_id != 'VACANT_ROLE',
            Project.is_active_version == 1,
            ~Project.project_status.in_(['CLOSED', 'COMPLETE', 'DEAL LOST']),
            Allocation.allocated_end_date >= ref_date,
            Allocation.allocated_end_date <= limit_date
        ).all()
        
        rolloff_by_role = defaultdict(int)
        seen_rolloff_emp = set()
        for a in rolloffs_30d:
            if a.employee_id not in seen_rolloff_emp:
                r = emp_roles.get(a.employee_id, 'Consultant')
                rolloff_by_role[r] += 1
                seen_rolloff_emp.add(a.employee_id)
                
        # Net external hiring needed
        hiring_needed = 0
        roles_list = ['Architect', 'Consultant', 'Backend Engineer', 'Frontend Engineer', 'Data Engineer', 'Data Scientist', 'QA', 'DevOps', 'Non-Delivery']
        for r in roles_list:
            d = demand_by_role.get(r, 0)
            ro = rolloff_by_role.get(r, 0)
            b = bench_by_role.get(r, 0)
            hiring_needed += max(0, d - ro - b)
            
        # 6. Compose capacity chart mapping from six-month forecast
        six_month_forecast = self.forecast_service.get_six_month_forecast()
        capacityChart = []
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        for m in six_month_forecast.monthly_projections:
            parts = m.month.split("-")
            month_idx = int(parts[1]) - 1 if len(parts) > 1 and parts[1].isdigit() else 0
            short_month = month_names[month_idx] if month_idx < 12 else m.month
            
            capacityChart.append({
                "month": short_month,
                "Supply": MathRound(m.headcount_demand + m.capacity_surplus - m.capacity_deficit),
                "Demand": MathRound(m.headcount_demand),
                "Pipeline": max(0, MathRound(m.capacity_deficit))
            })
            
        # 7. Compose project health row list
        projects_dict = {p.project_id: p for p in self.db.query(Project).filter(Project.is_active_version == 1).all()}
        staff_counts = defaultdict(int)
        allocs_all = self.db.query(Allocation).filter(
            Allocation.is_active_version == 1,
            Allocation.is_allocation_active == 1,
            Allocation.employee_id != 'VACANT_ROLE'
        ).all()
        for a in allocs_all:
            staff_counts[a.project_id] += 1
            
        util_stats = {u["project_id"]: u["average_utilization"] for u in self.health_service.get_utilization_stats()}
        
        projectHealth = []
        for h in healths:
            p = projects_dict.get(h.project_id)
            client_name = p.client_id if p else "N/A"
            pm_name = p.reporter_id if p else "N/A"
            proj_name = p.project_key if p and p.project_key else f"Project {h.project_id}"
            
            avg_util_val = util_stats.get(h.project_id, 100.0)
            
            risk_detail = "On schedule"
            if h.overall_health == "Red":
                risk_detail = "Critical staff gap detected"
            elif h.overall_health == "Amber":
                risk_detail = "Schedule delay risk warning"
                
            projectHealth.append({
                "id": h.project_id,
                "name": proj_name,
                "client": client_name,
                "status": h.overall_health,
                "progress": int(round(avg_util_val)),
                "PM": pm_name,
                "staffCount": staff_counts[h.project_id],
                "riskDetail": risk_detail
            })
            
        # 8. Compose Availability timeline (first 5 unique employees rolling off in next 30 days)
        # Fallback to benched employees if no roll-offs exist
        availabilityTimeline = []
        seen_emp = set()
        for a in rolloffs_30d:
            if a.employee_id in seen_emp:
                continue
            seen_emp.add(a.employee_id)
            
            emp = employees_dict_lookup(self.db, a.employee_id)
            emp_role = emp_roles.get(a.employee_id, "Consultant")
            days_left = (a.allocated_end_date - ref_date).days
            
            availabilityTimeline.append({
                "id": a.employee_id,
                "name": a.employee_id,
                "skill": emp_role,
                "project": a.project_id,
                "date": a.allocated_end_date.strftime("%Y-%m-%d"),
                "daysRemaining": max(0, days_left)
            })
            if len(availabilityTimeline) >= 5:
                break
                
        # If less than 5 roll-offs found, pad with currently benched employees
        if len(availabilityTimeline) < 5:
            for emp in employees:
                if emp_util[emp.employee_id] == 0.0 and emp.employee_id not in seen_emp:
                    seen_emp.add(emp.employee_id)
                    emp_role = emp_roles.get(emp.employee_id, "Consultant")
                    availabilityTimeline.append({
                        "id": emp.employee_id,
                        "name": emp.employee_id,
                        "skill": emp_role,
                        "project": "Unallocated",
                        "date": "Available Now",
                        "daysRemaining": 0
                    })
                    if len(availabilityTimeline) >= 5:
                        break
                        
        # 9. Pipeline deals (top 3)
        pipeline_deals_all = self.db.query(Pipeline).filter(
            Pipeline.likely_start_date >= ref_date
        ).order_by(Pipeline.likely_start_date.asc()).limit(3).all()
        
        pipelineDeals = []
        for deal in pipeline_deals_all:
            prob = "0%"
            if deal.percentage:
                pct_str = deal.percentage.replace("%", "").strip()
                if pct_str.isdigit():
                    prob = f"{pct_str}%"
                    
            hc = 1.0
            try:
                req_res = str(deal.resources_requested or "")
                if "," in req_res:
                    hc = float(len(req_res.split(",")))
                elif req_res and req_res[0].isdigit():
                    hc = float(req_res[0])
            except Exception:
                pass
                
            weeks = 12
            try:
                w_str = str(deal.number_of_weeks or "")
                if w_str.isdigit():
                    weeks = int(w_str)
            except Exception:
                pass
                
            deal_size_k = round((hc * weeks * 4000) / 1000)
            
            pipelineDeals.append({
                "id": f"DEAL-{deal.id}",
                "client": deal.client or "Client Account",
                "project": deal.solution or "Consulting Contract",
                "start": deal.likely_start_date.strftime("%Y-%m-%d") if deal.likely_start_date else "",
                "probability": prob,
                "size": f"${deal_size_k}K",
                "roles": [deal.resources_requested.strip()] if deal.resources_requested else []
            })
            
        # 10. Recent Activity list
        recentActivity = [
            { "id": "ACT-01", "time": "Recent", "category": "allocation", "text": f"Active benched headcount is currently {bench_count} developers." },
            { "id": "ACT-02", "time": "Recent", "category": "risk", "text": f"Database scanned. Flagged {redCount} Red and {amberCount} Amber project risks." },
            { "id": "ACT-03", "time": "Recent", "category": "pipeline", "text": f"{len(pipeline_deals_30d)} active deals synced from CRM HubSpot pipeline in next 30 days." }
        ]
        
        # 11. AI Actions
        aiActions = []
        if redCount > 0:
            red_proj_id = red_project_ids[0]
            aiActions.append({
                "id": "ACT-REC-1",
                "title": "Resolve Staffing Vacancies",
                "description": f"Trigger Recommendation matching to resolve critical staffing gap for Red project {red_proj_id}.",
                "type": "allocation",
                "path": f"/recommendation?project={red_proj_id}"
            })
        else:
            aiActions.append({
                "id": "ACT-REC-1",
                "title": "Optimize Staffing Allocations",
                "description": "Trigger Recommendation matching to clear benched developers.",
                "type": "allocation",
                "path": "/recommendation"
            })
            
        aiActions.append({
            "id": "ACT-REC-2",
            "title": "Run Capacity Gaps Outlooks",
            "description": "Review six-month capacity deficit models.",
            "type": "hiring",
            "path": "/forecast"
        })
        
        # 12. AI summary text
        aiSummary = (
            f"Active utilization averages {int(round(avg_util))}% (against an 80% operational threshold). "
            f"Relational scan registers {redCount} critical Red status project{'s' if redCount != 1 else ''}. "
            f"There are {bench_count} available employee{'s' if bench_count != 1 else ''} currently unallocated or on bench, "
            f"while forecasting indicates {hiring_needed} open hire{'s' if hiring_needed != 1 else ''} will be required over the upcoming month."
        )
        
        return {
            "aiSummary": aiSummary,
            "kpiCards": [
                {
                    "id": "utilization",
                    "title": "Current Utilization",
                    "value": f"{int(round(avg_util))}%",
                    "change": "Capped at 100% per FTE",
                    "status": "good" if avg_util >= 80 else "neutral",
                    "detail": "Target: 80% threshold",
                    "color": "blue"
                },
                {
                    "id": "risks",
                    "title": "Projects At Risk",
                    "value": f"{redCount} Critical",
                    "change": f"{amberCount} Amber warnings",
                    "status": "bad" if redCount > 0 else "good",
                    "detail": f"{len(healths)} active projects audited",
                    "color": "red"
                },
                {
                    "id": "bench",
                    "title": "Available Employees",
                    "value": f"{bench_count} Benched",
                    "change": "Ready for allocation",
                    "status": "good" if bench_count > 0 else "neutral",
                    "detail": "0% active allocation",
                    "color": "green"
                },
                {
                    "id": "hiring",
                    "title": "Hiring Needed",
                    "value": f"{hiring_needed} Openings",
                    "change": "Based on role deficits",
                    "status": "warning" if hiring_needed > 0 else "good",
                    "detail": "Priority hiring queue",
                    "color": "yellow"
                }
            ],
            "capacityChart": capacityChart,
            "projectHealth": projectHealth,
            "availabilityTimeline": availabilityTimeline,
            "pipelineDeals": pipelineDeals,
            "recentActivity": recentActivity,
            "aiActions": aiActions
        }


def MathRound(val: float) -> int:
    """Helper to round float values to nearest int."""
    return int(round(val))

def employees_dict_lookup(db: Session, employee_id: str) -> Employee:
    """Retrieves an employee record by ID."""
    return db.query(Employee).filter(Employee.employee_id == employee_id, Employee.is_active_version == 1).first()
