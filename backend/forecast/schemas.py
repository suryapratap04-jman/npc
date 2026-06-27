from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class NewProjectDemandRequest(BaseModel):
    project_type: str = Field(..., description="Project type (e.g., AI, Data Engineering, BI)")
    expected_duration_months: int = Field(..., description="Duration of the project in months")
    required_skills: List[str] = Field(default=[], description="List of required skills")
    expected_start_date: str = Field(..., description="Expected start date in YYYY-MM-DD format")
    expected_team_size: Optional[int] = Field(default=None, description="Optional target team size")

class TeamRecommendation(BaseModel):
    architect: int = Field(default=0)
    consultant: int = Field(default=0)
    backend: int = Field(default=0)
    frontend: int = Field(default=0)
    data_engineer: int = Field(default=0)
    data_scientist: int = Field(default=0)
    qa: int = Field(default=0)
    devops: int = Field(default=0)

class ActionableRecommendations(BaseModel):
    redeploy: List[str] = Field(default=[], description="List of specific redeployment recommendations")
    hire: List[str] = Field(default=[], description="List of specific external hiring requirements")

class CapacityProjections(BaseModel):
    available_now: int = Field(default=0)
    available_30_days: int = Field(default=0)
    available_60_days: int = Field(default=0)
    available_90_days: int = Field(default=0)

class NewProjectForecastResponse(BaseModel):
    project_type: str
    team_recommendation: Dict[str, int]
    estimated_fte: float
    estimated_cost: float
    expected_duration: int
    capacity: CapacityProjections
    recommendation: ActionableRecommendations
    confidence: str
    explanation: Optional[str] = None

class MonthlyProjection(BaseModel):
    month: str  # YYYY-MM
    expected_project_volume: int
    headcount_demand: float
    skill_demand: Dict[str, int]
    utilization_percentage: float
    capacity_surplus: int
    capacity_deficit: int

class SixMonthForecastResponse(BaseModel):
    monthly_projections: List[MonthlyProjection]
    average_projected_utilization: float
    total_capacity_surplus: int
    total_capacity_deficit: int
    confidence_score: str

class CapacityStatusResponse(BaseModel):
    capacity_projections: CapacityProjections
    available_employees_by_role: Dict[str, List[str]]  # role -> list of employee_ids
    details: Dict[str, Any]

class HiringNeed(BaseModel):
    role: str
    count_needed: int
    priority: str  # High, Medium, Low
    reason: str

class HiringResponse(BaseModel):
    hiring_needs: List[HiringNeed]
    summary: str

class RedeploymentOption(BaseModel):
    employee_id: str
    name: Optional[str] = None
    role: str
    current_project_id: Optional[str] = None
    project_end_date: Optional[str] = None
    available_from: str
    match_score: float

class RedeploymentResponse(BaseModel):
    redeployment_options: List[RedeploymentOption]
    summary: str
