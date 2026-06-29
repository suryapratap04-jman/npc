import pytest
from sqlalchemy.orm import Session

from backend.cache.cache_service import cache_service
from backend.cache.cache_keys import NS_RECOMMENDATION, NS_DASHBOARD, NS_SEARCH, NS_EMPLOYEE, NS_PROJECT
from backend.database.models import Employee, Project, Skill
from backend.database.session import SessionLocal
import backend.database.events


def test_cache_set_get_delete():
    # Test setting and getting values
    key = "test_ns:key1"
    val = {"data": [1, 2, 3], "status": "active"}
    
    assert cache_service.set(key, val, ttl_seconds=60) is True
    assert cache_service.get(key) == val
    
    # Test deleting
    assert cache_service.delete(key) is True
    assert cache_service.get(key) is None

def test_namespace_invalidation():
    # Set multiple keys in namespace
    cache_service.set("dashboard:kpi1", 100, 60)
    cache_service.set("dashboard:kpi2", 200, 60)
    cache_service.set("recommendation:payload1", {"items": []}, 60)
    
    assert cache_service.get("dashboard:kpi1") == 100
    assert cache_service.get("dashboard:kpi2") == 200
    assert cache_service.get("recommendation:payload1") == {"items": []}
    
    # Invalidate dashboard namespace
    invalidated_count = cache_service.invalidate_namespace("dashboard")
    assert invalidated_count >= 2
    
    assert cache_service.get("dashboard:kpi1") is None
    assert cache_service.get("dashboard:kpi2") is None
    assert cache_service.get("recommendation:payload1") is not None
    
    # Clean up recommendation key
    cache_service.delete("recommendation:payload1")

def test_db_event_triggered_invalidation():
    db: Session = SessionLocal()
    
    # Pre-populate some dummy entries in cache namespaces
    cache_service.set("recommendation:dummy", "rec_data", 60)
    cache_service.set("dashboard:dummy", "dash_data", 60)
    cache_service.set("employee:dummy", "emp_data", 60)
    
    assert cache_service.get("recommendation:dummy") == "rec_data"
    assert cache_service.get("dashboard:dummy") == "dash_data"
    assert cache_service.get("employee:dummy") == "emp_data"
    
    # Trigger db write by inserting a temporary skill or modifying an employee
    # Since we don't want to pollute production DB, let's insert a temp skill with employee_id = 'NON_EXISTENT_TEMP_ID' and rollback
    try:
        temp_emp = Employee(
            employee_id="TEMP_TEST_101",
            job_name="Staff Engineer",
            department_name="Data Science",
            is_active_version=1
        )
        db.add(temp_emp)
        db.flush()
        db.commit()
    except Exception:
        db.rollback()
        
    # Relational write triggers employee change listeners, which invalidates NS_RECOMMENDATION, NS_DASHBOARD, NS_SEARCH, NS_EMPLOYEE
    assert cache_service.get("recommendation:dummy") is None
    assert cache_service.get("dashboard:dummy") is None
    assert cache_service.get("employee:dummy") is None
    
    # Clean up DB
    try:
        emp_in_db = db.query(Employee).filter(Employee.employee_id == "TEMP_TEST_101").first()
        if emp_in_db:
            db.delete(emp_in_db)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
