import hashlib
import json
from typing import Any

# Namespace prefixes
NS_RECOMMENDATION = "recommendation"
NS_DASHBOARD = "dashboard"
NS_FORECAST = "forecast"
NS_HEALTH = "health"
NS_EMBEDDING = "embedding"
NS_SEARCH = "search"
NS_EMPLOYEE = "employee"
NS_PROJECT = "project"
NS_COPILOT = "copilot"

def generate_payload_hash(payload: Any) -> str:
    """Generates a deterministic SHA256 hex digest for a JSON-serializable payload."""
    if payload is None:
        return "none"
    
    # Sort keys to ensure determinism across similar requests
    if isinstance(payload, (dict, list)):
        payload_str = json.dumps(payload, sort_keys=True, default=str)
    else:
        payload_str = str(payload)
        
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

def make_recommendation_key(payload: Any) -> str:
    """Key format: recommendation:SHA256"""
    return f"{NS_RECOMMENDATION}:{generate_payload_hash(payload)}"

def make_dashboard_key(key_suffix: str) -> str:
    """Key format: dashboard:kpis, dashboard:charts, etc."""
    return f"{NS_DASHBOARD}:{key_suffix}"

def make_forecast_key(payload: Any) -> str:
    """Key format: forecast:SHA256"""
    return f"{NS_FORECAST}:{generate_payload_hash(payload)}"

def make_health_key(project_id: str = "all") -> str:
    """Key format: health:project_id"""
    return f"{NS_HEALTH}:{project_id}"

def make_embedding_key(text: str) -> str:
    """Key format: embedding:text_hash"""
    clean_text = text.strip().lower()
    text_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
    return f"{NS_EMBEDDING}:{text_hash}"

def make_search_key(category: str, query: str, limit: int) -> str:
    """Key format: search:category:query_hash:limit"""
    query_hash = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()
    return f"{NS_SEARCH}:{category}:{query_hash}:{limit}"

def make_employee_profile_key(employee_id: str) -> str:
    """Key format: employee:employee_id"""
    return f"{NS_EMPLOYEE}:{employee_id}"

def make_project_profile_key(project_id: str) -> str:
    """Key format: project:project_id"""
    return f"{NS_PROJECT}:{project_id}"

def make_copilot_session_key(session_id: str, key_suffix: str) -> str:
    """Key format: copilot:session_id:key_suffix"""
    return f"{NS_COPILOT}:{session_id}:{key_suffix}"
