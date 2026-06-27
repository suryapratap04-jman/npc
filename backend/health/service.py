import time
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.database.models import Project, Allocation

from backend.health.feature_builder import HealthFeatureBuilder
from backend.health.risk_engine import RiskEngine
from backend.health.utilization_engine import UtilizationEngine
from backend.health.billability_engine import BillabilityEngine
from backend.health.rampdown_engine import RampdownEngine
from backend.health.recommendation_engine import ActionRecommendationEngine
from backend.health.explanation_engine import ExplanationEngine
from backend.health.evaluation import HealthEvaluator
from backend.health.schemas import (
    ProjectHealthSummary, ProjectHealthDetail, ScheduleHealth, 
    UtilizationHealth, BillabilityHealth, RampDownDetail
)

logger = logging.getLogger("health_service")

class ProjectHealthService:
    def __init__(self, db: Session):
        self.db = db
        self.feature_builder = HealthFeatureBuilder(db)
        self.risk_engine = RiskEngine()
        self.utilization_engine = UtilizationEngine()
        self.billability_engine = BillabilityEngine(db)
        self.rampdown_engine = RampdownEngine(db)
        self.rec_engine = ActionRecommendationEngine(db)
        self.explanation_engine = ExplanationEngine()
        self.evaluator = HealthEvaluator()

    def _get_active_projects(self) -> List[Project]:
        """Returns all projects that are not Closed, Completed, or Deal Lost."""
        return self.db.query(Project).filter(
            Project.is_active_version == 1,
            ~Project.project_status.in_(["CLOSED", "COMPLETE", "DEAL LOST"])
        ).all()

    def get_projects_health(self) -> List[ProjectHealthSummary]:
        """
        Retrieves health summaries for all active projects and logs the aggregated run metrics.
        """
        start_time = time.time()
        projects = self._get_active_projects()
        summaries = []
        details_for_log = []

        for p in projects:
            try:
                features = self.feature_builder.build_project_features(p.project_id)
                risk = self.risk_engine.calculate_risk(features)
                
                # Fetch basic utilization & billability metrics for aggregate evaluation
                allocs = self.db.query(Allocation).filter(
                    Allocation.project_id == p.project_id,
                    Allocation.is_allocation_active == 1
                ).all()
                team_ids = [a.employee_id for a in allocs if a.employee_id]
                
                util = self.utilization_engine.analyze_utilization(features)
                bill = self.billability_engine.analyze_billability(p.project_id, team_ids)

                summaries.append(ProjectHealthSummary(
                    project_id=p.project_id,
                    project_key=p.project_key,
                    overall_health=risk["overall_health"],
                    risk_score=risk["risk_score"],
                    risk_level=risk["risk_level"]
                ))
                
                details_for_log.append({
                    "risk_level": risk["risk_level"],
                    "risk_score": risk["risk_score"],
                    "utilization": util,
                    "billability": bill
                })
            except Exception as e:
                logger.error(f"Error computing health for project {p.project_id}: {e}")

        # Run offline evaluator
        elapsed_ms = (time.time() - start_time) * 1000.0
        try:
            self.evaluator.evaluate_and_log(details_for_log, elapsed_ms)
        except Exception as eval_err:
            logger.error(f"Failed to run health evaluator: {eval_err}")

        return summaries

    def get_project_health_detail(self, project_id: str) -> ProjectHealthDetail:
        """
        Runs detailed diagnostic pipelines for a specific project.
        """
        # 1. Build features
        features = self.feature_builder.build_project_features(project_id)

        # 2. Risk Detection
        risk = self.risk_engine.calculate_risk(features)

        # 3. Utilization Analysis
        util = self.utilization_engine.analyze_utilization(features)

        # 4. Billability Analysis
        allocs = self.db.query(Allocation).filter(
            Allocation.project_id == project_id,
            Allocation.is_allocation_active == 1
        ).all()
        team_employee_ids = [a.employee_id for a in allocs if a.employee_id]
        bill = self.billability_engine.analyze_billability(project_id, team_employee_ids)

        # 5. Ramp-down Evaluation
        ramp = self.rampdown_engine.evaluate_rampdown(project_id, features, team_employee_ids)

        # 6. Generate Action Recommendations
        actions = self.rec_engine.generate_recommendations(
            project_id=project_id,
            features=features,
            risk_analysis=risk,
            utilization_analysis=util,
            billability_analysis=bill,
            rampdown_analysis=ramp,
            team_employee_ids=team_employee_ids
        )

        # 7. Generate Explanation
        explanation = self.explanation_engine.generate_explanation(
            project_id=project_id,
            risk_analysis=risk,
            utilization_analysis=util,
            billability_analysis=bill,
            rampdown_analysis=ramp,
            actions=actions
        )

        return ProjectHealthDetail(
            project_id=project_id,
            overall_health=risk["overall_health"],
            risk_score=risk["risk_score"],
            risk_level=risk["risk_level"],
            schedule=ScheduleHealth(
                status=features["schedule_status"],
                delay_days=features["delay_days"],
                days_remaining=features["days_remaining"],
                planned_duration=features["planned_duration"],
                actual_duration=features["actual_duration"],
                extension_count=features["extension_count"]
            ),
            utilization=UtilizationHealth(
                average=util["average"],
                peak=util["peak"],
                overallocated_count=util["overallocated_count"],
                underutilized_count=util["underutilized_count"],
                idle_capacity_percentage=util["idle_capacity_percentage"],
                releasable_capacity_percentage=util["releasable_capacity_percentage"]
            ),
            billability=BillabilityHealth(
                percentage=bill["percentage"],
                billable_hours=bill["billable_hours"],
                non_billable_hours=bill["non_billable_hours"],
                shadow_resources_count=bill["shadow_resources_count"],
                billability_trend=bill["billability_trend"],
                cost_recovery_status=bill["cost_recovery_status"]
            ),
            recommended_actions=actions,
            explanation=explanation
        )

    def get_rampdown_candidates(self) -> List[RampDownDetail]:
        """
        List all projects suitable for resource releases.
        """
        projects = self._get_active_projects()
        candidates = []
        
        for p in projects:
            try:
                features = self.feature_builder.build_project_features(p.project_id)
                allocs = self.db.query(Allocation).filter(
                    Allocation.project_id == p.project_id,
                    Allocation.is_allocation_active == 1
                ).all()
                team_ids = [a.employee_id for a in allocs if a.employee_id]
                
                ramp = self.rampdown_engine.evaluate_rampdown(p.project_id, features, team_ids)
                if ramp["is_suitable"]:
                    candidates.append(RampDownDetail(
                        project_id=p.project_id,
                        is_suitable=True,
                        estimated_release_count=ramp["estimated_release_count"],
                        earliest_release_date=ramp["earliest_release_date"],
                        skills_released=ramp["skills_released"]
                    ))
            except Exception as e:
                logger.error(f"Error checking rampdown for project {p.project_id}: {e}")
                
        return candidates

    def get_utilization_stats(self) -> List[Dict[str, Any]]:
        """Returns capacity utilization breakdown per active project."""
        projects = self._get_active_projects()
        stats = []
        for p in projects:
            try:
                features = self.feature_builder.build_project_features(p.project_id)
                util = self.utilization_engine.analyze_utilization(features)
                stats.append({
                    "project_id": p.project_id,
                    "average_utilization": util["average"],
                    "peak_utilization": util["peak"],
                    "overallocated_count": util["overallocated_count"],
                    "idle_capacity": util["idle_capacity_percentage"]
                })
            except Exception as e:
                logger.error(f"Error building utilization stats for project {p.project_id}: {e}")
        return stats

    def get_billability_stats(self) -> List[Dict[str, Any]]:
        """Returns resource cost recovery logs per active project."""
        projects = self._get_active_projects()
        stats = []
        for p in projects:
            try:
                allocs = self.db.query(Allocation).filter(
                    Allocation.project_id == p.project_id,
                    Allocation.is_allocation_active == 1
                ).all()
                team_ids = [a.employee_id for a in allocs if a.employee_id]
                bill = self.billability_engine.analyze_billability(p.project_id, team_ids)
                stats.append({
                    "project_id": p.project_id,
                    "billability_percentage": bill["percentage"],
                    "billable_hours": bill["billable_hours"],
                    "non_billable_hours": bill["non_billable_hours"],
                    "shadow_resources_count": bill["shadow_resources_count"],
                    "cost_recovery_status": bill["cost_recovery_status"]
                })
            except Exception as e:
                logger.error(f"Error building billability stats for project {p.project_id}: {e}")
        return stats
