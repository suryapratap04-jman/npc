# 10. API Documentation

This document describes the FastAPI endpoints exposed by the backend service.

## 1. Core Endpoints

### `GET /api/pipeline`
- **Description**: Returns list of CRM sales pipeline deals.
- **Response**: `List[PipelineOpportunity]`
  - `id`: string
  - `project_name`: string
  - `client`: string
  - `technology`: string
  - `domain`: string
  - `required_skills`: List[str]
  - `start_date`: string
  - `team_size`: string
  - `status`: string

### `POST /api/recommend/resources`
- **Description**: Retrieves candidate recommendations for a project.
- **Request Body**:
  - `project_id`: string
  - `required_skills`: List[str]
  - `project_type`: string
  - `project_start_date`: string
  - `top_n`: integer
- **Response**: `RecommendationResponse`

### `GET /api/project-health`
- **Description**: Returns list of active project health summaries.
- **Response**: `List[ProjectHealthSummary]`

### `GET /api/forecast`
- **Description**: Returns six-month rolling capacity forecasts.
- **Response**: `ForecastResult`
