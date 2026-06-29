import time
import logging
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.database.models import Skill, Employee
from backend.recommendation.utils import load_recommendation_config
from backend.recommendation.candidate_retriever import CandidateRetriever
from backend.recommendation.business_rules import BusinessRulesEngine
from backend.recommendation.feature_builder import FeatureBuilder
from backend.recommendation.scoring_engine import ScoringEngine
from backend.recommendation.ranking_engine import RankingEngine
from backend.recommendation.explanation_engine import ExplanationEngine
from backend.recommendation.evaluation import RecommendationEvaluator
from backend.recommendation.schemas import RecommendationRequest, RecommendationResponse

# Sub-engines
from backend.recommendation.semantic_engine import SemanticEngine
from backend.recommendation.historical_engine import HistoricalEngine
from backend.recommendation.availability_engine import AvailabilityEngine
from backend.recommendation.competency_engine import CompetencyEngine
from backend.recommendation.fusion_engine import FusionEngine
from backend.recommendation.confidence_engine import ConfidenceEngine
from backend.recommendation.diversity_engine import DiversityEngine

logger = logging.getLogger("recommendation_service")

class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.config = load_recommendation_config()
        self.retriever = CandidateRetriever(db)
        self.rules_engine = BusinessRulesEngine(self.config)
        self.scoring_engine = ScoringEngine(self.config)
        self.ranking_engine = RankingEngine(self.config)
        self.explanation_engine = ExplanationEngine(self.config)
        self.evaluator = RecommendationEvaluator(db)

        # Instantiate multiple recommendation strategy engines
        self.semantic_engine = SemanticEngine(self.config)
        self.historical_engine = HistoricalEngine(db, self.config)
        self.availability_engine = AvailabilityEngine(self.config)
        self.competency_engine = CompetencyEngine(self.config)
        self.fusion_engine = FusionEngine(self.config)
        self.confidence_engine = ConfidenceEngine()
        self.diversity_engine = DiversityEngine(self.config)

    def _build_skills_rarity(self) -> Tuple[Dict[str, float], float]:
        """Precomputes a rarity mapping (IDF) for all skills registered in the database for active employees."""
        active_employees = self.db.query(Employee).filter(
            (Employee.date_of_resignation == None) | (Employee.date_of_resignation > Employee.date_of_join)
        ).all()
        active_emp_ids = {emp.employee_id for emp in active_employees}
        total_active_employees = len(active_emp_ids) or 1

        all_skills = self.db.query(Skill).all()
        skill_counts = Counter(
            s.skill.lower().strip()
            for s in all_skills
            if s.skill and s.employee_id in active_emp_ids
        )
        
        import math
        skills_idf = {
            skill: math.log(1.0 + total_active_employees / (1.0 + count))
            for skill, count in skill_counts.items()
        }
        default_idf = math.log(1.0 + total_active_employees / 1.0)
        return skills_idf, default_idf

    def recommend_resources(self, request: RecommendationRequest) -> RecommendationResponse:
        """
        Orchestrates candidate retrieval, filtering, multi-strategy scoring, ensembling, diversity, and LLM explanation.
        """
        start_time = time.time()
        selected_strategy = (request.strategy or "hybrid_v1").lower().strip()
        logger.info(f"Triggering recommendations with strategy '{selected_strategy}' for project {request.project_id}")

        # Parse project start date and determine target window
        import datetime
        from backend.database.models import Project
        
        try:
            proj_start = datetime.datetime.strptime(request.project_start_date, "%Y-%m-%d").date()
        except Exception:
            proj_start = datetime.date.today() + datetime.timedelta(days=30)
            
        proj_end = None
        if request.project_id:
            proj = self.db.query(Project).filter(Project.project_id == request.project_id).first()
            if proj and proj.project_end_date:
                proj_end = proj.project_end_date
                
        if not proj_end:
            proj_end = proj_start + datetime.timedelta(days=180) # default to 6 months

        # 1. Candidate Retrieval (SQL + Qdrant similarity)
        raw_candidates = self.retriever.retrieve_candidates(
            required_skills=request.required_skills,
            project_id=request.project_id,
            top_n=50,
            project_start_date=proj_start,
            project_end_date=proj_end
        )

        # 2. Apply Business Rules Filter
        filtered_candidates = self.rules_engine.filter_candidates(
            candidates=raw_candidates,
            required_skills=request.required_skills,
            project_start_date_str=request.project_start_date
        )

        if not filtered_candidates:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return RecommendationResponse(
                recommendations=[],
                explanation="No active candidates met the business criteria or mandatory skills list.",
                processing_time_ms=round(elapsed_ms, 2)
            )

        # 3. Precompute Skill Rarity scores (IDF)
        skills_idf, default_idf = self._build_skills_rarity()

        # 4. Precompute Historical Metrics
        emp_ids = [c["employee"].employee_id for c in filtered_candidates]
        self.historical_engine.precompute_metrics(
            employee_ids=emp_ids,
            current_project_id=request.project_id,
            required_skills=request.required_skills,
            project_type=request.project_type
        )

        # 5. Multi-Strategy feature builder & scoring
        feature_builder = FeatureBuilder(self.config, skills_idf, default_idf)
        scored_candidates = []
        
        for cand in filtered_candidates:
            emp = cand["employee"]
            emp_id = emp.employee_id
            
            # Rule-Based Score features
            norm_features = feature_builder.build_features(
                cand=cand,
                required_skills=request.required_skills,
                required_competencies=request.required_competencies or []
            )
            rule_score_dict = self.scoring_engine.calculate_score(norm_features)
            rule_score = rule_score_dict["final_score"]
            
            # Semantic Score
            sem_score = self.semantic_engine.calculate_score(cand)
            
            # Historical Score
            hist_score = self.historical_engine.calculate_score(emp_id)
            
            # Availability Score
            avail_score = self.availability_engine.calculate_score(cand, request.project_start_date)
            
            # Competency Score
            comp_score = self.competency_engine.calculate_score(cand, request.required_competencies or [])

            # Compile strategy scores dict
            strategy_scores = {
                "rule_based_v1": rule_score,
                "semantic_only": sem_score,
                "historical_only": hist_score,
                "availability_only": avail_score,
                "competency_only": comp_score
            }
            
            # Route strategy selection
            if selected_strategy == "rule_based_v1":
                final_score = rule_score
            elif selected_strategy == "semantic_only":
                final_score = sem_score
            elif selected_strategy == "historical_only":
                final_score = hist_score
            elif selected_strategy == "availability_only":
                final_score = avail_score
            elif selected_strategy == "competency_only":
                final_score = comp_score
            elif selected_strategy == "hybrid_v1":
                final_score = self.fusion_engine.calculate_hybrid_score(strategy_scores)
            else:
                final_score = self.fusion_engine.calculate_hybrid_score(strategy_scores)

            scored_candidates.append({
                "candidate": cand,
                "final_score": final_score,
                "strategy_scores": strategy_scores,
                "category_scores": rule_score_dict["category_scores"]
            })

        # 6. Sorting
        sorted_scored = sorted(scored_candidates, key=lambda x: x["final_score"], reverse=True)

        # 7. Apply Diversity Capping Filter
        diverse_scored = self.diversity_engine.apply_diversity_filter(
            scored_candidates=sorted_scored,
            top_n=request.top_n
        )

        # 8. Rank, format, and assign confidence levels
        top_recommendations = []
        for idx, item in enumerate(diverse_scored):
            cand = item["candidate"]
            emp = cand["employee"]
            emp_id = emp.employee_id
            
            # Format availability
            availability_date = "Immediate"
            if cand["utilization"] > 0:
                max_end = None
                for a in cand["allocations"]:
                    if a.is_allocation_active == 1 and a.allocated_end_date:
                        if max_end is None or a.allocated_end_date > max_end:
                            max_end = a.allocated_end_date
                if max_end:
                    availability_date = max_end.strftime("%Y-%m-%d")

            # Extract matching skills
            emp_skills_lower = {s.skill.lower().strip() for s in cand["skills"] if s.skill}
            matching_skills = [req for req in request.required_skills if req.lower().strip() in emp_skills_lower]

            # Calculate confidence level
            confidence = self.confidence_engine.calculate_confidence(
                matching_skills=matching_skills,
                required_skills=request.required_skills,
                qdrant_score=cand.get("qdrant_score", 0.0),
                has_hist=cand.get("has_similar_proj_experience", False),
                final_score=item["final_score"]
            )

            top_recommendations.append({
                "employee_id": emp_id,
                "job_name": emp.job_name or "N/A",
                "department_name": emp.department_name or "N/A",
                "final_score": float(item["final_score"]),
                "rank": idx + 1,
                "category_scores": item["category_scores"],
                "strategy_scores": item["strategy_scores"],
                "confidence": confidence,
                "availability_date": availability_date,
                "utilization_percentage": float(cand["utilization"]),
                "matching_skills": matching_skills
            })

        # 9. Generate Explanation via LLM
        project_info = {
            "required_skills": request.required_skills,
            "project_type": request.project_type,
            "project_start_date": request.project_start_date,
            "required_competencies": request.required_competencies or []
        }
        
        explanation = self.explanation_engine.generate_explanation(
            project_info=project_info,
            top_recommendations=top_recommendations
        )

        # 10. Run evaluation logging & log experiment CSV
        elapsed_ms = (time.time() - start_time) * 1000.0
        if request.project_id:
            try:
                # Standard evaluate logging
                eval_metrics = self.evaluator.evaluate(
                    project_id=request.project_id,
                    recommendations=top_recommendations,
                    elapsed_time_ms=elapsed_ms
                )
                # Save as run experiment to strategy_comparison.csv
                self.evaluator.log_experiment(
                    strategy=selected_strategy,
                    weights=self.fusion_engine.fusion_weights,
                    metrics=eval_metrics
                )
            except Exception as eval_err:
                logger.error(f"Failed to log evaluation run details: {eval_err}")

        return RecommendationResponse(
            recommendations=top_recommendations,
            explanation=explanation,
            processing_time_ms=round(elapsed_ms, 2)
        )
