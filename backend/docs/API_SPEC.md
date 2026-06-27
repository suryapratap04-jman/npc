# AI Resource Management Platform API Specification

This document details the REST API specifications for the FastAPI backend services.

---

## Base URL
When running locally via Docker Compose, the API is available at:
`http://localhost:8000`

---

## Core Resources API

### 1. Get Employees
Retrieves employee master records from the relational database.
- **Endpoint**: `GET /api/employees`
- **Query Parameters**:
  - `limit` (int, default=20): Number of records to return.
  - `location` (str, optional): Filter employees by location (case-insensitive).
- **Response (200 OK)**:
```json
[
  {
    "employee_id": "EMP101",
    "location": "London",
    "date_of_join": "2024-01-15",
    "date_of_resignation": null,
    "job_name": "Associate Consultant",
    "department_name": "Delivery",
    "manager_id": "EMP99",
    "account_status": 1,
    "is_active_version": 1,
    "impossible_value_flag": 0
  }
]
```

### 2. Get Projects
Retrieves project master records from the relational database.
- **Endpoint**: `GET /api/projects`
- **Query Parameters**:
  - `limit` (int, default=20): Number of records to return.
  - `status` (str, optional): Filter by project status (e.g., `'IN PROGRESS'`, `'COMPLETE'`).
- **Response (200 OK)**:
```json
[
  {
    "project_id": "CLIENT_101_005",
    "project_key": "PROJ-101",
    "project_start_date": "2024-03-08",
    "project_end_date": "2024-03-29",
    "type_of_project": "Client Project",
    "project_status": "COMPLETE",
    "reporter_id": "EMP50",
    "approver_id": "EMP51",
    "client_id": "CLIENT_101",
    "tech_coe": "Data Engineering",
    "proposition_coe": "Due Diligence",
    "is_active_version": 1,
    "impossible_value_flag": 0
  }
]
```

### 3. Get Skills
Retrieves skills records mapping employee capabilities.
- **Endpoint**: `GET /api/skills`
- **Query Parameters**:
  - `limit` (int, default=50)
  - `skill_name` (str, optional): Filter by specific skill term (e.g. `'Python'`).

---

## Embeddings and Search API

### 4. Trigger Vector Ingestion Sync
Rebuilds semantic AI Profiles and synchronizes embeddings into Qdrant collections.
- **Endpoint**: `POST /api/embeddings/generate`
- **Response (200 OK)**:
```json
{
  "status": "success",
  "message": "Embedding sync completed successfully across all collections."
}
```

### 5. Semantic Search: Employees
Performs vector similarity search matching employee profiles against natural language queries (e.g., search for a python engineer with consultative communication skills).
- **Endpoint**: `POST /api/search/employees`
- **Request Body**:
```json
{
  "query": "Senior data engineer with SQL optimization experience and client communication skills",
  "limit": 5
}
```
- **Response (200 OK)**:
```json
[
  {
    "id": "c04bf60c-25e2-57b1-912a-446dfc08f4c1",
    "score": 0.8842,
    "payload": {
      "employee_id": "EMP546",
      "job_name": "Senior Software Engineer",
      "department_name": "Data Engineering",
      "location": "London",
      "skills": ["SQL", "Consulting", "Tableau"],
      "subskills": ["SQL Proficiency-Ability to write complex queries...", "Data Warehousing- Understanding of..."],
      "profile_text": "Employee ID: EMP546\nRole Designation: Senior Software Engineer..."
    }
  }
]
```

---

## Retrieval-Augmented Generation (RAG) API

### 6. RAG Query
Executes semantic retrieval combined with local LLM completions. Supports general Q&A, recommendation explanations, and project scoping summaries.
- **Endpoint**: `POST /api/rag/query`
- **Request Body Options**:

#### Option A: General QA Search
```json
{
  "type": "general",
  "collection": "employees",
  "query": "Find consultants who have strong stakeholder management scores."
}
```

#### Option B: Explain Staffing Recommendation
```json
{
  "type": "explain",
  "employee_id": "EMP546",
  "project_id": "CLIENT_101_005"
}
```

#### Option C: Summarize Project Details
```json
{
  "type": "summarize",
  "project_id": "CLIENT_101_005"
}
```
- **Response (200 OK)**:
```json
{
  "query_type": "explain_recommendation",
  "answer": "Based on the provided profiles, Employee EMP546 (Senior Software Engineer) is recommended for Project CLIENT_101_005 due to the following alignments:\n\n1. **Technical Alignment**: The project is in the 'Data Engineering' Center of Excellence (CoE). Employee EMP546 holds senior capabilities in SQL proficiency and Data Warehousing, directly overlapping with the project requirements.\n2. **Qualitative Competency**: The project client is CLIENT_101, demanding consultative engagement. EMP546 has a registered 'Consulting' score of 2.0/5 and competencies in stakeholder advisory roles.\n3. **Availability**: EMP546's current utilization is at 0% (bench status), providing immediate capacity for allocation."
}
```

---

## System Diagnostics

### 7. Health check
Checks connectivity status for PostgreSQL database, Qdrant Vector DB, and Ollama.
- **Endpoint**: `GET /api/health`
- **Response (200 OK)**:
```json
{
  "relational_db": "healthy",
  "vector_db": "healthy",
  "llm_orchestrator": "healthy",
  "status": "all_services_operational"
}
```
