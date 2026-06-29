from backend.cache.redis_client import verify_redis_connection, get_redis_client
from backend.cache.cache_service import (
    cache_service,
    TTL_RECOMMENDATION,
    TTL_DASHBOARD,
    TTL_FORECAST,
    TTL_HEALTH,
    TTL_EMBEDDING,
    TTL_SEARCH,
    TTL_EMPLOYEE,
    TTL_PROJECT,
    TTL_COPILOT_SESSION
)
from backend.cache.cache_keys import (
    NS_RECOMMENDATION,
    NS_DASHBOARD,
    NS_FORECAST,
    NS_HEALTH,
    NS_EMBEDDING,
    NS_SEARCH,
    NS_EMPLOYEE,
    NS_PROJECT,
    NS_COPILOT,
    make_recommendation_key,
    make_dashboard_key,
    make_forecast_key,
    make_health_key,
    make_embedding_key,
    make_search_key,
    make_employee_profile_key,
    make_project_profile_key,
    make_copilot_session_key
)
from backend.cache.decorators import cache
