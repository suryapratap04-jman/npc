# AI Resource Management API Platform

An enterprise-grade, decision-intelligence platform that integrates relational storage, semantic vector search, and local LLM orchestration to automate candidate staffing recommendations, analyze delivery risks, and simulate operational capacity.

---

## 1. Project Overview

### Problem Statement
In modern delivery organizations, staffing projects with optimal talent is a highly complex task. Resource managers must balance technical skill requirements, qualitative soft-skills, individual utilization rates, upcoming timeline ramp-downs, and cost structures. Traditional spreadsheet tracking leads to suboptimal allocations, uncoordinated capacity planning, and delayed project timelines.

### Solution Overview
The **AI Resource Management Platform** solves this by unifying data across HubSpot CRM pipelines, timesheets, and employee registries. Using a hybrid scoring recommendation model, semantic vector embeddings, and retrieval-augmented generation (RAG), the platform provides:
1. **Intelligent Staffing Recommendations**: Ranks and matches active developers to project specifications using SQL and vector searches.
2. **Project Health & Risk Diagnostics**: Flags project delivery delays, overallocation, and shadow resource billing leakages.
3. **Capacity Forecasting & What-If Simulations**: Models future resource supply vs. demand over a rolling 6-month period, simulating deal wins and capacity deficits.
4. **AI Conversational Copilot**: A RAG-driven chat assistant that reasons across all system engines to answer resource management questions.

---

## 2. Technology Stack

- **Frontend**: Next.js 15 (React 19, TypeScript, Tailwind CSS v4, TanStack React Query, Framer Motion, Recharts)
- **Backend API**: FastAPI (Python 3.11, SQLAlchemy, Uvicorn)
- **Relational Database**: PostgreSQL 16
- **Vector Database**: Qdrant Vector DB
- **Local LLM**: Ollama (orchestrating `qwen2.5:7b` for text generation and `nomic-ai/nomic-embed-text-v1.5` for text profiles encoding)
- **Containerization**: Docker & Docker Compose

---

## 3. Architecture & System Design

The system runs as a collection of decoupled containers coordinated inside a private network bridge.

```
                    ┌────────────────────────────┐
                    │      Client Browser        │
                    │   (http://localhost:3000)  │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │   Next.js Frontend Container│
                    └─────────────┬──────────────┘
                                  │ (REST API / localhost:8000)
                                  ▼
                    ┌────────────────────────────┐
                    │    FastAPI Backend Container│
                    └──────┬──────┬──────┬───────┘
                           │      │      │
          ┌────────────────┘      │      └────────────────┐
          ▼                       ▼                       ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│  PostgreSQL 16    │   │ Qdrant Vector DB  │   │   Ollama Local    │
│  (Relational DB)  │   │  (Semantic DB)    │   │    (LLM Server)   │
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

### Relational Database Design
SQL schemas under `backend/database/models.py` track core organizational entities:
- **`employees`**: Employee data, location, role, department, and active utilization.
- **`projects`**: Project status, dates, managers, and CoE affiliations.
- **`allocations`**: Active allocation matrices tracking start/end dates and percentages.
- **`skills`** & **`competencies`**: Detailed skill profiles and qualitative scores out of 5.
- **`timesheets`**: Time tracking logs mapping hours and billable status.
- **`weekly_status`**: Project status indicators (scope, schedule, quality).
- **`pipeline`**: Active HubSpot sales deal pipelines.

For detailed schema descriptions, see the [Database Design Guide](docs/database_design.md).

### Vector Database Design
Qdrant manages high-dimensional embeddings representing employee profiles, projects, and pipeline opportunities. Rich text representations are encoded into 768-dimensional vectors using `nomic-ai/nomic-embed-text-v1.5`.

For vector profile layouts and retrieval flows, see the [Vector Database Guide](docs/vector_database.md).

---

## 4. Reorganized Repository Structure

The project layout has been reorganized into a standardized enterprise structure:

```
project/
├── backend/                       # FastAPI backend codebase
│   ├── config/                    # Environment parser and configurations
│   ├── copilot/                   # Conversational LLM copilot engine
│   ├── database/                  # PostgreSQL database session and models
│   ├── embeddings/                # Embedding generation and Qdrant sync
│   ├── forecast/                  # Rolling forecasting pipelines
│   ├── health/                    # Project risk heuristics engines
│   ├── llm/                       # Local/cloud LLM providers adapters
│   ├── rag/                       # RAG retriever and generator templates
│   ├── recommendation/            # Recommendation service and scoring models
│   ├── scripts/                   # Seeding and startup scripts
│   └── tests/                     # Backend pytest suites
├── datasets/                      # Directory for data files (git-ignored)
│   ├── raw/                       # Unstructured raw files
│   └── cleaned/                   # Deduplicated, cleaned CSV tables
├── docs/                          # Architecture, API, and setup guides
├── frontend/                      # Next.js web application code
│   └── src/                       # App pages, components, services, and hooks
├── scripts/                       # Reusable tooling and pipeline scripts
│   ├── cleaning/                  # Data profiling, cleaning, and validation scripts
│   ├── notebooks/                 # Jupyter notebook documentation
│   └── ops/                       # Operational start/stop/reset helper scripts
├── docker-compose.yml             # Main Docker Compose configuration
```

For more details on directory functions, see the [Repository Structure Guide](docs/repository_structure.md).

---

## 5. Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- Local memory of at least 16GB (recommended for running local Ollama model generation).

### Single-Command Quickstart
To start the entire platform—including Next.js, FastAPI, PostgreSQL, Qdrant, and Ollama—run the startup script in your terminal:

**Windows**:
```powershell
.\scripts\ops\start.bat
```

**Linux/macOS**:
```bash
chmod +x scripts/ops/start.sh scripts/ops/stop.sh scripts/ops/reset.sh
./scripts/ops/start.sh
```

### What happens behind the scenes:
1. The script checks if `.env` exists. If not, it copies `.env.example` to create a default `.env`.
2. Docker Compose builds and starts all 5 containers in detached mode.
3. The script polls the backend health check endpoint (`http://localhost:8000/api/health`) until it returns healthy.
4. **Automatic Seeding & Syncing**: On startup, the containerized backend runs `backend/scripts/start_prod.py`.
   - If PostgreSQL is empty, it seeds SQL tables with cleaned datasets from `datasets/cleaned/`.
   - If Qdrant collections are empty or missing, it indexes the employee and project text profiles.
   - If `qwen2.5:7b` is missing in Ollama, it pulls the model automatically.
5. Once healthy, the console displays the application URLs:
   - **Frontend UI**: `http://localhost:3000`
   - **Backend API Swagger**: `http://localhost:8000/docs`
   - **Qdrant DB Dashboard**: `http://localhost:6333/dashboard`

---

## 6. API Reference

The FastAPI backend exposes endpoints for all platform features:
- **`GET /api/health`**: System status verification.
- **`POST /api/recommend/resources`**: Matches and ranks candidates for project roles.
- **`POST /api/search/employees`**: Cosine-similarity profile search.
- **`POST /api/copilot/chat`**: Conversational reasoning router.
- **`GET /api/forecast/six-month`**: Rolling 6-month capacity demand metrics.

For the complete API request and response specifications, see the [API Documentation](docs/api.md).

---

## 7. Operational Scripts

- **`.\scripts\ops\stop.bat`** (or `./scripts/ops/stop.sh`): Stops all active Docker containers without losing stored database volumes.
- **`.\scripts\ops\reset.bat`** (or `./scripts/ops/reset.sh`): Stops containers and deletes all database volumes. Run this to clear database data and trigger a fresh seed and embedding sync.

---

## 8. Verification and Tests

To run the Python backend test suite locally:
1. Activate your virtual environment and install requirements:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Execute `pytest` targeting the tests directory:
   ```bash
   python -m pytest backend/tests/
   ```

---

## 9. Troubleshooting

- **Ollama Model Download Failures**: If the model pull fails, verify your internet connection. Alternatively, you can run the pull command manually:
  ```bash
  docker exec -it resource-ollama ollama pull qwen2.5:7b
  ```
- **Connection Refused in Browser**: If you cannot access the frontend, make sure the `resource-frontend` container is running by typing `docker compose ps` and verify its logs using `docker compose logs frontend`.

---

## 10. Contributors and License

- **Maintainer**: Open Source Maintainer & AI Devops Engineer
- **License**: MIT License - see LICENSE file for details.
