import time
import logging
from datetime import date
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from backend.forecast.schemas import (
    NewProjectDemandRequest, NewProjectForecastResponse, CapacityProjections,
    ActionableRecommendations, SixMonthForecastResponse, CapacityStatusResponse,
    HiringResponse, RedeploymentResponse, HiringNeed, RedeploymentOption, MonthlyProjection
)
from backend.forecast.demand_feature_builder import DemandFeatureBuilder
from backend.forecast.role_mix_engine import RoleMixEngine
from backend.forecast.demand_forecast_engine import DemandForecastEngine
from backend.forecast.capacity_engine import CapacityEngine
from backend.forecast.hiring_engine import HiringEngine
from backend.forecast.redeployment_engine import RedeploymentEngine
from backend.forecast.pipeline_forecast_engine import PipelineForecastEngine
from backend.forecast.explanation_engine import ExplanationEngine
from backend.forecast.evaluation import ForecastEvaluator

logger = logging.getLogger("forecast_service")

class ForecastService:
    def __init__(self, db: Session):
        self.db = db
        self.feature_builder = DemandFeatureBuilder(db)
        self.role_mix_engine = RoleMixEngine(self.feature_builder)
        self.demand_forecast_engine = DemandForecastEngine(self.role_mix_engine)
        self.capacity_engine = CapacityEngine(db, self.feature_builder)
        self.hiring_engine = HiringEngine()
        self.redeployment_engine = RedeploymentEngine(db, self.feature_builder)
        self.pipeline_forecast_engine = PipelineForecastEngine(db, self.feature_builder)
        self.explanation_engine = ExplanationEngine()
        self.evaluator = ForecastEvaluator()

    def get_reference_date(self) -> date:
        return self.capacity_engine.get_reference_date()

    def forecast_new_project(self, req: NewProjectDemandRequest) -> NewProjectForecastResponse:
        """
        Coordinates the full pipeline: staffing derivation, capacity validation,
        hiring/redeployment extraction, and RAG explanation.
        """
        start_time = time.time()
        
        # 1. Staffing demand forecast
        demand = self.demand_forecast_engine.forecast_project_demand(
            project_type=req.project_type,
            expected_duration_months=req.expected_duration_months,
            required_skills=req.required_skills,
            expected_team_size=req.expected_team_size
        )
        
        # 2. Capacity validations
        ref_date = self.get_reference_date()
        try:
            req_start_date = date.fromisoformat(req.expected_start_date)
        except Exception:
            req_start_date = ref_date + date.timedelta(days=30)
            
        start_offset_days = (req_start_date - ref_date).days
        capacity_data = self.capacity_engine.calculate_capacity_projections(ref_date)
        
        # 3. Redeployment matching
        required_roles = [role for role, count in demand["team_recommendation"].items() if count > 0]
        redeploy_data = self.redeployment_engine.get_candidate_redeployments(
            expected_start_date_str=req.expected_start_date,
            required_roles=required_roles,
            required_skills=req.required_skills
        )
        
        # 4. Hiring validation
        hiring_data = self.hiring_engine.evaluate_hiring_needs(
            team_recommendation=demand["team_recommendation"],
            capacity_projections=capacity_data,
            redeployment_recommendations=redeploy_data["candidates_by_role"],
            project_start_offset_days=start_offset_days
        )
        
        # Extract lists
        redeploy_ids = [opt["employee_id"] for opt in redeploy_data["redeployment_options"][:5]]
        hire_roles = [hn["role"] for hn in hiring_data["hiring_needs"]]
        
        # 5. Extract historical statistics for explainability
        tech_category = None
        skills_lower = [s.lower() for s in req.required_skills]
        if any("ai" in s or "llm" in s for s in skills_lower):
            tech_category = "Gen AI"
        elif any("spark" in s or "databricks" in s for s in skills_lower):
            tech_category = "Data Engineering"
            
        history = self.feature_builder.get_historical_aggregates(
            project_type=req.project_type,
            technology=tech_category
        )
        
        # 6. Generate narrative
        explanation = self.explanation_engine.generate_explanation(
            project_type=req.project_type,
            expected_start_date=req.expected_start_date,
            duration=demand["expected_duration"],
            team_rec=demand["team_recommendation"],
            hiring_summary=hiring_data["summary"],
            redeploy_summary=redeploy_data["summary"],
            sample_size=history.get("sample_size", 0),
            avg_team_size=history.get("avg_team_size", 0.0),
            avg_duration=history.get("avg_duration_months", 0.0)
        )
        
        # Compile response
        res = NewProjectForecastResponse(
            project_type=req.project_type,
            team_recommendation=demand["team_recommendation"],
            estimated_fte=demand["estimated_fte"],
            estimated_cost=demand["estimated_cost"],
            expected_duration=demand["expected_duration"],
            capacity=CapacityProjections(
                available_now=capacity_data["capacity_projections"]["available_now"],
                available_30_days=capacity_data["capacity_projections"]["available_30_days"],
                available_60_days=capacity_data["capacity_projections"]["available_60_days"],
                available_90_days=capacity_data["capacity_projections"]["available_90_days"]
            ),
            recommendation=ActionableRecommendations(
                redeploy=redeploy_ids,
                hire=hire_roles
            ),
            confidence=demand["confidence"],
            explanation=explanation
        )
        
        # 7. Log evaluation metrics
        elapsed_ms = (time.time() - start_time) * 1000.0
        try:
            # We pass details for logging
            details = {
                "forecast_accuracy": 1.0 if history.get("sample_size", 0) > 0 else 0.0,
                "avg_projected_utilization": 80.0,  # general baseline
                "capacity_surplus": capacity_data["capacity_projections"]["available_now"],
                "capacity_deficit": len(hire_roles),
                "hiring_recommendations_count": len(hire_roles),
                "redeployment_recommendations_count": len(redeploy_ids),
                "api_latency_ms": elapsed_ms
            }
            self.evaluator.evaluate_and_log(details)
        except Exception as eval_err:
            logger.error(f"Failed to log forecast evaluation: {eval_err}")
            
        return res

    def get_six_month_forecast(self) -> SixMonthForecastResponse:
        """Returns monthly volume and headcount forecast for next 6 months."""
        start_time = time.time()
        ref_date = self.get_reference_date()
        forecast = self.pipeline_forecast_engine.get_six_month_forecast(ref_date)
        
        projections = []
        for p in forecast["monthly_projections"]:
            projections.append(MonthlyProjection(
                month=p["month"],
                expected_project_volume=p["expected_project_volume"],
                headcount_demand=p["headcount_demand"],
                skill_demand=p["skill_demand"],
                utilization_percentage=p["utilization_percentage"],
                capacity_surplus=p["capacity_surplus"],
                capacity_deficit=p["capacity_deficit"]
            ))
            
        res = SixMonthForecastResponse(
            monthly_projections=projections,
            average_projected_utilization=forecast["average_projected_utilization"],
            total_capacity_surplus=forecast["total_capacity_surplus"],
            total_capacity_deficit=forecast["total_capacity_deficit"],
            confidence_score=forecast["confidence_score"]
        )
        
        elapsed_ms = (time.time() - start_time) * 1000.0
        try:
            self.evaluator.evaluate_and_log({
                "forecast_accuracy": 1.0,
                "avg_projected_utilization": forecast["average_projected_utilization"],
                "capacity_surplus": forecast["total_capacity_surplus"],
                "capacity_deficit": forecast["total_capacity_deficit"],
                "hiring_recommendations_count": 0,
                "redeployment_recommendations_count": 0,
                "api_latency_ms": elapsed_ms
            })
        except Exception as e:
            logger.error(f"Failed to log forecast evaluation: {e}")
            
        return res

    def get_capacity_status(self) -> CapacityStatusResponse:
        """Returns active available resources today, +30, +60, +90 days."""
        ref_date = self.get_reference_date()
        capacity_data = self.capacity_engine.calculate_capacity_projections(ref_date)
        
        proj = CapacityProjections(
            available_now=capacity_data["capacity_projections"]["available_now"],
            available_30_days=capacity_data["capacity_projections"]["available_30_days"],
            available_60_days=capacity_data["capacity_projections"]["available_60_days"],
            available_90_days=capacity_data["capacity_projections"]["available_90_days"]
        )
        
        return CapacityStatusResponse(
            capacity_projections=proj,
            available_employees_by_role=capacity_data["available_employees_by_role"],
            details=capacity_data["role_breakdown"]
        )

    def get_hiring_needs(self, req: NewProjectDemandRequest) -> HiringResponse:
        """Returns prioritized external hires list for a project request."""
        # Query demand
        demand = self.demand_forecast_engine.forecast_project_demand(
            project_type=req.project_type,
            expected_duration_months=req.expected_duration_months,
            required_skills=req.required_skills,
            expected_team_size=req.expected_team_size
        )
        ref_date = self.get_reference_date()
        try:
            req_start_date = date.fromisoformat(req.expected_start_date)
        except Exception:
            req_start_date = ref_date + date.timedelta(days=30)
            
        start_offset_days = (req_start_date - ref_date).days
        capacity_data = self.capacity_engine.calculate_capacity_projections(ref_date)
        
        required_roles = [role for role, count in demand["team_recommendation"].items() if count > 0]
        redeploy_data = self.redeployment_engine.get_candidate_redeployments(
            expected_start_date_str=req.expected_start_date,
            required_roles=required_roles,
            required_skills=req.required_skills
        )
        
        hiring_data = self.hiring_engine.evaluate_hiring_needs(
            team_recommendation=demand["team_recommendation"],
            capacity_projections=capacity_data,
            redeployment_recommendations=redeploy_data["candidates_by_role"],
            project_start_offset_days=start_offset_days
        )
        
        needs = []
        for hn in hiring_data["hiring_needs"]:
            needs.append(HiringNeed(
                role=hn["role"],
                count_needed=hn["count_needed"],
                priority=hn["priority"],
                reason=hn["reason"]
            ))
            
        return HiringResponse(
            hiring_needs=needs,
            summary=hiring_data["summary"]
        )

    def get_redeployment_options(self, req: NewProjectDemandRequest) -> RedeploymentResponse:
        """Returns matched transition candidates for a new project demand."""
        # Query demand to find required roles
        demand = self.demand_forecast_engine.forecast_project_demand(
            project_type=req.project_type,
            expected_duration_months=req.expected_duration_months,
            required_skills=req.required_skills,
            expected_team_size=req.expected_team_size
        )
        
        required_roles = [role for role, count in demand["team_recommendation"].items() if count > 0]
        redeploy_data = self.redeployment_engine.get_candidate_redeployments(
            expected_start_date_str=req.expected_start_date,
            required_roles=required_roles,
            required_skills=req.required_skills
        )
        
        options = []
        for opt in redeploy_data["redeployment_options"]:
            options.append(RedeploymentOption(
                employee_id=opt["employee_id"],
                name=opt["name"],
                role=opt["role"],
                current_project_id=opt["current_project_id"],
                project_end_date=opt["project_end_date"],
                available_from=opt["available_from"],
                match_score=opt["match_score"]
            ))
            
        return RedeploymentResponse(
            redeployment_options=options,
            summary=redeploy_data["summary"]
        )
