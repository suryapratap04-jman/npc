import logging
from typing import Dict, List, Any

logger = logging.getLogger("response_builder")

class ResponseBuilder:
    def __init__(self):
        pass

    def build_response(self, 
                       intent: str, 
                       parameters: Dict[str, Any], 
                       aggregated_results: Dict[str, Any]) -> str:
        """
        Formats aggregated tool outputs into a cohesive, executive conversational response
        comprising Summary, Evidence, Risks, Recommendation, and Confidence.
        """
        # Fallback if no tool output was retrieved
        if not aggregated_results:
            return self._build_error_response("We encountered an error retrieving data from the backend services.")

        if intent == "NEW_PROJECT_FORECAST":
            return self._build_forecast_response(parameters, aggregated_results)
        elif intent == "RESOURCE_RECOMMENDATION":
            return self._build_recommendation_response(parameters, aggregated_results)
        elif intent == "PROJECT_HEALTH":
            return self._build_health_response(parameters, aggregated_results)
        elif intent == "PIPELINE_FORECAST":
            return self._build_pipeline_response(parameters, aggregated_results)
        elif intent == "CAPACITY":
            return self._build_capacity_response(parameters, aggregated_results)
        elif intent == "HIRING":
            return self._build_hiring_response(parameters, aggregated_results)
        elif intent == "REDEPLOYMENT":
            return self._build_redeploy_response(parameters, aggregated_results)
        elif intent == "EMPLOYEE_SEARCH":
            return self._build_employee_search_response(parameters, aggregated_results)
        elif intent == "PROJECT_SEARCH":
            return self._build_project_search_response(parameters, aggregated_results)
        else:
            return self._build_general_qa_response(parameters, aggregated_results)

    def _build_forecast_response(self, params: Dict[str, Any], results: Dict[str, Any]) -> str:
        f = results.get("forecast", {})
        c = results.get("capacity", {})
        r = results.get("redeployment", {})
        h = results.get("hiring", {})

        p_type = f.get("project_type", params.get("project_type", "New"))
        duration = f.get("expected_duration", params.get("expected_duration_months", 6))
        team_rec = f.get("team_recommendation", {})
        total_fte = f.get("estimated_fte", 0.0)
        cost = f.get("estimated_cost", 0.0)
        confidence = f.get("confidence", "Medium")

        avail_now = c.get("capacity_projections", {}).get("available_now", 0)
        avail_30 = c.get("capacity_projections", {}).get("available_30_days", 0)
        
        redeploy_ids = r.get("redeployment_options", [])
        hiring_needs = h.get("hiring_needs", [])

        # Executive Summary
        hiring_text = "No external hiring is required."
        if hiring_needs:
            hiring_text = f"External hiring is recommended for {sum(hn['count_needed'] for hn in hiring_needs)} slot(s)."
        
        summary = f"Capacity is sufficient to support a new **{p_type}** project. "
        summary += f"The project requires **{total_fte} FTEs** for a duration of **{duration} months**, with an estimated internal cost of **${cost:,.2f}**. {hiring_text}"

        # Evidence
        evidence_list = []
        evidence_list.append(f"Recommended staffing: " + ", ".join([f"{val} {key.replace('_', ' ').title()}" for key, val in team_rec.items() if val > 0]))
        evidence_list.append(f"We have **{avail_now}** available employees today, and **{avail_30}** within 30 days.")
        if redeploy_ids:
            evidence_list.append(f"Identified **{len(redeploy_ids)}** potential internal redeployment candidates completing active projects.")
        if f.get("sample_size", 0) > 0:
            evidence_list.append(f"Backed by historical data from **{f['sample_size']}** matching projects.")

        # Risks
        risks_list = []
        if hiring_needs:
            risks_list.append(f"External hiring takes typical ramp-up time and might delay project kickoff.")
        if avail_now < total_fte:
            risks_list.append(f"Immediate starting headcount is tight ({avail_now} available vs {total_fte} required).")
        if not risks_list:
            risks_list.append("None. Capacity matches demands perfectly.")

        # Recommendation
        recoms = []
        recoms.append(f"Approve the kickoff of the {p_type} project.")
        if redeploy_ids:
            recoms.append(f"Redeploy: " + ", ".join([f"{opt['employee_id']} (ends {opt['available_from']})" for opt in redeploy_ids[:2]]))
        for hn in hiring_needs:
            recoms.append(f"Hire: {hn['count_needed']} {hn['role']}")

        # Compile
        markdown = f"### Executive Summary\n\n{summary}\n\n"
        markdown += "### Supporting Evidence\n\n" + "\n".join([f"* {ev}" for ev in evidence_list]) + "\n\n"
        markdown += "### Risks\n\n" + "\n".join([f"* {rk}" for rk in risks_list]) + "\n\n"
        markdown += "### Recommendations\n\n" + "\n".join([f"1. {rec}" for rec in recoms]) + "\n\n"
        markdown += f"### Confidence\n\n**{confidence}**\n"
        return markdown

    def _build_recommendation_response(self, params: Dict[str, Any], results: Dict[str, Any]) -> str:
        rec_data = results.get("recommendations", {})
        health_data = results.get("project_health", {})
        rag_expl = results.get("rag_explanation", "")

        candidates = rec_data.get("recommendations", [])
        explanation = rec_data.get("explanation", "")

        if not candidates:
            return self._build_error_response("No suitable candidates were found matching the required criteria.")

        top_cand = candidates[0]
        
        # Summary
        summary = f"Top recommended resource is **{top_cand['employee_id']}** ({top_cand['job_name']}) with suitability score of **{top_cand['final_score'] * 100:.1f}%**. "
        if len(candidates) > 1:
            summary += f"We identified {len(candidates)} total matching candidate options."

        # Evidence
        evidence = []
        for c in candidates[:3]:
            evidence.append(f"**{c['employee_id']}** — Score: {c['final_score']*100:.1f}%, Availability: {c['availability_date']}, Match Skills: {', '.join(c['matching_skills'][:3])}")
        
        if rag_expl:
            evidence.append(f"\n*RAG Assessment*:\n{rag_expl}")

        # Risks
        risks = []
        for c in candidates[:2]:
            if c.get("utilization_percentage", 0) > 100:
                risks.append(f"{c['employee_id']} is currently overallocated at {c['utilization_percentage']}% utilization.")
        if health_data:
            risks.append(f"Target project health is currently {health_data.get('overall_health', 'Green')} (Risk score: {health_data.get('risk_score')}).")
        if not risks:
            risks.append("No active workload allocation overlaps detected.")

        # Recommendation
        recoms = [f"Allocate **{top_cand['employee_id']}** to the project starting {top_cand['availability_date']}."]
        if len(candidates) > 1:
            recoms.append(f"Consider **{candidates[1]['employee_id']}** as alternative fallback.")

        markdown = f"### Executive Summary\n\n{summary}\n\n"
        markdown += "### Supporting Evidence\n\n" + "\n".join([f"* {ev}" for ev in evidence]) + "\n\n"
        markdown += "### Risks\n\n" + "\n".join([f"* {rk}" for rk in risks]) + "\n\n"
        markdown += "### Recommendations\n\n" + "\n".join([f"1. {rec}" for rec in recoms]) + "\n\n"
        markdown += f"### Confidence\n\n**{top_cand.get('confidence', 'High')}**\n"
        return markdown

    def _build_health_response(self, params: Dict[str, Any], results: Dict[str, Any]) -> str:
        h_detail = results.get("project_health")
        h_list = results.get("projects_health_list", [])
        rampdowns = results.get("rampdown_candidates", [])

        if h_detail:
            pid = h_detail.get("project_id")
            health = h_detail.get("overall_health", "Green")
            risk_score = h_detail.get("risk_score", 0.0)
            
            # Summary
            summary = f"Project **{pid}** is in **{health}** health state (Risk Score: {risk_score}/100)."
            
            # Evidence
            evidence = [
                f"Schedule delay: {h_detail.get('schedule', {}).get('delay_days', 0)} days.",
                f"Resource utilization average: {h_detail.get('utilization', {}).get('average', 0.0)}%.",
                f"Billability: {h_detail.get('billability', {}).get('percentage', 100.0)}% ({h_detail.get('billability', {}).get('cost_recovery_status')} recovery)."
            ]
            if h_detail.get("explanation"):
                evidence.append(f"\n*Diagnostic report*:\n{h_detail['explanation']}")
                
            # Risks
            risks = []
            if health == "Red":
                risks.append("Critical threat to timeline execution. Urgent realignment required.")
            elif health == "Amber":
                risks.append("Minor delays and cost efficiency deviations observed.")
            else:
                risks.append("Stable delivery path.")
                
            # Recommendation
            recoms = h_detail.get("recommended_actions", ["Maintain current allocation pool."])
            
            markdown = f"### Executive Summary\n\n{summary}\n\n"
            markdown += "### Supporting Evidence\n\n" + "\n".join([f"* {ev}" for ev in evidence]) + "\n\n"
            markdown += "### Risks\n\n" + "\n".join([f"* {rk}" for rk in risks]) + "\n\n"
            markdown += "### Recommendations\n\n" + "\n".join([f"1. {rec}" for rec in recoms]) + "\n\n"
            markdown += f"### Confidence\n\n**High**\n"
            return markdown
            
        else:
            # Multi-project health status
            total_active = len(h_list)
            red_count = sum(1 for p in h_list if p.get("overall_health") == "Red")
            amber_count = sum(1 for p in h_list if p.get("overall_health") == "Amber")
            
            summary = f"Out of **{total_active}** active projects audited, **{red_count}** are at Critical Risk (Red) and **{amber_count}** are at Moderate Risk (Amber)."
            
            evidence = []
            for p in h_list:
                if p.get("overall_health") in ["Red", "Amber"]:
                    evidence.append(f"Project **{p['project_id']}** (Health: **{p['overall_health']}**, Risk: {p['risk_score']:.1f})")
            if not evidence:
                evidence.append("All active projects are operating within healthy metrics (Green).")
                
            risks = [f"Critical project issues in Red status threaten client delivery timelines and budget recovery."]
            
            recoms = []
            if red_count > 0:
                recoms.append("Trigger diagnostic health audit for all Red projects.")
            if rampdowns:
                recoms.append(f"Consider releasing resources from suitability candidates: " + ", ".join([rc["project_id"] for rc in rampdowns[:2]]))
                
            markdown = f"### Executive Summary\n\n{summary}\n\n"
            markdown += "### Supporting Evidence\n\n" + "\n".join([f"* {ev}" for ev in evidence]) + "\n\n"
            markdown += "### Risks\n\n" + "\n".join([f"* {rk}" for rk in risks]) + "\n\n"
            markdown += "### Recommendations\n\n" + "\n".join([f"1. {rec}" for rec in recoms]) + "\n\n"
            markdown += f"### Confidence\n\n**High**\n"
            return markdown

    def _build_pipeline_response(self, params: Dict[str, Any], results: Dict[str, Any]) -> str:
        pf = results.get("pipeline_forecast", {})
        projs = pf.get("monthly_projections", [])
        
        if not projs:
            return self._build_error_response("No pipeline projections could be generated.")
            
        # Summary
        summary = f"Six-month forecast predicts average employee utilization of **{pf.get('average_projected_utilization')}%**."
        
        # Evidence
        evidence = []
        for p in projs:
            evidence.append(f"Month **{p['month']}** — Projects: {p['expected_project_volume']}, Demand: {p['headcount_demand']} FTE, Util: {p['utilization_percentage']}%, Surplus: {p['capacity_surplus']} FTE, Deficit: {p['capacity_deficit']} FTE")
            
        # Risks
        risks = []
        deficit_months = [p["month"] for p in projs if p["capacity_deficit"] > 0]
        if deficit_months:
            risks.append(f"Headcount capacity deficits forecasted in months: {', '.join(deficit_months)}.")
        else:
            risks.append("None. Workforce capacity remains surplus across all horizons.")
            
        # Recommendation
        recoms = ["Maintain sales pipeline velocity."]
        if deficit_months:
            recoms.append("Initiate external hiring pipeline ahead of high-demand deficit periods.")
            
        markdown = f"### Executive Summary\n\n{summary}\n\n"
        markdown += "### Supporting Evidence\n\n" + "\n".join([f"* {ev}" for ev in evidence]) + "\n\n"
        markdown += "### Risks\n\n" + "\n".join([f"* {rk}" for rk in risks]) + "\n\n"
        markdown += "### Recommendations\n\n" + "\n".join([f"1. {rec}" for rec in recoms]) + "\n\n"
        markdown += f"### Confidence\n\n**{pf.get('confidence_score', 'Medium')}**\n"
        return markdown

    def _build_capacity_response(self, params: Dict[str, Any], results: Dict[str, Any]) -> str:
        cap = results.get("capacity", {})
        proj = cap.get("capacity_projections", {})
        details = cap.get("details", {})
        
        summary = f"Total available organization headcount today is **{proj.get('available_now', 0)} FTEs**, rising to **{proj.get('available_90_days', 0)} FTEs** in 90 days."
        
        evidence = []
        for role, breakdown in details.items():
            evidence.append(f"**{role.replace('_', ' ').title()}** — Now: {breakdown['available_now']} FTE, 30 days: {breakdown['available_30_days']} FTE, 90 days: {breakdown['available_90_days']} FTE")
            
        risks = []
        critical_roles = [r for r, b in details.items() if b["available_now"] == 0]
        if critical_roles:
            risks.append(f"Zero current availability for roles: {', '.join([c.replace('_', ' ').title() for c in critical_roles])}.")
        else:
            risks.append("None. Healthy reserves exist for all core skills.")
            
        recoms = ["Cross-train consultants on high-demand skills to balance bench pools."]
        
        markdown = f"### Executive Summary\n\n{summary}\n\n"
        markdown += "### Supporting Evidence\n\n" + "\n".join([f"* {ev}" for ev in evidence]) + "\n\n"
        markdown += "### Risks\n\n" + "\n".join([f"* {rk}" for rk in risks]) + "\n\n"
        markdown += "### Recommendations\n\n" + "\n".join([f"1. {rec}" for rec in recoms]) + "\n\n"
        markdown += f"### Confidence\n\n**High**\n"
        return markdown

    def _build_hiring_response(self, params: Dict[str, Any], results: Dict[str, Any]) -> str:
        h = results.get("hiring", {})
        needs = h.get("hiring_needs", [])
        
        summary = h.get("summary", "Hiring metrics compiled.")
        
        evidence = []
        for hn in needs:
            evidence.append(f"**{hn['role']}** (Priority: **{hn['priority']}**) — {hn['reason']}")
        if not evidence:
            evidence.append("No active capacity gaps indicating hiring demands.")
            
        risks = []
        high_priority = [hn["role"] for hn in needs if hn["priority"] in ["High", "Critical"]]
        if high_priority:
            risks.append(f"Critical gaps in {', '.join(high_priority)} might stall upcoming project kickoffs.")
        else:
            risks.append("Low risk.")
            
        recoms = [hn["reason"] for hn in needs]
        if not recoms:
            recoms = ["Reject external recruiting requests and leverage internal redeployment benches."]
            
        markdown = f"### Executive Summary\n\n{summary}\n\n"
        markdown += "### Supporting Evidence\n\n" + "\n".join([f"* {ev}" for ev in evidence]) + "\n\n"
        markdown += "### Risks\n\n" + "\n".join([f"* {rk}" for rk in risks]) + "\n\n"
        markdown += "### Recommendations\n\n" + "\n".join([f"1. {rec}" for rec in recoms]) + "\n\n"
        markdown += f"### Confidence\n\n**High**\n"
        return markdown

    def _build_redeploy_response(self, params: Dict[str, Any], results: Dict[str, Any]) -> str:
        r = results.get("redeployment", {})
        opts = r.get("redeployment_options", [])
        
        summary = r.get("summary", "Redeployment options analysis.")
        
        evidence = []
        for opt in opts[:3]:
            evidence.append(f"**{opt['employee_id']}** ({opt['role']}) — Current Project: {opt['current_project_id']} (ends {opt['project_end_date']}), Skill Match: {opt['match_score']*100:.0f}%")
        if not evidence:
            evidence.append("No redeployment candidates matched within timeframe.")
            
        risks = []
        if not opts:
            risks.append("Deficit cannot be mitigated internally. Risk of delivery delay unless external hires are initiated.")
        else:
            risks.append("Resource transitions depend on current projects ending on schedule without timeline extensions.")
            
        recoms = [f"Redeploy {opt['employee_id']} after project completes" for opt in opts[:2]]
        
        markdown = f"### Executive Summary\n\n{summary}\n\n"
        markdown += "### Supporting Evidence\n\n" + "\n".join([f"* {ev}" for ev in evidence]) + "\n\n"
        markdown += "### Risks\n\n" + "\n".join([f"* {rk}" for rk in risks]) + "\n\n"
        markdown += "### Recommendations\n\n" + "\n".join([f"1. {rec}" for rec in recoms]) + "\n\n"
        markdown += f"### Confidence\n\n**High**\n"
        return markdown

    def _build_employee_search_response(self, params: Dict[str, Any], results: Dict[str, Any]) -> str:
        search = results.get("search_results", [])
        rec = results.get("recommendations", {})
        recs = rec.get("recommendations", [])
        
        summary = f"Semantic search matched **{len(search)}** candidates in the vector database."
        
        evidence = []
        for item in search[:3]:
            payload = item.get("payload", {})
            evidence.append(f"**{payload.get('employee_id')}** — Job: {payload.get('job_name')}, Location: {payload.get('location')}, Score: {item.get('score', 0.0):.3f}")
            
        risks = ["Matching profiles based on semantic search score alone does not validate project schedule availability."]
        
        recoms = []
        if recs:
            recoms.append(f"Top matching available candidate ranked by recommendation rules is: **{recs[0]['employee_id']}** (Score: {recs[0]['final_score']*100:.1f}%).")
            
        markdown = f"### Executive Summary\n\n{summary}\n\n"
        markdown += "### Supporting Evidence\n\n" + "\n".join([f"* {ev}" for ev in evidence]) + "\n\n"
        markdown += "### Risks\n\n" + "\n".join([f"* {rk}" for rk in risks]) + "\n\n"
        markdown += "### Recommendations\n\n" + "\n".join([f"1. {rec}" for rec in recoms]) + "\n\n"
        markdown += f"### Confidence\n\n**High**\n"
        return markdown

    def _build_project_search_response(self, params: Dict[str, Any], results: Dict[str, Any]) -> str:
        search = results.get("search_results", [])
        
        summary = f"Identified **{len(search)}** matching historical projects in database."
        
        evidence = []
        for item in search[:3]:
            payload = item.get("payload", {})
            evidence.append(f"Project **{payload.get('project_id')}** — Type: {payload.get('type_of_project')}, Tech: {payload.get('tech_coe')}, Score: {item.get('score', 0.0):.3f}")
            
        risks = ["Semantic mapping matches metadata description and may show minor variations in actual staff mix execution."]
        
        recoms = ["Reference the historical staffing mix of matched projects as the starting blueprint."]
        
        markdown = f"### Executive Summary\n\n{summary}\n\n"
        markdown += "### Supporting Evidence\n\n" + "\n".join([f"* {ev}" for ev in evidence]) + "\n\n"
        markdown += "### Risks\n\n" + "\n".join([f"* {rk}" for rk in risks]) + "\n\n"
        markdown += "### Recommendations\n\n" + "\n".join([f"1. {rec}" for rec in recoms]) + "\n\n"
        markdown += f"### Confidence\n\n**High**\n"
        return markdown

    def _build_general_qa_response(self, params: Dict[str, Any], results: Dict[str, Any]) -> str:
        ans = results.get("rag_result", "I'm sorry, I could not query RAG to answer your question.")
        
        markdown = f"### Executive Summary\n\n{ans}\n\n"
        markdown += "### Supporting Evidence\n\n* Retrieved matching semantic contexts from the RAG database.\n\n"
        markdown += "### Recommendations\n\n1. Let me know if you would like me to retrieve specific details about any employee or project listed above.\n\n"
        markdown += "### Confidence\n\n**High**\n"
        return markdown

    def _build_error_response(self, message: str) -> str:
        markdown = f"### Executive Summary\n\n{message}\n\n"
        markdown += "### Supporting Evidence\n\n* Backend service query error logs.\n\n"
        markdown += "### Recommendations\n\n1. Verify if the database is seeded and the services are online.\n\n"
        markdown += "### Confidence\n\n**Low**\n"
        return markdown
