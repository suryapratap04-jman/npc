# AI Resource Management Copilot — Architecture & Integration

This document details the system design, intent classification, sequential planning flows, entity memory, and database fallbacks implemented in the **AI Resource Management Copilot** microservice.

---

## 1. Architectural Layout

The Copilot acts as a conversational orchestration layer. Rather than duplicating logic, it acts as an intelligent router that runs queries through specialized sub-engines and aggregates their outputs.

```
                     User Chat Query
                            │
                            ▼
                    Copilot API Route
                            │
                            ▼
                    Intent Classifier
                            │
              ┌─────────────┼─────────────┐
              │             │             │
       Recommendation    Forecast      Health
           Engine         Engine       Engine
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                 Multi-Tool Exec Aggregator
                            │
                            ▼
                    SQL Database Stubs (Fallback)
                            │
                            ▼
                    Response Builder
                            │
                            ▼
                     Assistant Reply
```

---

## 2. Component Design

The module is organized under `backend/copilot/`:

1. **`schemas.py`**: Transfer contracts for the conversation: `CopilotChatRequest`, `CopilotChatResponse`, `CopilotExplainRequest`, `ChatMessage`, and `ConversationHistoryResponse`.
2. **`intent_classifier.py`**: A hybrid classifier utilizing rule-based keyword matching and context indicators to classify messages into 10 operational intents.
3. **`conversation_memory.py`**: Stores message logs scoped per session and employs regex patterns to parse queries for Project IDs (`CLIENT_X_Y`) or Employee IDs (`EMP_X`), tracking them as contextual values for follow-up questions.
4. **`tool_registry.py`**: Resolves downstream engine objects. It imports and wraps core services. If PyTorch or SentenceTransformers are not present on the host environment, it registers SQL-based fallback stubs that perform database-driven keyword queries to simulate retrieval hits, ensuring zero crash risk.
5. **`planner.py`**: Evaluates the intent and triggers sequential workflows that execute multiple tools in logical order (e.g., fetching forecasts, looking up available capacity, and returning matched hiring/redeployment records).
6. **`response_builder.py`**: Consolidates raw tool outputs into structured, executive-level markdown answers.
7. **`orchestrator.py`**: Drives the execution loop: updates message history, runs the agent, compiles the tool plan, updates contextual memory parameters, and returns response attributes.
8. **`evaluation.py`**: Appends chat metrics (API latency, tool latency, success rate, and session message lengths) to `experiments/copilot_metrics.csv`.

---

## 3. Supported Intents & Parameters

| Intent Key | Keywords / Context | Extracted Parameters |
| :--- | :--- | :--- |
| `RESOURCE_RECOMMENDATION` | "recommend", "assign", "staff", "who should work on", "why/explain" (contextual) | `project_id`, `required_skills`, `project_type` |
| `PROJECT_HEALTH` | "health", "risk", "status", "at risk" | `project_id` (optional) |
| `NEW_PROJECT_FORECAST` | "can we take on", "new project", "take on" | `project_type`, `required_skills`, `expected_duration_months` |
| `PIPELINE_FORECAST` | "six-month", "pipeline forecast", "monthly projections" | - |
| `CAPACITY` | "capacity", "available", "bench", "utilization" | `horizon_days` (0, 30, 60, 90) |
| `HIRING` | "hire", "hiring", "recruit", "external hire" | `project_type`, `required_skills` |
| `REDEPLOYMENT` | "redeploy", "redeployment", "transfer", "transition" | `project_type`, `required_skills` |
| `EMPLOYEE_SEARCH` | "who knows", "who has skill", "search employee" | `required_skills` |
| `PROJECT_SEARCH` | "find project", "search project", "similar project" | `required_skills` |
| `GENERAL_QA` | *Fallback standard question* | `query` |

---

## 4. Multi-Tool Workflows

### Workflow A: Staffing & Validation (Intent: `RESOURCE_RECOMMENDATION`)
```
recommend_resources (Ranks available candidate matches)
       ↓
get_project_health_detail (Audits current project risk state)
       ↓
query_rag (Generates RAG narrative explaining why top candidate matches)
```

### Workflow B: New Project Ingestion (Intent: `NEW_PROJECT_FORECAST`)
```
get_new_project_forecast (Forecasts team sizes, FTE requirements, and monthly costs)
       ↓
get_capacity_status (Validates current available benches per role)
       ↓
get_redeployment_options (Queries internal transition candidates wrapping up assignments)
       ↓
get_hiring_needs (Calculates net external hiring deficit priorities)
```

### Workflow C: Semantic Match Validation (Intent: `EMPLOYEE_SEARCH`)
```
search_employees (Queries vector space or database for matching skill keywords)
       ↓
recommend_resources (Ranks matched profiles using business/availability rules)
```

### Workflow D: Operations Review (Intent: `PROJECT_HEALTH`)
```
get_projects_health (Queries overall risk metrics for all active projects)
       ↓
get_rampdown_candidates (Queries project release suitability to locate benched capacity)
```

---

## 5. Conversational Examples

### Example 1: Contextual Entity Memory
* **User**: "Recommend engineers for Project CLIENT_201_005"
* **Copilot**: *(Runs Workflow A. Recommends EMP1001 as top fit, and updates `last_project_id` to CLIENT_201_005 and `last_employee_id` to EMP1001 in session context).*
* **User**: "Explain why they were selected"
* **Copilot**: *(Classifies intent. Sees no explicit ID parameters in the query but extracts `project_id=CLIENT_201_005` and `employee_id=EMP1001` from the session context, then fetches and prints the suitability analysis).*

### Example 2: Multi-Tool Forecast Ingestion
* **User**: "Can we take on three new AI projects next month?"
* **Copilot**: *(Runs Workflow B. Formulates forecast, lists 30-day capacity horizons, matches transition candidates, logs a deficit requiring 1 DevOps hire, and formats the executive markdown response).*

---

## 6. Assumptions & Limitations

* **Session Memory Scope**: Conversational context is stored in memory (`_session_memory` instance). Restarting the FastAPI server clears session context.
* **SQL Fallback Accuracy**: The database-driven stubs perform SQL `LIKE` wildcard matching. While they match correct skills and roles, they do not carry out vector-based cosine semantic distance checks.
