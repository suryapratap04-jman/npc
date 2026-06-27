import time
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("conversation_memory")

PROJECT_ID_REGEX = re.compile(r'\b(CLIENT_\d+_\d+)\b', re.IGNORECASE)
EMPLOYEE_ID_REGEX = re.compile(r'\b(EMP-?\d+)\b', re.IGNORECASE)

class ConversationMemory:
    def __init__(self):
        # session_id -> list of message dicts
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
        # session_id -> dict of parsed contextual variables
        self.contexts: Dict[str, Dict[str, Any]] = {}

    def add_message(self, session_id: str, role: str, content: str):
        """Adds a message to the session memory and extracts context entities."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            self.contexts[session_id] = {
                "last_project_id": None,
                "last_employee_id": None,
                "last_role": None,
                "last_recommendations": []
            }

        self.sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        
        # Keep memory to last 20 messages to prevent context length bloat
        if len(self.sessions[session_id]) > 20:
            self.sessions[session_id] = self.sessions[session_id][-20:]

        # Extract entities from the user query and assistant response
        self._extract_entities(session_id, content)

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns session message log history."""
        return self.sessions.get(session_id, [])

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Returns extracted contextual variables for the session."""
        return self.contexts.get(session_id, {
            "last_project_id": None,
            "last_employee_id": None,
            "last_role": None,
            "last_recommendations": []
        })

    def update_context(self, session_id: str, key: str, value: Any):
        """Updates specific context parameter in session."""
        if session_id not in self.contexts:
            self.contexts[session_id] = {
                "last_project_id": None,
                "last_employee_id": None,
                "last_role": None,
                "last_recommendations": []
            }
        self.contexts[session_id][key] = value

    def _extract_entities(self, session_id: str, text: str):
        """Parses message text to log mentioned Project IDs or Employee IDs."""
        context = self.contexts[session_id]
        
        # 1. Project ID
        project_matches = PROJECT_ID_REGEX.findall(text)
        if project_matches:
            # save the latest match
            context["last_project_id"] = project_matches[-1].upper()
            logger.info(f"Extracted Project ID from session {session_id}: {context['last_project_id']}")
            
        # 2. Employee ID
        employee_matches = EMPLOYEE_ID_REGEX.findall(text)
        if employee_matches:
            context["last_employee_id"] = employee_matches[-1].upper()
            logger.info(f"Extracted Employee ID from session {session_id}: {context['last_employee_id']}")

        # 3. Mapped standard roles keywords
        roles_keywords = {
            "architect": "architect",
            "consultant": "consultant",
            "backend": "backend",
            "frontend": "frontend",
            "data engineer": "data_engineer",
            "data scientist": "data_scientist",
            "qa": "qa",
            "devops": "devops"
        }
        for kw, role_key in roles_keywords.items():
            if kw in text.lower():
                context["last_role"] = role_key
                break
