import time
import logging
from typing import Dict, List, Any, Tuple

from backend.copilot.conversation_memory import ConversationMemory
from backend.copilot.agent import CopilotAgent
from backend.copilot.planner import Planner
from backend.copilot.tool_registry import ToolRegistry
from backend.copilot.response_builder import ResponseBuilder
from backend.copilot.prompt_templates import SUGGESTED_QUESTIONS_CATALOG

logger = logging.getLogger("copilot_orchestrator")

class CopilotOrchestrator:
    def __init__(self, 
                 agent: CopilotAgent, 
                 planner: Planner, 
                 response_builder: ResponseBuilder,
                 tool_registry: ToolRegistry,
                 memory: ConversationMemory):
        self.agent = agent
        self.planner = planner
        self.response_builder = response_builder
        self.tool_registry = tool_registry
        self.memory = memory

    def execute_query(self, 
                      session_id: str, 
                      message: str) -> Tuple[Dict[str, Any], float]:
        """
        Coordinates intent classification, tool execution, response rendering, 
        and updates conversation memory state. Returns the response details and latency.
        """
        start_time = time.time()
        
        # 1. Store user message in history
        self.memory.add_message(session_id, "user", message)
        
        # 2. Agent classifies query and pulls entity context
        intent, params, confidence = self.agent.process_message(session_id, message)
        
        # 3. Planner formulates tool steps and executes them
        aggregated_results, executed_tools = self.planner.execute_plan(
            intent=intent,
            parameters=params,
            registry=self.tool_registry
        )
        
        # 4. Formulate markdown executive response
        response_text = self.response_builder.build_response(
            intent=intent,
            parameters=params,
            aggregated_results=aggregated_results
        )
        
        # 5. Store assistant message in history
        self.memory.add_message(session_id, "assistant", response_text)
        
        # Update context based on execution results
        # If recommendation search was done, save list to context
        if "recommendations" in aggregated_results:
            recs = aggregated_results["recommendations"].get("recommendations", [])
            if recs:
                self.memory.update_context(session_id, "last_recommendations", [c["employee_id"] for c in recs])
                self.memory.update_context(session_id, "last_employee_id", recs[0]["employee_id"])

        # 6. Retrieve suggested follow-up questions matching intent (Step 8)
        suggested = SUGGESTED_QUESTIONS_CATALOG.get(intent, SUGGESTED_QUESTIONS_CATALOG["GENERAL_QA"])
        
        elapsed_ms = (time.time() - start_time) * 1000.0
        
        output = {
            "response": response_text,
            "detected_intent": intent,
            "intent_confidence": confidence,
            "suggested_questions": suggested,
            "executed_tools": executed_tools
        }
        
        return output, elapsed_ms
