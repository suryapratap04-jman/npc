import sys
from pathlib import Path

# Enable absolute path imports for the backend directory
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.session import SessionLocal
from backend.dashboard.service import DashboardService


def test_get_dashboard_overview():
    """Asserts that DashboardService correctly computes metrics and returns the structured composed overview."""
    db = SessionLocal()
    try:
        service = DashboardService(db)
        res = service.get_dashboard_overview()
        
        # Verify presence of all expected composed fields
        assert res is not None
        assert "aiSummary" in res
        assert "kpiCards" in res
        assert "capacityChart" in res
        assert "projectHealth" in res
        assert "availabilityTimeline" in res
        assert "pipelineDeals" in res
        assert "recentActivity" in res
        assert "aiActions" in res
        
        # 1. KPI Cards Assertions
        kpi_cards = res["kpiCards"]
        assert len(kpi_cards) == 4
        
        # Card 1: Utilization
        util_card = next(c for c in kpi_cards if c["id"] == "utilization")
        assert util_card["title"] == "Current Utilization"
        assert "%" in util_card["value"]
        util_val = float(util_card["value"].replace("%", ""))
        assert 0.0 <= util_val <= 100.0
        assert util_card["color"] == "blue"
        
        # Card 2: Risks
        risk_card = next(c for c in kpi_cards if c["id"] == "risks")
        assert risk_card["title"] == "Projects At Risk"
        assert "Critical" in risk_card["value"]
        assert risk_card["color"] == "red"
        
        # Card 3: Bench
        bench_card = next(c for c in kpi_cards if c["id"] == "bench")
        assert bench_card["title"] == "Available Employees"
        assert "Benched" in bench_card["value"]
        assert bench_card["color"] == "green"
        
        # Card 4: Hiring Needed
        hiring_card = next(c for c in kpi_cards if c["id"] == "hiring")
        assert hiring_card["title"] == "Hiring Needed"
        assert "Openings" in hiring_card["value"]
        hiring_val = int(hiring_card["value"].split()[0])
        assert hiring_val >= 0
        assert hiring_card["color"] == "yellow"
        
        # 2. Capacity Chart Assertions
        capacity_chart = res["capacityChart"]
        assert isinstance(capacity_chart, list)
        if capacity_chart:
            first_point = capacity_chart[0]
            assert "month" in first_point
            assert "Supply" in first_point
            assert "Demand" in first_point
            assert "Pipeline" in first_point
            assert first_point["Supply"] >= 0
            
        # 3. Project Health Assertions
        project_health = res["projectHealth"]
        assert isinstance(project_health, list)
        if project_health:
            first_proj = project_health[0]
            assert "id" in first_proj
            assert "name" in first_proj
            assert "status" in first_proj
            assert "PM" in first_proj
            assert "staffCount" in first_proj
            assert first_proj["status"] in ["Green", "Amber", "Red"]
            
        # 4. Availability Timeline Assertions
        timeline = res["availabilityTimeline"]
        assert isinstance(timeline, list)
        assert len(timeline) <= 5
        if timeline:
            first_item = timeline[0]
            assert "id" in first_item
            assert "skill" in first_item
            assert "project" in first_item
            assert "daysRemaining" in first_item
            assert first_item["daysRemaining"] >= 0
            
        # 5. AI Summary Assertion
        assert isinstance(res["aiSummary"], str)
        assert len(res["aiSummary"]) > 0
        
        print("✔ Dashboard overview service integration test passed.")
    finally:
        db.close()
