from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RecommendationRequest(BaseModel):
    project_id: Optional[str] = Field(None, description="Masked Project ID requesting resources.")
    required_skills: List[str] = Field(..., description="Mandatory list of skills needed for project (e.g. Python, SQL).")
    project_type: Optional[str] = Field("AI", description="Type or CoE of the project (e.g. AI, Data Engineering).")
    required_competencies: Optional[List[str]] = Field(default_factory=list, description="Target competency fields (e.g. Communication Skills, Stakeholder Management).")
    project_start_date: Optional[str] = Field("2026-08-01", description="Target start date formatted as YYYY-MM-DD.")
    top_n: int = Field(10, ge=1, le=50, description="Number of top candidates to return.")
    strategy: Optional[str] = Field("hybrid_v1", description="Recommendation strategy algorithm to use.")
    
    # Redesigned and Connected Filters
    department: Optional[str] = Field("all", description="Filter by department name.")
    experience_range: Optional[str] = Field("all", description="Filter by experience years (junior, mid, senior, all).")
    availability_window: Optional[str] = Field("all", description="Filter by business-focused availability window.")
    location: Optional[str] = Field("all", description="Filter by employee location.")
    technology: Optional[str] = Field(None, description="Filter by project technology / solution.")
    domain: Optional[str] = Field(None, description="Filter by project industry domain / cluster.")

class CandidateRecommendation(BaseModel):
    employee_id: str
    name: str
    email: str
    job_name: str
    department_name: str
    location: str
    experience_years: float
    skills: List[str]
    competencies: List[str]
    matching_skills: List[str]
    current_allocation: float
    utilization_percentage: float
    availability_date: str
    current_project: Optional[str] = None
    final_score: float
    rank: int
    confidence: Optional[str] = "Medium"
    why_recommended: str
    strengths: List[str]
    potential_risks: List[str]
    
    # Detailed scoring breakdown
    skill_match: float
    competency_match: float
    experience_score: float
    availability_score: float
    historical_score: float
    semantic_score: float
    
    # Backwards compatibility fields
    category_scores: Dict[str, float]
    strategy_scores: Optional[Dict[str, float]] = None

class ProjectDetail(BaseModel):
    project_id: str
    name: str
    client: str
    technology: Optional[str] = None
    domain: Optional[str] = None
    required_skills: List[str]
    project_type: str
    expected_start_date: str
    demand: str

class RecommendationResponse(BaseModel):
    project: Optional[ProjectDetail] = None
    summary: Optional[str] = None
    candidates: List[CandidateRecommendation] = Field(default_factory=list)
    recommendations: List[CandidateRecommendation] = Field(default_factory=list) # Backwards compatibility
    explanation: str
    confidence: Optional[str] = "Medium"
    processing_time_ms: float
    model_version: str = "v1"

class BenchmarkResponse(BaseModel):
    benchmark_results: Dict[str, List[CandidateRecommendation]]
    evaluation_metrics: Dict[str, Dict[str, Any]]
    processing_time_ms: float

class PipelineOpportunity(BaseModel):
    id: str
    project_name: str
    client: str
    technology: str
    domain: str
    required_skills: List[str]
    start_date: str
    team_size: str
    status: str
    project_type: str
