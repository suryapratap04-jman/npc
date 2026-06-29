import logging
from sqlalchemy import event
from backend.database.models import Employee, Project, Skill, Competency, Allocation, Timesheet, WeeklyStatus, Pipeline
from backend.cache.cache_service import cache_service
from backend.cache.cache_keys import NS_RECOMMENDATION, NS_DASHBOARD, NS_FORECAST, NS_HEALTH, NS_SEARCH, NS_EMPLOYEE, NS_PROJECT

logger = logging.getLogger("db_events")

def invalidate_employee_related_cache(mapper, connection, target):
    logger.info(f"Database event: Invalidation triggered on namespace recommendation, dashboard, search, employee by model {target.__class__.__name__}")
    cache_service.invalidate_namespace(NS_RECOMMENDATION)
    cache_service.invalidate_namespace(NS_DASHBOARD)
    cache_service.invalidate_namespace(NS_SEARCH)
    cache_service.invalidate_namespace(NS_EMPLOYEE)

def invalidate_project_related_cache(mapper, connection, target):
    logger.info(f"Database event: Invalidation triggered on namespace dashboard, health, project, search by model {target.__class__.__name__}")
    cache_service.invalidate_namespace(NS_DASHBOARD)
    cache_service.invalidate_namespace(NS_HEALTH)
    cache_service.invalidate_namespace(NS_PROJECT)
    cache_service.invalidate_namespace(NS_SEARCH)

def invalidate_pipeline_related_cache(mapper, connection, target):
    logger.info(f"Database event: Invalidation triggered on namespace recommendation, forecast, pipeline by model {target.__class__.__name__}")
    cache_service.invalidate_namespace(NS_RECOMMENDATION)
    cache_service.invalidate_namespace(NS_FORECAST)
    cache_service.invalidate_namespace("pipeline")

# Register listeners for Employee-related models
employee_models = [Employee, Skill, Competency, Allocation]
for model in employee_models:
    event.listen(model, 'after_insert', invalidate_employee_related_cache)
    event.listen(model, 'after_update', invalidate_employee_related_cache)
    event.listen(model, 'after_delete', invalidate_employee_related_cache)

# Register listeners for Project-related models
project_models = [Project, WeeklyStatus, Timesheet]
for model in project_models:
    event.listen(model, 'after_insert', invalidate_project_related_cache)
    event.listen(model, 'after_update', invalidate_project_related_cache)
    event.listen(model, 'after_delete', invalidate_project_related_cache)

# Register listeners for Pipeline-related models
pipeline_models = [Pipeline]
for model in pipeline_models:
    event.listen(model, 'after_insert', invalidate_pipeline_related_cache)
    event.listen(model, 'after_update', invalidate_pipeline_related_cache)
    event.listen(model, 'after_delete', invalidate_pipeline_related_cache)

logger.info("SQLAlchemy event listeners registered for cache invalidation.")
