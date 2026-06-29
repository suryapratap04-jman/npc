# API Documentation

This document lists all endpoints exposed by the FastAPI backend application.

---

## 1. System & Indexing Services

### Health Status
- **Route**: `GET /api/health`
- **Description**: Verifies Postgres, Qdrant, and Ollama/LLM connections.
- **Response**: `{"status": "healthy", "services": {...}}`

### Index Re-sync
- **Route**: `POST /api/embeddings/generate`
- **Description**: Triggers vector synch between PostgreSQL and Qdrant.
- **Response**: `{"status": "success", "message": "Vector index synchronization completed."}`

---

## 2. Resource Information

### Get Employees List
- **Route**: `GET /api/employees`
- **Query Params**: `limit: int = 20`, `location: str = None`
- **Response**: List of enriched employee objects including skills list, competencies scorecard, allocations, and experience.

### Get Projects List
- **Route**: `GET /api/projects`
- **Query Params**: `limit: int = 20`, `status: str = None`
- **Response**: List of project records.

---

## 3. Search Services

### Search Employees
- **Route**: `POST /api/search/employees`
- **Request Body**: `{"query": "React Developer", "limit": 5}`
- **Response**: List of Qdrant matches including cosine distance scores and profiles payload.

### Search Projects
- **Route**: `POST /api/search/projects`
- **Request Body**: `{"query": "fixed bid", "limit": 5}`
- **Response**: List of project search matches.

---

## 4. Recommendations

### Get Recommendations
- **Route**: `POST /api/recommend/resources`
- **Request Body**:
  ```json
  {
    "project_id": "PROJ_101",
    "required_skills": ["React", "TypeScript"],
    "top_n": 5
  }
  ```
- **Response**:
  ```json
  {
    "recommendations": [
      {
        "employee_id": "EMP_001",
        "final_score": 0.85,
        "matching_skills": ["React"],
        "availability_date": "Available Now"
      }
    ],
    "explanation": "Markdown description report..."
  }
  ```

---

## 5. Project Health Analytics

### Get Projects Health
- **Route**: `GET /api/health/projects`
- **Response**: List of project health summaries (`project_id`, `overall_health`, `risk_score`, `risk_level`).

### Get Project Health Details
- **Route**: `GET /api/health/projects/{project_id}`
- **Response**: Detailed diagnostic scorecard (`schedule`, `utilization`, `billability`, `recommended_actions`, and `explanation`).

---

## 6. Capacity & Forecasting

### Get Six-Month Forecast
- **Route**: `GET /api/forecast/six-month`
- **Response**: Monthly rolling projections.

### Simulate Project Impact
- **Route**: `POST /api/forecast/new-project`
- **Request Body**: `{"project_type": "AI", "expected_duration_months": 6, "required_skills": ["Python"]}`
- **Response**: Estimated cost, hiring priority lists, and redeployment rotation options.

---

## 7. AI Copilot Chat

### Chat Input
- **Route**: `POST /api/copilot/chat`
- **Request Body**: `{"message": "What is the health of project CLI-201?", "session_id": "default"}`
- **Response**: `{"response": "Markdown response", "detected_intent": "health"}`

### Fit Diagnostics Explain
- **Route**: `POST /api/copilot/explain`
- **Request Body**: `{"employee_id": "EMP_001", "project_id": "PROJ_101"}`
- **Response**: `{"explanation": "Detailed fit analysis..."}`
