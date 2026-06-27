import time
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.recommendation.schemas import RecommendationRequest, CandidateRecommendation

logger = logging.getLogger("benchmark")

class RecommendationBenchmarker:
    def __init__(self, db: Session):
        self.db = db

    def run_benchmark(self, request: RecommendationRequest) -> Dict[str, Any]:
        """
        Executes multiple recommendation strategies on the same request for comparison.
        Returns a dictionary containing benchmark results and evaluation metrics.
        """
        from backend.recommendation.recommendation_service import RecommendationService
        
        strategies_to_test = [
            "rule_based_v1",
            "semantic_only",
            "historical_only",
            "availability_only",
            "competency_only",
            "hybrid_v1"
        ]

        benchmark_results = {}
        evaluation_metrics = {}
        start_time = time.time()

        for strat in strategies_to_test:
            strat_start = time.time()
            try:
                strat_req = RecommendationRequest(
                    project_id=request.project_id,
                    required_skills=request.required_skills,
                    project_type=request.project_type,
                    required_competencies=request.required_competencies,
                    project_start_date=request.project_start_date,
                    top_n=request.top_n,
                    strategy=strat
                )
                
                service = RecommendationService(self.db)
                res = service.recommend_resources(strat_req)
                
                benchmark_results[strat] = res.recommendations
                
                # Perform offline evaluation for metrics comparison
                elapsed_strat_ms = (time.time() - strat_start) * 1000.0
                metrics = service.evaluator.evaluate(
                    project_id=request.project_id,
                    recommendations=[r.model_dump() for r in res.recommendations],
                    elapsed_time_ms=elapsed_strat_ms
                )
                evaluation_metrics[strat] = metrics
                
            except Exception as e:
                logger.error(f"Failed to benchmark strategy {strat}: {e}")
                benchmark_results[strat] = []
                evaluation_metrics[strat] = {"error": str(e)}

        total_elapsed_ms = (time.time() - start_time) * 1000.0

        return {
            "benchmark_results": benchmark_results,
            "evaluation_metrics": evaluation_metrics,
            "processing_time_ms": round(total_elapsed_ms, 2)
        }
