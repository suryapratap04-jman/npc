from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ProjectHealthSummary(BaseModel):
    project_id: str
    project_key: Optional[str] = None
    overall_health: str  # Green, Amber, Red
    risk_score: float
    risk_level: str      # Low, Medium, High, Critical

class ScheduleHealth(BaseModel):
    status: str          # Green, Amber, Red
    delay_days: int
    days_remaining: int
    planned_duration: int
    actual_duration: int
    extension_count: int

class UtilizationHealth(BaseModel):
    average: float
    peak: float
    overallocated_count: int
    underutilized_count: int
    idle_capacity_percentage: float
    releasable_capacity_percentage: float

class BillabilityHealth(BaseModel):
    percentage: float
    billable_hours: float
    non_billable_hours: float
    shadow_resources_count: int
    billability_trend: str  # Improving, Stable, Declining
    cost_recovery_status: str  # Good, Degraded, Poor

class RampDownDetail(BaseModel):
    project_id: str
    is_suitable: bool
    estimated_release_count: int
    earliest_release_date: Optional[str] = None
    skills_released: List[str]

class ProjectHealthDetail(BaseModel):
    project_id: str
    overall_health: str
    risk_score: float
    risk_level: str
    schedule: ScheduleHealth
    utilization: UtilizationHealth
    billability: BillabilityHealth
    recommended_actions: List[str]
    explanation: Optional[str] = None

class ProjectHealthAnalysisRequest(BaseModel):
    project_id: str
