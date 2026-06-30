# AI Resource Management Decision Intelligence Platform

An enterprise-grade decision intelligence platform designed to optimize human resource allocations, project assignments, and capacity forecasts across technical services organizations.

---

## 1. Project Overview
The AI Resource Management Platform is a high-performance web application that automates talent sourcing, project staffing, delivery risk analysis, and capacity forecasting. By integrating core human resources catalogs, timesheet activities, competency matrices, and sales CRM opportunity pipelines, it removes manual overallocation and matching biases.

## 2. Business Problem
- **High Bench Overhead**: Lagging project rotations cause unassigned, non-billable bench hours.
- **Suboptimal Staffing Choice**: Manual resourcing lacks robust verification of skills, availability, and expertise.
- **Capacity Forecasting Blindness**: Hard to predict rolling talent demands and skills gaps.
- **Disconnected Sales Pipelines**: Recruiting and training lack visibility into active CRM deals.

## 3. Proposed Solution
An integrated decision intelligence architecture combining:
- **Centralized Allocation Engine**: Relational matching of availability, expertise, and active workloads.
- **Vector Search Matching**: Semantic capabilities retrieval.
- **Health & Delivery Risk Monitoring**: Automated dashboard flagging project delay and cost metrics.
- **Interactive Forecast Scenario Workbench**: "What-If" planning workbench modeling sales pipelines.

## 4. Key Features
- **Semantic Candidate Matching**: Blends relational filtering with vector embeddings.
- **Active Utilization Engine**: Tracks true billable allocations, excluding expired projects and JMAN internal BAU activities.
- **Fit Explanations**: Generates professional natural language fit reports.
- **Project Health Tracker**: Automated alerts on timelines, workloads, and finances.
- **Interactive Forecast workbench**: Simulate sales pipelines against active staff ratios.

## 5. Technology Stack
- **Backend Core**: FastAPI (Python), SQLAlchemy (ORM).
- **Caching Layer**: Redis (In-memory storage and precomputed candidate caches).
- **Databases**: PostgreSQL 16 (Relational), Qdrant (Vector Database).
- **LLM/AI Orchestrator**: SentenceTransformers (local embeddings encoding), Ollama (`qwen2.5:7b` for text generation).
- **Frontend Core**: Next.js (App Router), React, TypeScript, Tailwind CSS, Shadcn UI, TanStack Query (v5), Recharts.

## 6. High-Level Architecture
```mermaid
graph TD
    subgraph Client [Client Presentation Layer]
        next[Next.js App Client]
    end

    subgraph Service [Application Services Gateway]
        api[FastAPI Router Gateway]
        pre[Precomputation Pipeline]
    end

    subgraph Cache [Caching Layer]
        redis[(Redis In-Memory Cache)]
    end

    subgraph Database [Database Storage Layer]
        postgres[(PostgreSQL Relational DB)]
        qdrant[(Qdrant Vector DB)]
    end

    subgraph AI [LLM Orchestration]
        ollama[Local Ollama / Gemini APIs]
    end

    next <==>|HTTP /api| api
    api <==>|Cache hits| redis
    api <==>|SQLAlchemy ORM| postgres
    api <==>|Vector Similarity| qdrant
    api ==>|Fit Explanations| ollama
    pre ==>|Warm Cache| redis
```

## 7. Repository Structure
Detailed module mappings and responsibilities are described in [Repository Structure Documentation](file:///c:/Users/SuryaPratapSingh/Documents/project/docs/12_Repository_Structure.md).

## 8. Dataset Description
CSV data tables loaded from `datasets/cleaned/`:
- `employees_clean.csv`: Payroll profiles, designations, and status.
- `skills_clean.csv`: Employee skills catalog and ratings.
- `competencies_clean.csv`: Consulting scorecard metrics.
- `projects_clean.csv`: Timelines, clients, and project manager designations.
- `allocations_clean.csv`: Allocation history.
- `pipeline_clean.csv`: Upcoming CRM opportunities.

## 9. Data Cleaning Pipeline
Managed via `scripts/cleaning/clean_data.py`:
- Parses and standardizes date formats.
- Removes duplicates, null keys, and corrects invalid references.
- Exports cleaned CSV files to `datasets/cleaned/` and seeds PostgreSQL tables.

## 10. Database Architecture
Relational tables schema implemented in [models.py](file:///c:/Users/SuryaPratapSingh/Documents/project/backend/database/models.py):
- `employees`: Core details (employee_id, location, job, department).
- `projects`: Key timelines, status, and project managers.
- `allocations`: Assigns employee IDs to project IDs with allocation ratios.
- `skills`: Skills catalog.
- `competencies`: Professional consultancy scorecards.
- `pipeline`: Anticipated CRM pipeline deals.

## 11. Vector Database
Qdrant is populated using the [generate_embeddings.py](file:///c:/Users/SuryaPratapSingh/Documents/project/backend/embeddings/generate_embeddings.py) script:
- Collections: `employees`, `projects`.
- Model: `nomic-ai/nomic-embed-text-v1.5` (768-dimensions, COSINE).

## 12. Recommendation Architecture
- **Retriever**: Queries Qdrant for semantic similarity, database for active rosters.
- **Scoring**: Blends Skills (40%), Competencies (20%), Availability (15%), Project Experience (15%), and Project Similarity (10%).
- **Active Utilization Filter**: Filters out candidates with active allocations $\ge 100\%$.
- **Skill Filter**: Only matches skills with `score > 0.0` to avoid recommendation inertia.

## 13. Project Health Engine
Assesses delivery risks:
- **Timeline Risk**: Calculates schedule delays.
- **Workload Risk**: Flags overallocated (>100%) or underutilized (<70%) staff.
- **Cost Risk**: Flags budget deviations.

## 14. Forecast Engine
- Combines Postgres active allocations with CRM pipeline deals to estimate future supply/demand gaps over a six-month rolling projection.

## 15. AI Copilot
The AI conversational chat views were deprecated to keep the dashboard focused. The LLM text generation provider is utilized behind the scenes for generating natural language explanations for candidate resourcing matches.

## 16. RAG Pipeline
- Retrieves candidate profiles from Qdrant, compiles them with relational database metadata, and prompts local or cloud LLMs to generate context-bound resourcing summaries.

## 17. API Architecture
Exposes FastAPI routes under `/api/*`:
- `/api/pipeline`: CRM pipeline deals.
- `/api/recommend/resources`: Generates candidate recommendations.
- `/api/project-health`: Delivery health stats.
- `/api/forecast`: Rolling scenario workbench.

## 18. Frontend Architecture
- Client Components (`"use client"`) using React Query hooks for client caching and state binding.
- Recharts maps charts; Framer Motion manages transitions.

## 19. Docker Architecture
Configured via `docker-compose.yml`:
- `resource-postgres`: PostgreSQL 16 relational store.
- `resource-redis`: Caching layer.
- `resource-qdrant`: Vector database.
- `resource-backend`: FastAPI application.
- `resource-frontend`: Next.js client.

## 20. Folder Structure
```
├── backend/                  # FastAPI Application
│   ├── cache/                # Redis Caching Services
│   ├── config/               # Settings & Variables
│   ├── database/             # Postgres Schemas & Connections
│   ├── embeddings/           # Vector Indexing
│   ├── forecast/             # Forecast Engine
│   ├── health/               # Project Health Engine
│   ├── llm/                  # AI/LLM Provider Classes
│   ├── recommendation/       # Candidate Scoring Engine
│   └── tests/                # Pytest Test Suites
├── datasets/                 # Datasets
├── docs/                     # Documentation (numbered 01-15)
├── frontend/                 # Next.js SPA App
├── scripts/                  # Cleaning & Pipeline Scripts
└── docker-compose.yml        # Multi-Container Config
```

## 21. Installation
Ensure Python 3.11+, Node 18+, and Docker are installed.
```bash
git clone <repo-url>
cd project
```

## 22. Environment Variables
Copy `.env.example` to `.env` in the root:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resource_db
REDIS_URL=redis://localhost:6379/0
QDRANT_HOST=localhost
QDRANT_PORT=6333
LLM_PROVIDER=ollama
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
```

## 23. Running with Docker
```bash
docker-compose up --build -d
```

## 24. Running without Docker
### Backend Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
python -m backend.main
```
### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 25. Data Pipeline
```bash
# Run cleaning & seed database
.venv\Scripts\python -m scripts.cleaning.clean_data
```

## 26. Embedding Pipeline
```bash
# Run vector indexing
.venv\Scripts\python -m backend.embeddings.generate_embeddings
```

## 27. Testing
```bash
.venv\Scripts\pytest backend/tests/
```

## 28. Troubleshooting
- **WSL Port Binding**: Stop local PostgreSQL/Redis before compose up.
- **HuggingFace Timeout**: Ensure internet connection is active on model startup to verify caching.

## 29. Future Improvements
- Multi-tenancy support.
- Live timesheet APIs integrations.
- Dynamic skill ontology graphs.

## 30. Contributors
- Engineering Team

## 31. License
Proprietary. All rights reserved.
