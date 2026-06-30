import time
import logging
import datetime
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.database.models import Skill, Employee, Project, Pipeline, Competency, Allocation
from backend.recommendation.utils import load_recommendation_config
from backend.recommendation.candidate_retriever import CandidateRetriever
from backend.recommendation.business_rules import BusinessRulesEngine
from backend.recommendation.feature_builder import FeatureBuilder
from backend.recommendation.scoring_engine import ScoringEngine
from backend.recommendation.ranking_engine import RankingEngine
from backend.recommendation.explanation_engine import ExplanationEngine
from backend.recommendation.evaluation import RecommendationEvaluator
from backend.recommendation.schemas import RecommendationRequest, RecommendationResponse, CandidateRecommendation, ProjectDetail
from backend.cache.cache_service import cache_service

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
        try:
            proj_start = datetime.datetime.strptime(request.project_start_date, "%Y-%m-%d").date()
        except Exception:
            proj_start = datetime.date.today() + datetime.timedelta(days=30)
            
        proj_end = None
        if request.project_id:
            try:
                proj = self.db.query(Project).filter(Project.project_id == request.project_id).first()
                if proj and proj.project_end_date:
                    proj_end = proj.project_end_date
            except Exception:
                pass
                
        if not proj_end:
            proj_end = proj_start + datetime.timedelta(days=180) # default to 6 months

        # 1. Load project details from the pipeline/project DB for response enrichment
        project_detail = None
        if request.project_id:
            try:
                pipeline_id = int(request.project_id)
                db_proj = self.db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
                if db_proj:
                    project_detail = ProjectDetail(
                        project_id=str(db_proj.id),
                        name=f"{db_proj.client or 'N/A'} - {db_proj.solution or 'N/A'}",
                        client=db_proj.client or "N/A",
                        technology=db_proj.solution or "N/A",
                        domain=db_proj.cluster or "N/A",
                        required_skills=[s.strip() for s in (db_proj.skillset or "").split(",") if s.strip()],
                        project_type=db_proj.request_type or "AI",
                        expected_start_date=str(db_proj.likely_start_date or "N/A"),
                        demand=db_proj.resources_requested or "N/A"
                    )
            except Exception as e:
                logger.debug(f"Could not load project from pipeline by ID: {e}")

        # 2. Candidate Retrieval (SQL + Qdrant similarity)
        raw_candidates = self.retriever.retrieve_candidates(
            required_skills=request.required_skills,
            project_id=request.project_id,
            top_n=50,
            project_start_date=proj_start,
            project_end_date=proj_end,
            technology=request.technology,
            domain=request.domain,
            project_type=request.project_type
        )
        logger.info(f"[STAGE 8] Semantic Retrieval candidate pool: {len(raw_candidates)}")

        # 3. Apply Business Rules Filter
        filtered_candidates = self.rules_engine.filter_candidates(
            candidates=raw_candidates,
            required_skills=request.required_skills,
            project_start_date_str=request.project_start_date,
            department=request.department or "all",
            experience_range=request.experience_range or "all",
            availability_window=request.availability_window or "all",
            location=request.location or "all"
        )

        if not filtered_candidates:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return RecommendationResponse(
                project=project_detail,
                summary="No active candidates met the search filters.",
                candidates=[],
                recommendations=[],
                explanation="No active candidates met the business criteria or mandatory skills list.",
                processing_time_ms=round(elapsed_ms, 2)
            )

        # 4. Precompute Skill Rarity scores (IDF)
        skills_idf_cache = cache_service.get("precomputed:skills_idf")
        if skills_idf_cache:
            skills_idf = skills_idf_cache["skills_idf"]
            default_idf = skills_idf_cache["default_idf"]
        else:
            skills_idf, default_idf = self._build_skills_rarity()

        # 5. Precompute Historical Metrics
        emp_ids = [c["employee"].employee_id for c in filtered_candidates]
        self.historical_engine.precompute_metrics(
            employee_ids=emp_ids,
            current_project_id=request.project_id,
            required_skills=request.required_skills,
            project_type=request.project_type
        )

        # 6. Preload all projects for candidate current project lookup
        projects_name_map = cache_service.get("precomputed:projects_name_map")
        if not projects_name_map:
            all_active_projects = self.db.query(Project).all()
            projects_name_map = {p.project_id: f"{p.client_id or 'Client'} - {p.type_of_project or 'Engagement'}" for p in all_active_projects}

        # 7. Multi-Strategy feature builder & scoring
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

        # 8. Sorting
        sorted_scored = sorted(scored_candidates, key=lambda x: x["final_score"], reverse=True)

        # 9. Apply Diversity Capping Filter
        diverse_scored = self.diversity_engine.apply_diversity_filter(
            scored_candidates=sorted_scored,
            top_n=request.top_n
        )
        logger.info(f"[STAGE 9] Final Ranking returned: {len(diverse_scored)} recommendations.")

        # 10. Rank, format, and assign confidence levels & enrichment details
        top_recommendations = []
        for idx, item in enumerate(diverse_scored):
            cand = item["candidate"]
            emp = cand["employee"]
            emp_id = emp.employee_id
            
            # Format availability date
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

            # Generate friendly employee name
            emp_numeric_id = emp_id.split('_')[-1]
            employee_name = f"Employee {emp_numeric_id}"

            # Skills list (raw strings)
            candidate_skills = [s.skill for s in cand["skills"] if s.skill]

            # Competencies list (those with rating >= 3, similar to /api/employees endpoint)
            candidate_competencies = []
            comp = cand["competency"]
            if comp:
                comp_map = {
                    "Stakeholder Management": comp.stakeholder_management_score,
                    "Consultative Guidance": comp.consultative_guidance_score,
                    "Techno-Functional Expertise": comp.techno_functional_score,
                    "Communication Skills": comp.communication_score,
                    "Ambiguity Navigation": comp.ambiguity_navigation_score,
                    "Capabilities Articulation": comp.capabilities_articulation_score,
                    "Solution Architecture": comp.solution_architecture_score,
                    "Project Planning": comp.project_planning_score
                }
                candidate_competencies = [k for k, v in comp_map.items() if v is not None and v >= 3]

            # Current project lookup
            current_project_name = "None (On Bench)"
            if cand["allocations"]:
                sorted_allocs = sorted(cand["allocations"], key=lambda a: a.allocation_by_percentage or 0, reverse=True)
                top_alloc = sorted_allocs[0]
                if top_alloc.is_allocation_active == 1:
                    current_project_name = projects_name_map.get(top_alloc.project_id, f"Project {top_alloc.project_id}")

            # Calculate experience years
            exp_years = 0.0
            for s in cand["skills"]:
                if s.experience_numeric is not None:
                    exp_years = max(exp_years, float(s.experience_numeric))
            if exp_years == 0.0:
                exp_years = 4.0

            # Compute category scores for response mappings
            category_scores = item["category_scores"]
            
            # Generate Candidate-Specific Explanations
            why, strengths, risks = self._generate_candidate_highlights(
                category_scores=category_scores,
                matching_skills=matching_skills,
                experience_years=exp_years,
                current_allocation=cand["raw_utilization"]
            )

            rec = CandidateRecommendation(
                employee_id=emp_id,
                name=employee_name,
                email=f"{emp_id.lower()}@company.com",
                job_name=emp.job_name or "N/A",
                department_name=emp.department_name or "N/A",
                location=emp.location or "N/A",
                experience_years=float(exp_years),
                skills=candidate_skills,
                competencies=candidate_competencies,
                matching_skills=matching_skills,
                current_allocation=float(cand["raw_utilization"]),
                utilization_percentage=float(cand["utilization"]),
                availability_date=availability_date,
                current_project=current_project_name,
                final_score=float(item["final_score"]),
                rank=idx + 1,
                confidence=confidence,
                why_recommended=why,
                strengths=strengths,
                potential_risks=risks,
                
                # Detailed scoring breaks
                skill_match=float(category_scores.get("skill_match", 0.0)),
                competency_match=float(category_scores.get("competency_match", 0.0)),
                experience_score=float(category_scores.get("project_experience", 0.0)),
                availability_score=float(category_scores.get("availability", 0.0)),
                historical_score=float(item["strategy_scores"].get("historical_only", 50.0)),
                semantic_score=float(item["strategy_scores"].get("semantic_only", 50.0)),
                
                category_scores=category_scores,
                strategy_scores=item["strategy_scores"]
            )
            top_recommendations.append(rec)

        # 11. Generate Explanation via LLM
        project_info = {
            "required_skills": request.required_skills,
            "project_type": request.project_type,
            "project_start_date": request.project_start_date,
            "required_competencies": request.required_competencies or []
        }
        
        explanation = self.explanation_engine.generate_explanation(
            project_info=project_info,
            top_recommendations=[r.dict() for r in top_recommendations]
        )

        # 12. Run evaluation logging & log experiment CSV
        elapsed_ms = (time.time() - start_time) * 1000.0
        if request.project_id:
            try:
                # Standard evaluate logging
                eval_metrics = self.evaluator.evaluate(
                    project_id=request.project_id,
                    recommendations=[r.dict() for r in top_recommendations],
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

        # Compute list overall confidence
        overall_confidence = "Medium"
        if top_recommendations:
            high_count = sum(1 for r in top_recommendations[:3] if r.confidence == "High")
            if high_count >= 2:
                overall_confidence = "High"
            elif sum(1 for r in top_recommendations[:3] if r.confidence == "Low") >= 2:
                overall_confidence = "Low"

        summary_text = f"Identified {len(top_recommendations)} qualified resources matching constraints. Top recommendation is {top_recommendations[0].name if top_recommendations else 'N/A'}."

        return RecommendationResponse(
            project=project_detail,
            summary=summary_text,
            candidates=top_recommendations,
            recommendations=top_recommendations,
            explanation=explanation,
            confidence=overall_confidence,
            processing_time_ms=round(elapsed_ms, 2)
        )

    def _generate_candidate_highlights(
        self,
        category_scores: Dict[str, float],
        matching_skills: List[str],
        experience_years: float,
        current_allocation: float
    ) -> Tuple[str, List[str], List[str]]:
        """
        Calculates rule-based candidate specific highlights, strengths, and risks.
        """
        strengths = []
        risks = []
        
        skill_score = category_scores.get("skill_match", 0.0)
        comp_score = category_scores.get("competency_match", 0.0)
        exp_score = category_scores.get("project_experience", 0.0)
        avail_score = category_scores.get("availability", 0.0)
        sim_score = category_scores.get("project_similarity", 0.0)
        
        # Strengths Builder
        if skill_score >= 80:
            strengths.append(f"Exceptional required skill match ({len(matching_skills)} skills matched)")
        elif skill_score >= 50:
            strengths.append(f"Strong match for target skillset ({', '.join(matching_skills[:3])})")
            
        if comp_score >= 80:
            strengths.append("Verified expert-level behavioral and technical competencies")
        elif comp_score >= 60:
            strengths.append("Demonstrates solid communication and consultative guidance capabilities")
            
        if exp_score >= 70:
            strengths.append(f"High seniority with {experience_years:.1f} years of relative experience")
            
        if avail_score >= 80:
            strengths.append("Immediate bandwidth for assignment; fully unallocated or rolling off soon")
        elif avail_score >= 50:
            strengths.append(f"Moderate capacity available ({100.0 - current_allocation:.0f}% capacity free)")
            
        if sim_score >= 70:
            strengths.append("High historical similarity with project technical architecture")
            
        if not strengths:
            strengths.append("Good baseline skills match and functional readiness")
            
        # Risks Builder
        if current_allocation >= 80.0:
            risks.append(f"High workload allocation ({current_allocation:.0f}%) may cause delivery conflicts")
        if skill_score < 60:
            risks.append("Partial skill match; may require upskilling on minor requested tools")
        if exp_score < 40:
            risks.append(f"Junior profile ({experience_years:.1f} yrs experience) might need senior mentorship")
        if comp_score < 50:
            risks.append("Lower competency verified scores in client-facing traits")
            
        if not risks:
            risks.append("Minimal operational risks identified for this candidate")
            
        # Why Recommended Summary
        top_recs = []
        if skill_score >= 80:
            top_recs.append("top-tier technical alignment")
        if avail_score >= 80:
            top_recs.append("immediate availability")
        if comp_score >= 80:
            top_recs.append("proven competencies")
            
        if top_recs:
            why = f"Highly recommended due to {' and '.join(top_recs)}."
        else:
            why = f"Recommended based on a solid combined score of {skill_score:.0f}% skills match and {avail_score:.0f}% availability."
            
        return why, strengths, risks
