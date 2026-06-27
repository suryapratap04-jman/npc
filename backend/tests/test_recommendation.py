import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session

# Enable absolute path imports for the backend directory
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.session import SessionLocal
from backend.recommendation.utils import load_recommendation_config
from backend.recommendation.schemas import RecommendationRequest
from backend.recommendation.recommendation_service import RecommendationService

def test_load_config():
    """Asserts that configuration YAML is successfully parsed."""
    config = load_recommendation_config()
    assert config is not None
    assert "weights" in config
    assert "thresholds" in config
    assert "normalization" in config
    
    # Assert weights sum to exactly 1.0
    weights = config["weights"]
    total = sum(weights.values())
    assert abs(total - 1.0) < 1e-5

def test_recommendation_service():
    """Asserts that recommendation service compiles candidate scoring and ranking correctly."""
    db = SessionLocal()
    try:
        service = RecommendationService(db)
        
        # Build request for verification
        req = RecommendationRequest(
            project_id="CLIENT_101_005",
            required_skills=["Python", "SQL"],
            project_type="AI",
            required_competencies=["Communication Skills", "Stakeholder Management"],
            project_start_date="2026-08-01",
            top_n=5
        )
        
        res = service.recommend_resources(req)
        
        assert res is not None
        assert res.processing_time_ms >= 0.0
        assert res.model_version == "v1"
        assert isinstance(res.explanation, str)
        
        # If active candidates exist and are returned
        if res.recommendations:
            # Check length is capped at top_n
            assert len(res.recommendations) <= 5
            
            # Check descending score sorting
            scores = [r.final_score for r in res.recommendations]
            assert scores == sorted(scores, reverse=True)
            
            # Check rank assignment matches position
            for idx, r in enumerate(res.recommendations):
                assert r.rank == idx + 1
                assert r.employee_id is not None
                assert r.final_score >= 0.0 and r.final_score <= 100.0
                assert "skill_match" in r.category_scores
                assert "availability" in r.category_scores
                
            print(f"✔ Recommendations test passed. Returned {len(res.recommendations)} candidates. Top match: {res.recommendations[0].employee_id}")
        else:
            print("✔ Recommendations test passed. Pool is empty (as expected if DB contains no candidates matching current constraints).")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_load_config()
    test_recommendation_service()
