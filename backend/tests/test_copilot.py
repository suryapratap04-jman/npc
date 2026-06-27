import os
import sys
from pathlib import Path

# Enable absolute path imports for the backend directory
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.session import SessionLocal
from backend.copilot.conversation_memory import ConversationMemory
from backend.copilot.intent_classifier import IntentClassifier
from backend.copilot.response_builder import ResponseBuilder
from backend.copilot.planner import Planner
from backend.copilot.tool_registry import ToolRegistry
from backend.copilot.service import CopilotService
from backend.copilot.schemas import CopilotChatRequest, CopilotExplainRequest

def test_intent_classification():
    """Verifies queries classify to the correct operational intents."""
    classifier = IntentClassifier()
    context = {}

    # Test Resource Recommendation intent
    c1 = classifier.classify_intent("Who should be assigned to Project CLIENT_201_005?", context)
    assert c1["intent"] == "RESOURCE_RECOMMENDATION"
    assert c1["parameters"]["project_id"] == "CLIENT_201_005"

    # Test Project Health intent
    c2 = classifier.classify_intent("Show me projects at risk", context)
    assert c2["intent"] == "PROJECT_HEALTH"

    # Test New Project Forecast intent
    c3 = classifier.classify_intent("Can we take on three new AI projects next month?", context)
    assert c3["intent"] == "NEW_PROJECT_FORECAST"
    assert "AI" in c3["parameters"]["project_type"]

    # Test Hiring intent
    c4 = classifier.classify_intent("Should we hire or redeploy for a backend engineer?", context)
    assert c4["intent"] == "HIRING"
    assert c4["parameters"]["role"] == "backend"

    print("[OK] Intent classification tests passed.")

def test_conversation_memory():
    """Asserts conversation memory logs chat events and extracts referenced entity IDs."""
    mem = ConversationMemory()
    session_id = "test-session-123"

    # Add query referencing Project ID
    mem.add_message(session_id, "user", "Recommend engineers for Project CLIENT_201_005")
    context = mem.get_context(session_id)
    assert context["last_project_id"] == "CLIENT_201_005"

    # Add follow-up referencing Employee ID
    mem.add_message(session_id, "user", "Why was EMP1001 recommended?")
    context = mem.get_context(session_id)
    assert context["last_employee_id"] == "EMP1001"
    
    # Verify history maintains sequence
    history = mem.get_history(session_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"

    print("[OK] Conversation memory entity tracking tests passed.")

def test_planner_workflows():
    """Asserts planner aggregates sequential tool execution blocks for multi-tool intents."""
    db = SessionLocal()
    try:
        registry = ToolRegistry(db)
        planner = Planner()
        
        # Test Workflow B (NEW_PROJECT_FORECAST)
        params = {"project_type": "AI", "required_skills": ["Python"], "expected_duration_months": 6}
        results, tools = planner.execute_plan("NEW_PROJECT_FORECAST", params, registry)
        
        assert "forecast" in results
        assert "capacity" in results
        assert "hiring" in results
        assert "redeployment" in results
        assert "get_new_project_forecast" in tools
        
        print("[OK] Planner multi-tool workflow execution tests passed.")
    finally:
        db.close()

def test_response_builder():
    """Asserts markdown output is parsed and compiled into standard executive categories."""
    builder = ResponseBuilder()
    
    dummy_results = {
        "forecast": {
            "project_type": "AI",
            "team_recommendation": {"backend": 1, "data_scientist": 1},
            "estimated_fte": 2.0,
            "estimated_cost": 24000.0,
            "expected_duration": 6,
            "confidence": "High",
            "source": "Fallback"
        },
        "capacity": {
            "capacity_projections": {"available_now": 5, "available_30_days": 10}
        },
        "redeployment": {"redeployment_options": []},
        "hiring": {"hiring_needs": []}
    }
    
    params = {"project_type": "AI", "expected_duration_months": 6}
    response = builder.build_response("NEW_PROJECT_FORECAST", params, dummy_results)
    
    assert "### Executive Summary" in response
    assert "### Supporting Evidence" in response
    assert "### Risks" in response
    assert "### Recommendations" in response
    assert "### Confidence" in response
    
    print("[OK] Response builder formatting tests passed.")

def test_metrics_evaluation_logging():
    """Asserts that running the Copilot updates experiments/copilot_metrics.csv."""
    project_root = Path(__file__).parent.parent.parent
    csv_path = project_root / "experiments" / "copilot_metrics.csv"
    
    if csv_path.exists():
        os.remove(csv_path)
        
    db = SessionLocal()
    try:
        service = CopilotService(db)
        req = CopilotChatRequest(
            message="Show available capacity today",
            session_id="eval-session"
        )
        service.chat(req)
        
        assert csv_path.exists(), "experiments/copilot_metrics.csv was not created."
        with open(csv_path, mode="r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) >= 2, "experiments/copilot_metrics.csv is empty."
            
        print("[OK] CSV Copilot metrics logging test passed.")
    finally:
        db.close()

if __name__ == "__main__":
    test_intent_classification()
    test_conversation_memory()
    test_planner_workflows()
    test_response_builder()
    test_metrics_evaluation_logging()
