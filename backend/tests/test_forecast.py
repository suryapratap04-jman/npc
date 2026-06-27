import os
import sys
from pathlib import Path
from datetime import date, timedelta

# Enable absolute path imports for the backend directory
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.session import SessionLocal
from backend.forecast.service import ForecastService
from backend.forecast.schemas import NewProjectDemandRequest
from backend.forecast.demand_feature_builder import map_employee_to_role

def test_role_mapping_heuristics():
    """Verifies the rule-based mapping rules for various job titles and skill configurations."""
    # 1. Test Architect matching
    role1 = map_employee_to_role("EMP001", "Technical Solutions Architect", ["python"], [])
    assert role1 == "Architect"

    # 2. Test Non-Delivery matching
    role2 = map_employee_to_role("EMP002", "Senior HRBP", ["communication"], [])
    assert role2 == "Non-Delivery"

    # 3. Test Data Scientist matching
    role3 = map_employee_to_role("EMP003", "Software Engineer", ["python", "machine learning", "neural networks"], ["Data Science & AI"])
    assert role3 == "Data Scientist"

    # 4. Test Data Engineer matching
    role4 = map_employee_to_role("EMP004", "Software Engineer", ["sql", "databricks", "data pipeline"], ["Data Engineering"])
    assert role4 == "Data Engineer"

    # 5. Test DevOps matching
    role5 = map_employee_to_role("EMP005", "IT support", ["kubernetes", "docker", "devops"], ["TechOps & Automation"])
    assert role5 == "DevOps"

    # 6. Test Frontend matching
    role6 = map_employee_to_role("EMP006", "Software Engineer", ["react", "javascript", "frontend"], ["Full Stack"])
    assert role6 == "Frontend Engineer"

    # 7. Test QA matching
    role7 = map_employee_to_role("EMP007", "Software Engineer", ["automation infrastructure", "pytest"], ["Full Stack"])
    assert role7 == "QA"

    print("[OK] Role mapping heuristics tests passed.")

def test_capacity_horizons():
    """Asserts that capacity engine calculates available headcount projections across horizons."""
    db = SessionLocal()
    try:
        service = ForecastService(db)
        status = service.get_capacity_status()
        
        assert status is not None
        assert status.capacity_projections.available_now >= 0
        assert status.capacity_projections.available_30_days >= 0
        assert status.capacity_projections.available_60_days >= 0
        assert status.capacity_projections.available_90_days >= 0
        
        # Verify role details are populated
        assert "backend" in status.details
        assert "available_now" in status.details["backend"]
        
        print("[OK] Capacity horizons calculation test passed.")
    finally:
        db.close()

def test_new_project_forecast():
    """Asserts that new project forecasting successfully returns team recomms, FTE, cost, and recommendations."""
    db = SessionLocal()
    try:
        req = NewProjectDemandRequest(
            project_type="AI",
            expected_duration_months=8,
            required_skills=["Python", "LLM", "FastAPI"],
            expected_start_date="2026-08-15",
            expected_team_size=None
        )
        service = ForecastService(db)
        res = service.forecast_new_project(req)
        
        assert res is not None
        assert res.project_type == "AI"
        assert res.expected_duration == 8
        assert res.estimated_fte > 0.0
        assert res.estimated_cost > 0.0
        assert "backend" in res.team_recommendation
        assert res.confidence in ["High", "Medium", "Low"]
        assert len(res.explanation) > 50
        
        # Verify recommendations are structured
        assert isinstance(res.recommendation.redeploy, list)
        assert isinstance(res.recommendation.hire, list)
        
        print("[OK] New project demand forecasting test passed.")
    finally:
        db.close()

def test_six_month_pipeline_forecast():
    """Asserts rolling six month operational metrics projection is computed correctly."""
    db = SessionLocal()
    try:
        service = ForecastService(db)
        res = service.get_six_month_forecast()
        
        assert res is not None
        assert len(res.monthly_projections) == 6
        assert res.average_projected_utilization >= 0.0
        
        # Verify month projection keys
        first_month = res.monthly_projections[0]
        assert first_month.month is not None
        assert first_month.expected_project_volume >= 0
        assert first_month.headcount_demand >= 0.0
        assert first_month.utilization_percentage >= 0.0
        assert "backend" in first_month.skill_demand
        
        print("[OK] Six-month pipeline forecasting test passed.")
    finally:
        db.close()

def test_hiring_and_redeployment_endpoints():
    """Asserts sub-service API helper results are structured properly."""
    db = SessionLocal()
    try:
        req = NewProjectDemandRequest(
            project_type="Data Engineering",
            expected_duration_months=6,
            required_skills=["Spark", "Snowflake", "SQL"],
            expected_start_date="2026-08-15"
        )
        service = ForecastService(db)
        
        # Test Hiring Need Endpoint
        hiring_res = service.get_hiring_needs(req)
        assert hiring_res is not None
        assert isinstance(hiring_res.hiring_needs, list)
        assert hiring_res.summary is not None
        
        # Test Redeployment Endpoint
        redeploy_res = service.get_redeployment_options(req)
        assert redeploy_res is not None
        assert isinstance(redeploy_res.redeployment_options, list)
        assert redeploy_res.summary is not None
        
        print("[OK] Hiring and redeployment endpoint tests passed.")
    finally:
        db.close()

def test_metrics_evaluation_logging():
    """Asserts that running the forecasting pipeline logs evaluation indicators to forecast_metrics.csv."""
    project_root = Path(__file__).parent.parent.parent
    csv_path = project_root / "experiments" / "forecast_metrics.csv"
    
    if csv_path.exists():
        os.remove(csv_path)
        
    db = SessionLocal()
    try:
        req = NewProjectDemandRequest(
            project_type="AI",
            expected_duration_months=6,
            required_skills=["Python", "FastAPI"],
            expected_start_date="2026-08-15"
        )
        service = ForecastService(db)
        
        # Trigger forecast to write metrics
        service.forecast_new_project(req)
        
        assert csv_path.exists(), "experiments/forecast_metrics.csv was not created."
        with open(csv_path, mode="r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) >= 2, "experiments/forecast_metrics.csv is empty."
            
        print("[OK] CSV forecast metrics logging test passed.")
    finally:
        db.close()

if __name__ == "__main__":
    test_role_mapping_heuristics()
    test_capacity_horizons()
    test_new_project_forecast()
    test_six_month_pipeline_forecast()
    test_hiring_and_redeployment_endpoints()
    test_metrics_evaluation_logging()
