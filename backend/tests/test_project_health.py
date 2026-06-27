import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session

# Enable absolute path imports for the backend directory
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.session import SessionLocal
from backend.health.service import ProjectHealthService
from backend.health.schemas import ProjectHealthAnalysisRequest

def test_get_projects_health():
    """Asserts that the engine queries all active projects and compiles health summaries."""
    db = SessionLocal()
    try:
        service = ProjectHealthService(db)
        res = service.get_projects_health()
        assert res is not None
        assert isinstance(res, list)
        
        if res:
            first_proj = res[0]
            assert first_proj.project_id is not None
            assert first_proj.overall_health in ["Green", "Amber", "Red"]
            assert first_proj.risk_score >= 0.0 and first_proj.risk_score <= 100.0
            assert first_proj.risk_level in ["Low", "Medium", "High", "Critical"]
            
        print("✔ Project health summaries test passed.")
    finally:
        db.close()

def test_project_health_detail():
    """Asserts that the diagnostic pipeline computes detailed risk, schedule, utilization, and recovery metrics."""
    db = SessionLocal()
    try:
        service = ProjectHealthService(db)
        
        # Test using CLIENT_201_005 (valid active project)
        project_id = "CLIENT_201_005"
        res = service.get_project_health_detail(project_id)
        assert res is not None
        assert res.project_id == project_id
        assert res.overall_health in ["Green", "Amber", "Red"]
        assert res.risk_score >= 0.0 and res.risk_score <= 100.0
        
        # Schedule asserts
        assert res.schedule.status in ["Green", "Amber", "Red", "NO_COLOR", "NO COLOR"]
        assert res.schedule.delay_days >= 0
        assert res.schedule.planned_duration >= 0
        assert res.schedule.actual_duration >= 0
        
        # Utilization asserts
        assert res.utilization.average >= 0.0
        assert res.utilization.peak >= 0.0
        assert res.utilization.overallocated_count >= 0
        assert res.utilization.idle_capacity_percentage >= 0.0
        
        # Billability asserts
        assert res.billability.percentage >= 0.0 and res.billability.percentage <= 100.0
        assert res.billability.billable_hours >= 0.0
        assert res.billability.shadow_resources_count >= 0
        assert res.billability.cost_recovery_status in ["Good", "Degraded", "Poor"]
        
        # Recommendations & RAG Explanations asserts
        assert len(res.recommended_actions) > 0
        assert isinstance(res.explanation, str)
        
        print("✔ Project health detailed diagnostics test passed.")
    finally:
        db.close()

def test_rampdown_candidates():
    """Asserts that the ramp-down engine correctly identifies projects with idle allocations."""
    db = SessionLocal()
    try:
        service = ProjectHealthService(db)
        res = service.get_rampdown_candidates()
        assert res is not None
        assert isinstance(res, list)
        
        for r in res:
            assert r.project_id is not None
            assert r.is_suitable is True
            assert r.estimated_release_count >= 0
            
        print("✔ Ramp-down candidate evaluation test passed.")
    finally:
        db.close()

def test_utilization_and_billability_stats():
    """Asserts utilization and cost recovery endpoint lists are compiled correctly."""
    db = SessionLocal()
    try:
        service = ProjectHealthService(db)
        
        util_stats = service.get_utilization_stats()
        assert util_stats is not None
        assert isinstance(util_stats, list)
        
        bill_stats = service.get_billability_stats()
        assert bill_stats is not None
        assert isinstance(bill_stats, list)
        
        print("✔ Capacity utilization and billability lists test passed.")
    finally:
        db.close()

def test_experiments_metrics_logging():
    """Asserts that operational metrics are stored in experiments/project_health_metrics.csv."""
    db = SessionLocal()
    try:
        service = ProjectHealthService(db)
        
        # Clear metrics file to assert new write
        project_root = Path(__file__).parent.parent.parent
        csv_path = project_root / "experiments" / "project_health_metrics.csv"
        if csv_path.exists():
            os.remove(csv_path)
            
        # Trigger get_projects_health to log metrics
        service.get_projects_health()
        
        assert csv_path.exists(), "experiments/project_health_metrics.csv was not created."
        with open(csv_path, mode="r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) >= 2, "experiments/project_health_metrics.csv is empty."
            
        print("✔ CSV experiments logging test passed.")
    finally:
        db.close()

if __name__ == "__main__":
    test_get_projects_health()
    test_project_health_detail()
    test_rampdown_candidates()
    test_utilization_and_billability_stats()
    test_experiments_metrics_logging()
