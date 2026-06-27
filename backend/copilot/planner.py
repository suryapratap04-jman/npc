import logging
from typing import Dict, List, Any, Tuple, Optional

from backend.copilot.tool_registry import ToolRegistry

logger = logging.getLogger("planner")

class Planner:
    def __init__(self):
        pass

    def execute_plan(self, 
                     intent: str, 
                     parameters: Dict[str, Any], 
                     registry: ToolRegistry) -> Tuple[Dict[str, Any], List[str]]:
        """
        Formulates an execution plan (sequence of tools) based on classified intent,
        executes the tools, and aggregates the results.
        """
        executed_tools = []
        aggregated_results = {}
        
        # 1. Workflow B: NEW_PROJECT_FORECAST (Forecast -> Capacity -> Redeployment -> Hiring)
        if intent == "NEW_PROJECT_FORECAST":
            logger.info("Executing Planner Workflow B: New Project Demand Forecasting & Capacity Matching")
            
            p_type = parameters.get("project_type", "AI")
            skills = parameters.get("required_skills", [])
            duration = parameters.get("expected_duration_months", 6)
            start_date = "2026-08-15"
            
            # Tool 1: New Project Forecast
            try:
                aggregated_results["forecast"] = registry.get_new_project_forecast(
                    project_type=p_type,
                    expected_duration_months=duration,
                    required_skills=skills,
                    expected_start_date=start_date
                )
                executed_tools.append("get_new_project_forecast")
            except Exception as e:
                logger.error(f"Tool get_new_project_forecast failed: {e}")
                
            # Tool 2: Capacity Engine Projections
            try:
                aggregated_results["capacity"] = registry.get_capacity_status()
                executed_tools.append("get_capacity_status")
            except Exception as e:
                logger.error(f"Tool get_capacity_status failed: {e}")
                
            # Tool 3: Redeployment transitions
            try:
                aggregated_results["redeployment"] = registry.get_redeployment_options(
                    project_type=p_type,
                    expected_duration_months=duration,
                    required_skills=skills,
                    expected_start_date=start_date
                )
                executed_tools.append("get_redeployment_options")
            except Exception as e:
                logger.error(f"Tool get_redeployment_options failed: {e}")
                
            # Tool 4: Hiring requirements
            try:
                aggregated_results["hiring"] = registry.get_hiring_needs(
                    project_type=p_type,
                    expected_duration_months=duration,
                    required_skills=skills,
                    expected_start_date=start_date
                )
                executed_tools.append("get_hiring_needs")
            except Exception as e:
                logger.error(f"Tool get_hiring_needs failed: {e}")

        # 2. Workflow A: RESOURCE_RECOMMENDATION (Recommendation -> Project Health -> Explain)
        elif intent == "RESOURCE_RECOMMENDATION":
            logger.info("Executing Planner Workflow A: Resource Recommendation & Explanations")
            
            proj_id = parameters.get("project_id")
            skills = parameters.get("required_skills", [])
            p_type = parameters.get("project_type", "AI")
            
            # Tool 1: Recommendation Matching
            try:
                aggregated_results["recommendations"] = registry.recommend_resources(
                    project_id=proj_id,
                    required_skills=skills,
                    project_type=p_type,
                    top_n=5
                )
                executed_tools.append("recommend_resources")
            except Exception as e:
                logger.error(f"Tool recommend_resources failed: {e}")
                
            # Tool 2: Project Health audit (if project_id is available)
            if proj_id:
                try:
                    aggregated_results["project_health"] = registry.get_project_health_detail(proj_id)
                    executed_tools.append("get_project_health_detail")
                except Exception as e:
                    logger.error(f"Tool get_project_health_detail failed: {e}")
                    
            # Tool 3: RAG explanation matches
            recs = aggregated_results.get("recommendations", {}).get("recommendations", [])
            if recs and proj_id:
                first_emp_id = recs[0]["employee_id"]
                try:
                    explanation = registry.query_rag(
                        query="",
                        type="explain",
                        employee_id=first_emp_id,
                        project_id=proj_id
                    )
                    aggregated_results["rag_explanation"] = explanation
                    executed_tools.append("query_rag")
                except Exception as e:
                    logger.error(f"Tool query_rag failed: {e}")

        # 3. Workflow C: EMPLOYEE_SEARCH (Semantic Search -> Recommend -> Explain)
        elif intent == "EMPLOYEE_SEARCH":
            logger.info("Executing Planner Workflow C: Employee Semantic Search & Scoring")
            
            skills = parameters.get("required_skills", [])
            query = " ".join(skills) if skills else "data engineer"
            
            # Tool 1: Semantic Search
            try:
                aggregated_results["search_results"] = registry.search_employees(query, limit=5)
                executed_tools.append("search_employees")
            except Exception as e:
                logger.error(f"Tool search_employees failed: {e}")
                
            # Tool 2: Recommendations rules ranking
            try:
                aggregated_results["recommendations"] = registry.recommend_resources(
                    project_id=None,
                    required_skills=skills,
                    project_type="Client Project",
                    top_n=5
                )
                executed_tools.append("recommend_resources")
            except Exception as e:
                logger.error(f"Tool recommend_resources failed: {e}")

        # 4. Workflow D: PROJECT_HEALTH (List Health -> Rampdown Timelines)
        elif intent == "PROJECT_HEALTH":
            logger.info("Executing Planner Workflow D: Project Health & Release Audit")
            proj_id = parameters.get("project_id")
            
            if proj_id:
                try:
                    aggregated_results["project_health"] = registry.get_project_health_detail(proj_id)
                    executed_tools.append("get_project_health_detail")
                except Exception as e:
                    logger.error(f"Tool get_project_health_detail failed: {e}")
            else:
                try:
                    aggregated_results["projects_health_list"] = registry.get_projects_health()
                    executed_tools.append("get_projects_health")
                except Exception as e:
                    logger.error(f"Tool get_projects_health failed: {e}")
                    
            try:
                aggregated_results["rampdown_candidates"] = registry.get_rampdown_candidates()
                executed_tools.append("get_rampdown_candidates")
            except Exception as e:
                logger.error(f"Tool get_rampdown_candidates failed: {e}")

        # 5. Intent: PIPELINE_FORECAST
        elif intent == "PIPELINE_FORECAST":
            try:
                aggregated_results["pipeline_forecast"] = registry.get_six_month_forecast()
                executed_tools.append("get_six_month_forecast")
            except Exception as e:
                logger.error(f"Tool get_six_month_forecast failed: {e}")
                
            try:
                aggregated_results["rampdown_candidates"] = registry.get_rampdown_candidates()
                executed_tools.append("get_rampdown_candidates")
            except Exception as e:
                logger.error(f"Tool get_rampdown_candidates failed: {e}")

        # 6. Intent: CAPACITY
        elif intent == "CAPACITY":
            try:
                aggregated_results["capacity"] = registry.get_capacity_status()
                executed_tools.append("get_capacity_status")
            except Exception as e:
                logger.error(f"Tool get_capacity_status failed: {e}")

        # 7. Intent: HIRING
        elif intent == "HIRING":
            p_type = parameters.get("project_type", "AI")
            skills = parameters.get("required_skills", [])
            duration = parameters.get("expected_duration_months", 6)
            try:
                aggregated_results["hiring"] = registry.get_hiring_needs(
                    project_type=p_type,
                    expected_duration_months=duration,
                    required_skills=skills
                )
                executed_tools.append("get_hiring_needs")
            except Exception as e:
                logger.error(f"Tool get_hiring_needs failed: {e}")

        # 8. Intent: REDEPLOYMENT
        elif intent == "REDEPLOYMENT":
            p_type = parameters.get("project_type", "AI")
            skills = parameters.get("required_skills", [])
            duration = parameters.get("expected_duration_months", 6)
            try:
                aggregated_results["redeployment"] = registry.get_redeployment_options(
                    project_type=p_type,
                    expected_duration_months=duration,
                    required_skills=skills
                )
                executed_tools.append("get_redeployment_options")
            except Exception as e:
                logger.error(f"Tool get_redeployment_options failed: {e}")

        # 9. Intent: PROJECT_SEARCH
        elif intent == "PROJECT_SEARCH":
            query = " ".join(parameters.get("required_skills", [])) or "AI"
            try:
                aggregated_results["search_results"] = registry.search_projects(query, limit=5)
                executed_tools.append("search_projects")
            except Exception as e:
                logger.error(f"Tool search_projects failed: {e}")

        # 10. Fallback: GENERAL_QA
        else:
            query = parameters.get("query", "general Q&A")
            try:
                # Retrieve from RAG
                aggregated_results["rag_result"] = registry.query_rag(query=query)
                executed_tools.append("query_rag")
            except Exception as e:
                logger.error(f"Tool query_rag failed: {e}")

        return aggregated_results, executed_tools
