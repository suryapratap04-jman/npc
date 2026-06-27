import logging
import re
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("intent_classifier")

PROJECT_ID_PATTERN = re.compile(r'\b(CLIENT_\d+_\d+)\b', re.IGNORECASE)
EMPLOYEE_ID_PATTERN = re.compile(r'\b(EMP-?\d+)\b', re.IGNORECASE)

class IntentClassifier:
    def __init__(self):
        pass

    def classify_intent(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies user intent, computes a confidence score, and extracts necessary parameters,
        falling back to conversation context when parameters are missing.
        """
        msg_lower = message.lower()
        
        intent = "GENERAL_QA"
        confidence = 0.8
        
        # Rule-based classification
        if any(kw in msg_lower for kw in ["recommend", "assign", "staff", "who should be assigned", "who should work", "allocate"]):
            intent = "RESOURCE_RECOMMENDATION"
            confidence = 0.95
        elif any(kw in msg_lower for kw in ["health", "risk", "status", "at risk", "audit"]):
            intent = "PROJECT_HEALTH"
            confidence = 0.95
        elif any(kw in msg_lower for kw in ["can we take", "new project", "take on"]):
            intent = "NEW_PROJECT_FORECAST"
            confidence = 0.90
        elif any(kw in msg_lower for kw in ["six-month", "6-month", "pipeline forecast", "monthly projections", "project volume"]):
            intent = "PIPELINE_FORECAST"
            confidence = 0.90
        elif any(kw in msg_lower for kw in ["hire", "hiring", "recruit", "external hire"]):
            intent = "HIRING"
            confidence = 0.95
        elif any(kw in msg_lower for kw in ["redeploy", "redeployment", "transfer", "transition", "release"]):
            intent = "REDEPLOYMENT"
            confidence = 0.95
        elif any(kw in msg_lower for kw in ["capacity", "available", "bench", "utilization", "idle"]):
            intent = "CAPACITY"
            confidence = 0.90
        elif any(kw in msg_lower for kw in ["who knows", "who has skill", "search employee", "find employee"]):
            intent = "EMPLOYEE_SEARCH"
            confidence = 0.90
        elif any(kw in msg_lower for kw in ["find project", "search project", "similar project"]):
            intent = "PROJECT_SEARCH"
            confidence = 0.90
        elif any(kw in msg_lower for kw in ["why", "explain", "reason"]):
            # Contextual intent check
            if context.get("last_project_id") and context.get("last_employee_id"):
                intent = "RESOURCE_RECOMMENDATION"
                confidence = 0.85
            else:
                intent = "GENERAL_QA"
                confidence = 0.75

        # Parameter Extraction
        params = {}
        
        # 1. Project ID
        proj_match = PROJECT_ID_PATTERN.search(message)
        if proj_match:
            params["project_id"] = proj_match.group(1).upper()
        elif context.get("last_project_id"):
            params["project_id"] = context.get("last_project_id")
            
        # 2. Employee ID
        emp_match = EMPLOYEE_ID_PATTERN.search(message)
        if emp_match:
            params["employee_id"] = emp_match.group(1).upper()
        elif context.get("last_employee_id"):
            params["employee_id"] = context.get("last_employee_id")

        # 3. Skills extraction
        common_skills = ["python", "azure", "aws", "gcp", "spark", "pyspark", "databricks", "snowflake", "react", "sql", "fastapi", "llm", "ai", "qa", "devops", "kubernetes", "docker"]
        extracted_skills = []
        for s in common_skills:
            if s in msg_lower:
                extracted_skills.append(s.title() if s != "llm" and s != "sql" and s != "ai" and s != "qa" and s != "aws" and s != "gcp" else s.upper())
        params["required_skills"] = extracted_skills
        
        # 4. Target Role
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
        params["role"] = None
        for kw, role_key in roles_keywords.items():
            if kw in msg_lower:
                params["role"] = role_key
                break
        if not params["role"] and context.get("last_role"):
            params["role"] = context.get("last_role")
            
        # 5. Extract Project Type
        if "ai" in msg_lower or "llm" in msg_lower or "ml" in msg_lower:
            params["project_type"] = "AI"
        elif "data" in msg_lower or "spark" in msg_lower:
            params["project_type"] = "Data Engineering"
        elif "bi" in msg_lower or "report" in msg_lower:
            params["project_type"] = "BI"
        else:
            params["project_type"] = "Client Project"
            
        # 6. Expected Duration (extract digit near duration keyword)
        duration_match = re.search(r'(\d+)\s*month', msg_lower)
        if duration_match:
            params["expected_duration_months"] = int(duration_match.group(1))
        else:
            params["expected_duration_months"] = 6 # default
            
        # 7. Horizon Offset
        if "90 days" in msg_lower or "3 months" in msg_lower:
            params["horizon_days"] = 90
        elif "60 days" in msg_lower or "2 months" in msg_lower:
            params["horizon_days"] = 60
        elif "30 days" in msg_lower or "next month" in msg_lower:
            params["horizon_days"] = 30
        else:
            params["horizon_days"] = 0

        return {
            "intent": intent,
            "confidence": confidence,
            "parameters": params
        }
