import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Enable absolute path imports for the backend directory
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.session import SessionLocal
from backend.recommendation.schemas import RecommendationRequest
from backend.recommendation.recommendation_service import RecommendationService
from backend.recommendation.benchmark import RecommendationBenchmarker

def test_strategies_execution():
    """Asserts that each recommendation strategy executes successfully."""
    db = SessionLocal()
    try:
        service = RecommendationService(db)
        
        # We will test hybrid_v1, semantic_only, historical_only, availability_only, competency_only
        strategies = ["hybrid_v1", "semantic_only", "historical_only", "availability_only", "competency_only"]
        
        for strat in strategies:
            req = RecommendationRequest(
                project_id="CLIENT_101_005",
                required_skills=["Python", "SQL"],
                project_type="AI",
                required_competencies=["Communication Skills", "Stakeholder Management"],
                project_start_date="2026-08-01",
                top_n=5,
                strategy=strat
            )
            
            res = service.recommend_resources(req)
            assert res is not None
            assert isinstance(res.explanation, str)
            
            if res.recommendations:
                # Assert fields
                for r in res.recommendations:
                    assert r.employee_id is not None
                    assert r.final_score >= 0.0 and r.final_score <= 100.0
                    assert r.strategy_scores is not None
                    assert "rule_based_v1" in r.strategy_scores
                    assert "semantic_only" in r.strategy_scores
                    assert r.confidence in ["High", "Medium", "Low"]
                
                # Check sorting order by score
                scores = [rec.final_score for rec in res.recommendations]
                assert scores == sorted(scores, reverse=True)
                
        print("✔ Strategy tests execution completed successfully.")
    finally:
        db.close()

def test_diversity_filtering():
    """Asserts that diversity engine limits recommendations per department and manager."""
    db = SessionLocal()
    try:
        service = RecommendationService(db)
        
        # Request top_n=20 to capture potential duplicates
        req = RecommendationRequest(
            project_id="CLIENT_101_005",
            required_skills=["Python"],
            project_type="AI",
            project_start_date="2026-08-01",
            top_n=20,
            strategy="hybrid_v1"
        )
        
        res = service.recommend_resources(req)
        assert res is not None
        
        if res.recommendations:
            dept_counts = {}
            for r in res.recommendations:
                dept = r.department_name.lower().strip()
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
                
            # Verify no department has more than the max limit of 2 (configured in config.yaml)
            for dept, count in dept_counts.items():
                if dept != "n/a":
                    assert count <= 2, f"Department '{dept}' exceeded capping limit of 2 (count={count})"
                    
        print("✔ Diversity engine constraints verified successfully.")
    finally:
        db.close()

def test_recommendation_benchmarking():
    """Asserts that the benchmarker executes and reports comparison metrics."""
    db = SessionLocal()
    try:
        benchmarker = RecommendationBenchmarker(db)
        
        req = RecommendationRequest(
            project_id="CLIENT_101_005",
            required_skills=["Python", "SQL"],
            project_type="AI",
            project_start_date="2026-08-01",
            top_n=3,
            strategy="hybrid_v1"
        )
        
        res = benchmarker.run_benchmark(req)
        assert res is not None
        assert "benchmark_results" in res
        assert "evaluation_metrics" in res
        assert res["processing_time_ms"] >= 0.0
        
        # Verify that all 6 strategies are included in results
        expected_strats = [
            "rule_based_v1", "semantic_only", "historical_only",
            "availability_only", "competency_only", "hybrid_v1"
        ]
        
        for strat in expected_strats:
            assert strat in res["benchmark_results"]
            assert strat in res["evaluation_metrics"]
            metrics = res["evaluation_metrics"][strat]
            if "error" not in metrics:
                assert "precision_at_5" in metrics
                assert "mrr" in metrics
                
        print("✔ Recommendation Benchmarking test passed successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    test_strategies_execution()
    test_diversity_filtering()
    test_recommendation_benchmarking()
