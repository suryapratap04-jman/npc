import logging
import math
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database.models import Project, Allocation, Employee, Pipeline
from backend.forecast.demand_feature_builder import DemandFeatureBuilder

logger = logging.getLogger("pipeline_forecast_engine")

class BaseForecastModel:
    """Interface for forecasting models to support swapping algorithms."""
    def fit(self, history: List[float]):
        raise NotImplementedError()
        
    def predict(self, steps: int) -> List[float]:
        raise NotImplementedError()

class RollingAverageModel(BaseForecastModel):
    def __init__(self, window: int = 3):
        self.window = window
        self.history = []
        
    def fit(self, history: List[float]):
        self.history = history
        
    def predict(self, steps: int) -> List[float]:
        if not self.history:
            return [0.0] * steps
        predictions = []
        hist = list(self.history)
        for _ in range(steps):
            window_vals = hist[-self.window:] if len(hist) >= self.window else hist
            val = sum(window_vals) / len(window_vals) if window_vals else 0.0
            predictions.append(val)
            hist.append(val)
        return predictions

class ExponentialSmoothingModel(BaseForecastModel):
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.history = []
        
    def fit(self, history: List[float]):
        self.history = history
        
    def predict(self, steps: int) -> List[float]:
        if not self.history:
            return [0.0] * steps
        
        # Simple Exponential Smoothing (SES)
        level = self.history[0]
        for val in self.history[1:]:
            level = self.alpha * val + (1 - self.alpha) * level
            
        return [level] * steps

class TrendExtrapolationModel(BaseForecastModel):
    def __init__(self):
        self.history = []
        
    def fit(self, history: List[float]):
        self.history = history
        
    def predict(self, steps: int) -> List[float]:
        n = len(self.history)
        if n < 2:
            val = self.history[0] if n == 1 else 0.0
            return [val] * steps
            
        # Compute simple linear regression y = mx + c
        sum_x = sum(range(n))
        sum_y = sum(self.history)
        sum_xx = sum(i * i for i in range(n))
        sum_xy = sum(i * val for i, val in enumerate(self.history))
        
        denominator = (n * sum_xx - sum_x * sum_x)
        if denominator == 0:
            m = 0.0
            c = sum_y / n
        else:
            m = (n * sum_xy - sum_x * sum_y) / denominator
            c = (sum_y - m * sum_x) / n
            
        predictions = []
        for i in range(steps):
            x = n + i
            pred = max(0.0, m * x + c)
            predictions.append(pred)
        return predictions

class PipelineForecastEngine:
    def __init__(self, db: Session, feature_builder: DemandFeatureBuilder, model: Optional[BaseForecastModel] = None):
        self.db = db
        self.feature_builder = feature_builder
        self.model = model or TrendExtrapolationModel() # default to trend extrapolation

    def get_six_month_forecast(self, reference_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Reconstructs the past 12 months of operations and forecasts monthly metrics 6 months forward,
        integrating upcoming pipeline opportunities.
        """
        if not reference_date:
            reference_date = date(2026, 6, 27)  # standard context date
            
        emp_roles = self.feature_builder.load_employee_roles()
        
        # 1. Generate date list for past 12 months (e.g. July 2025 - June 2026)
        months_history: List[Tuple[date, date, str]] = []
        current_iter = reference_date - timedelta(days=365)
        # align to start of month
        current_iter = date(current_iter.year, current_iter.month, 1)
        
        for _ in range(12):
            # start of month
            m_start = current_iter
            # end of month
            if m_start.month == 12:
                m_end = date(m_start.year, 12, 31)
                next_month = date(m_start.year + 1, 1, 1)
            else:
                m_end = date(m_start.year, m_start.month + 1, 1) - timedelta(days=1)
                next_month = date(m_start.year, m_start.month + 1, 1)
                
            months_history.append((m_start, m_end, m_start.strftime("%Y-%m")))
            current_iter = next_month

        # Query databases
        allocations = self.db.query(Allocation).filter(Allocation.is_active_version == 1, Allocation.is_allocation_active == 1).all()
        employees = self.db.query(Employee).filter(Employee.is_active_version == 1, Employee.account_status == 1).all()
        pipeline_deals = self.db.query(Pipeline).all()
        
        # 2. Compile historical aggregates
        history_volume = []
        history_headcount = []
        history_utilization = []
        
        # Track historical role distributions
        role_distributions = {r: [] for r in ["architect", "consultant", "backend", "frontend", "data_engineer", "data_scientist", "qa", "devops"]}
        
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
        
        for m_start, m_end, label in months_history:
            # Active projects in this month
            active_projects: Set[str] = set()
            active_allocs_count = 0.0
            
            monthly_role_counts = {r: 0 for r in role_distributions}
            
            # Count employees active in this month
            active_employee_pool = 0
            for emp in employees:
                # joined before end of month and not resigned before start of month
                joined = emp.date_of_join or date(2020, 1, 1)
                resigned = emp.date_of_resignation
                if joined <= m_end:
                    if not resigned or resigned >= m_start:
                        active_employee_pool += 1
                        
            active_employee_pool = max(1, active_employee_pool)
            
            for a in allocations:
                a_start = a.allocated_start_date or date(2020, 1, 1)
                a_end = a.allocated_end_date or date(2099, 12, 31)
                
                # Check overlap
                if a_start <= m_end and a_end >= m_start:
                    if a.project_id:
                        active_projects.add(a.project_id)
                    pct = (a.allocation_by_percentage or 100.0) / 100.0
                    active_allocs_count += pct
                    
                    if a.employee_id:
                        role = emp_roles.get(a.employee_id)
                        role_key = role_key_map.get(role)
                        if role_key:
                            monthly_role_counts[role_key] += 1
                            
            history_volume.append(float(len(active_projects)))
            history_headcount.append(active_allocs_count)
            
            util = (active_allocs_count / active_employee_pool) * 100.0
            history_utilization.append(min(100.0, util))
            
            for r in role_distributions:
                role_distributions[r].append(monthly_role_counts[r])

        # 3. Fit models and predict next 6 months
        # Model for project volume
        self.model.fit(history_volume)
        pred_volume = self.model.predict(6)
        
        # Model for headcount
        self.model.fit(history_headcount)
        pred_headcount = self.model.predict(6)
        
        # Model for utilization
        self.model.fit(history_utilization)
        pred_utilization = self.model.predict(6)

        # 4. Process pipeline additions
        # Pipeline table lists pipeline requests with likely_start_date and skillset / requested resources
        pipeline_month_additions: Dict[str, List[Dict[str, Any]]] = {}
        for deal in pipeline_deals:
            if not deal.likely_start_date:
                continue
                
            p_start = deal.likely_start_date
            if p_start <= reference_date:
                continue  # already started or stale
                
            # Parse number of weeks, default to 12 weeks (3 months)
            duration_months = 3
            try:
                weeks_str = str(deal.number_of_weeks or "")
                if weeks_str.isdigit():
                    duration_months = max(1, round(int(weeks_str) / 4.0))
            except Exception:
                pass
                
            # Parse headcount from resource description (e.g. "1 Architect, 2 Backend") or use default
            headcount_addition = 1.0
            try:
                req_res = str(deal.resources_requested or "")
                # A simple count of numeric digits or comma splits
                if "," in req_res:
                    headcount_addition = float(len(req_res.split(",")))
                elif req_res and req_res[0].isdigit():
                    headcount_addition = float(req_res[0])
            except Exception:
                pass
                
            # Distribute pipeline additions to active months
            for i in range(duration_months):
                future_date = p_start + timedelta(days=i*30)
                # align to start of month
                m_label = future_date.strftime("%Y-%m")
                pipeline_month_additions.setdefault(m_label, []).append({
                    "headcount": headcount_addition
                })

        # 5. Build 6-Month projections
        proj_months: List[Tuple[date, date, str]] = []
        current_iter = reference_date
        # start of next month
        if current_iter.month == 12:
            current_iter = date(current_iter.year + 1, 1, 1)
        else:
            current_iter = date(current_iter.year, current_iter.month + 1, 1)
            
        for _ in range(6):
            m_start = current_iter
            if m_start.month == 12:
                m_end = date(m_start.year, 12, 31)
                next_month = date(m_start.year + 1, 1, 1)
            else:
                m_end = date(m_start.year, m_start.month + 1, 1) - timedelta(days=1)
                next_month = date(m_start.year, m_start.month + 1, 1)
                
            proj_months.append((m_start, m_end, m_start.strftime("%Y-%m")))
            current_iter = next_month
            
        total_capacity = len(employees) # total active employee pool size
        projections = []
        
        for idx, (m_start, m_end, label) in enumerate(proj_months):
            vol = round(pred_volume[idx])
            hc = pred_headcount[idx]
            util = pred_utilization[idx]
            
            # Apply pipeline overlays
            pipe_deals_active = pipeline_month_additions.get(label, [])
            pipe_vol_add = len(pipe_deals_active)
            pipe_hc_add = sum(d["headcount"] for d in pipe_deals_active)
            
            vol += pipe_vol_add
            hc += pipe_hc_add
            
            # Adjust utilization to reflect pipeline additions
            util_adjusted = min(100.0, max(0.0, util + (pipe_hc_add / max(1, total_capacity)) * 100.0))
            
            # Surplus vs Deficit
            surplus = max(0, round(total_capacity - hc))
            deficit = max(0, round(hc - total_capacity))
            
            # Forecast role breakdown based on average historical role proportions
            avg_distribution = {}
            total_historical_slots = sum(sum(lst) for lst in role_distributions.values())
            for r in role_distributions:
                r_hist_sum = sum(role_distributions[r])
                ratio = r_hist_sum / total_historical_slots if total_historical_slots > 0 else 0.125
                avg_distribution[r] = max(0, round(hc * ratio))
                
            projections.append({
                "month": label,
                "expected_project_volume": int(max(0, vol)),
                "headcount_demand": float(round(max(0.0, hc), 1)),
                "skill_demand": avg_distribution,
                "utilization_percentage": float(round(util_adjusted, 1)),
                "capacity_surplus": int(surplus),
                "capacity_deficit": int(deficit)
            })
            
        avg_projected_util = sum(p["utilization_percentage"] for p in projections) / len(projections)
        total_surplus = sum(p["capacity_surplus"] for p in projections)
        total_deficit = sum(p["capacity_deficit"] for p in projections)
        
        return {
            "monthly_projections": projections,
            "average_projected_utilization": float(round(avg_projected_util, 1)),
            "total_capacity_surplus": int(total_surplus),
            "total_capacity_deficit": int(total_deficit),
            "confidence_score": "High" if len(history_volume) >= 12 else "Medium"
        }
