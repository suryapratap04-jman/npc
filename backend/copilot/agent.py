import logging
from typing import Dict, List, Any, Optional, Tuple

from backend.copilot.conversation_memory import ConversationMemory
from backend.copilot.intent_classifier import IntentClassifier

logger = logging.getLogger("copilot_agent")

class CopilotAgent:
    def __init__(self, memory: ConversationMemory, classifier: IntentClassifier):
        self.memory = memory
        self.classifier = classifier

    def process_message(self, 
                        session_id: str, 
                        message: str) -> Tuple[str, Dict[str, Any], float]:
        """
        Interprets the conversational request, fetches entity memory context,
        and triggers intent classification.
        """
        # Load context from memory
        context = self.memory.get_context(session_id)
        
        # Classify intent
        classification = self.classifier.classify_intent(message, context)
        intent = classification["intent"]
        confidence = classification["confidence"]
        params = classification["parameters"]
        
        logger.info(f"Agent classified intent: '{intent}' (Confidence: {confidence:.2f}) for session '{session_id}'")
        
        return intent, params, confidence
