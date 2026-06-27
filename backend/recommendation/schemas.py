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

class CandidateRecommendation(BaseModel):
    employee_id: str
    job_name: str
    department_name: str
    final_score: float
    rank: int
    category_scores: Dict[str, float]
    strategy_scores: Optional[Dict[str, float]] = None
    confidence: Optional[str] = "Medium"
    availability_date: str
    utilization_percentage: float
    matching_skills: List[str]

class RecommendationResponse(BaseModel):
    recommendations: List[CandidateRecommendation]
    explanation: str
    processing_time_ms: float
    model_version: str = "v1"

class BenchmarkResponse(BaseModel):
    benchmark_results: Dict[str, List[CandidateRecommendation]]
    evaluation_metrics: Dict[str, Dict[str, Any]]
    processing_time_ms: float
