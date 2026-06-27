# FastAPI API Endpoint Reference

This document describes the API endpoints exposed by the FastAPI backend (port `8000`).

---

## 1. System Health

### GET `/api/health`
Verifies database connectivity and service status.
- **Response Shape**:
  ```json
  {
    "relational_db": "healthy",
    "vector_db": "healthy",
    "llm_orchestrator": "healthy",
    "status": "all_services_operational"
  }
  ```
- **Description**: Returns `503 Service Unavailable` if PostgreSQL, Qdrant, or Ollama fail health checks.

---

## 2. Relational Resources

### GET `/api/employees`
Returns employee records from PostgreSQL.
- **Query Parameters**:
  - `limit` (int, default `20`)
  - `location` (str, optional)
- **Response**: List of Employee objects.

### GET `/api/projects`
Returns project records from PostgreSQL.
- **Query Parameters**:
  - `limit` (int, default `20`)
  - `status` (str, optional)
- **Response**: List of Project objects.

### GET `/api/skills`
Returns skills records.
- **Query Parameters**:
  - `limit` (int, default `50`)
  - `skill_name` (str, optional)
- **Response**: List of Skill objects.

### GET `/api/pipeline`
Returns HubSpot pipeline opportunities.
- **Query Parameters**:
  - `limit` (int, default `20`)
  - `client` (str, optional)
- **Response**: List of Pipeline objects.

---

## 3. Vector Database Sync

### POST `/api/embeddings/generate`
Syncs database records to Qdrant vector collections.
- **Request**: Empty payload.
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Embedding sync completed successfully across all collections."
  }
  ```

---

## 4. Semantic Search

### POST `/api/search/employees`
Performs vector semantic similarity search for employees.
- **Request Payload**:
  ```json
  {
    "query": "React Developer with stakeholder experience",
    "limit": 5
  }
  ```
- **Response**: List of matching employee profiles with vector search similarity scores.

### POST `/api/search/projects`
Performs vector semantic similarity search for projects.
- **Request Payload**:
  ```json
  {
    "query": "Retail inventory dashboard architecture",
    "limit": 5
  }
  ```
- **Response**: List of matching projects.

---

## 5. Retrieval-Augmented Generation (RAG)

### POST `/api/rag/query`
Runs queries against RAG pipelines.
- **Request Payload**:
  ```json
  {
    "query": "What is the status of Delta E-Commerce?",
    "collection": "projects",
    "employee_id": null,
    "project_id": "CLI-201",
    "type": "general"
  }
  ```
- **Parameters**: `type` can be `general`, `explain` (requires `employee_id` and `project_id`), or `summarize` (requires `project_id`).
- **Response**:
  ```json
  {
    "query_type": "general_qa",
    "answer": "Delta E-Commerce is currently Red due to key staffing vacancies..."
  }
  ```

---

## 6. Recommendation Engine

### POST `/api/recommend/resources`
Ranks and recommends employees for project assignments.
- **Request Payload**:
  ```json
  {
    "project_id": "CLI-201",
    "required_skills": ["React", "TypeScript"],
    "project_type": "AI",
    "strategy": "hybrid_v1"
  }
  ```
- **Response Shape**:
  ```json
  {
    "recommendations": [
      {
        "employee_id": "EMP102",
        "name": "Alex Mercer",
        "job_name": "Lead React Developer",
        "final_score": 96.5,
        "confidence": "High",
        "skills": ["React", "TypeScript", "Redux"],
        "matching_skills": ["React", "TypeScript"],
        "utilization_percentage": 0
      }
    ],
    "explanation": "Alex Mercer is highly recommended because...",
    "processing_time_ms": 124.5
  }
  ```

---

## 7. Project Health & Capacity

### GET `/api/health/projects`
Returns health summaries for all active projects.
- **Response**: List of health summaries with status (`Green`, `Amber`, `Red`) and progress metrics.

### GET `/api/health/projects/{project_id}`
Returns details on risk, utilization, and cost recovery for a single project.
- **Response**: Detailed health report.

### GET `/api/health/rampdown`
Lists projects that are candidates for releasing allocations.
- **Response**: List of candidate projects.

---

## 8. Capacity Forecasting

### POST `/api/forecast/new-project`
Predicts staffing costs and hiring vs. redeployment needs for a new project.
- **Request Payload**:
  ```json
  {
    "project_type": "AI",
    "expected_duration_months": 6,
    "required_skills": ["React", "Python"],
    "expected_start_date": "2026-08-15"
  }
  ```
- **Response**: Capacity forecast, including team composition, hiring needs, and redeployment options.

### GET `/api/forecast/six-month`
Computes rolling 6-month operational capacity forecasts.
- **Response**: Monthly headcount demand, capacity surplus, and deficit projections.

---

## 9. Conversational Copilot

### POST `/api/copilot/chat`
Conversational chat endpoint for querying platform data.
- **Request Payload**:
  ```json
  {
    "session_id": "session-123",
    "message": "Summarize the Q3 capacity forecast"
  }
  ```
- **Response Shape**:
  ```json
  {
    "answer": "Based on current project timelines and the pipeline...",
    "confidence_score": 90,
    "sources": ["hubspot_pipeline", "timesheet_aggregations"]
  }
  ```
