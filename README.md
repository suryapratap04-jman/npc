# AI-Powered Resource Recommendation System Platform

This repository houses the AI platform infrastructure supporting semantic resource matching, skills searching, allocation optimization, and Retrieval-Augmented Generation (RAG) QA.

The system integrates a relational database (PostgreSQL 16) with a semantic vector space database (Qdrant) and a local LLM orchestrator (Ollama running Qwen2.5 7B), exposed via a FastAPI REST backend.

---

## Architecture Overview

```
                      +-------------------+
                      |   Client / UI     |
                      +---------+---------+
                                |
                                v
                      +---------+---------+
                      |  FastAPI Backend  | (Port 8000)
                      +----+----+----+----+
                           |    |    |
        +------------------+    |    +------------------+
        |                       |                       |
        v                       v                       v
+-------+-------+       +-------+-------+       +-------+-------+
|  PostgreSQL   |       |  Qdrant DB    |       |   Ollama LLM  |
|  (Relational) |       |   (Vectors)   |       |  (Generative) |
|  (Port 5432)  |       |  (Port 6333)  |       |  (Port 11434) |
+---------------+       +---------------+       +---------------+
```

---

## Directory Structure

The project code is organized as a modular Python package:
```
project/
├── rawData/             # Read-Only raw source Excel & CSV files
├── cleanedData/         # Cleaned, standardized CSV outputs from Phase 1
│
├── cleaning/            # Phase 1 Data Discovery, profiling, and ETL cleaning
│   ├── reports/         # Visual charting reports (.png plots)
│   ├── clean_data.py    # Main cleaning pipeline runner
│   ├── validation.py    # Standardized validation asserts
│   ├── config.py        # File path listings and constants
│   └── utils.py         # Helper utilities
│
├── backend/             # Phase 2 Multi-service API and AI Orchestrator package
│   ├── config/          # Application settings and environment parsing
│   │   └── settings.py
│   ├── database/        # SQLAlchemy database connection and models
│   │   ├── session.py
│   │   └── models.py
│   ├── scripts/         # Data migration and ETL seeding scripts
│   │   └── load_clean_data.py
│   ├── embeddings/      # SentenceTransformer vector indexing pipeline
│   │   └── generate_embeddings.py
│   ├── llm/             # Generative AI provider abstractions (Ollama/Gemini/Groq)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── ollama.py
│   │   ├── gemini.py
│   │   ├── groq.py
│   │   └── factory.py
│   ├── rag/             # Retrieval-Augmented Generation (RAG) orchestration
│   │   ├── retriever.py
│   │   ├── prompt_templates.py
│   │   └── generator.py
│   ├── tests/           # Integration tests suite (pytest)
│   │   ├── test_api.py
│   │   ├── test_db.py
│   │   ├── test_embeddings.py
│   │   ├── test_qdrant.py
│   │   └── test_rag.py
│   ├── docs/            # API Specifications
│   │   └── API_SPEC.md
│   ├── Dockerfile       # FastAPI container definition
│   ├── requirements.txt # Python backend dependencies
│   └── main.py          # FastAPI application server entrypoint
│
├── docker-compose.yml   # Multi-service infrastructure orchestration config
└── notebooks/           # Jupyter notebooks for data profiling
```

---

## Step-by-Step Platform Setup Workflow

Follow these steps in chronological order to initialize and run the platform.

### Step 1: Phase 1 Data Discovery & Cleaning (Local)
Ingest raw unstructured/dirty Excel and CSV sheets from `rawData/`, standardize datatypes, resolve constraints, write duplicate reports, and output cleaned data files into `cleanedData/`.

1. **Install local data science dependencies**:
   ```bash
   pip install pandas numpy openpyxl matplotlib seaborn jinja2
   ```
2. **Execute the cleaning pipeline**:
   ```bash
   python cleaning/clean_data.py
   ```
   This generates:
   - Cleaned output files inside `cleanedData/` (e.g. `employees_clean.csv`, `projects_clean.csv`).
   - Standardized profile quality charts, duplicate reports, and null maps inside `cleaning/reports/` and `cleaning/`.

---

### Step 2: Docker Containers Launch
Launch the platform services (FastAPI Backend, PostgreSQL, Qdrant, and Ollama) in detached background mode:

```bash
docker compose up -d --build
```
Verify that all 4 containers are running:
```bash
docker ps
```

---

### Step 3: Database Seeding (PostgreSQL ETL Ingestion)
Ingest the cleaned data from `cleanedData/` into PostgreSQL tables using the DB script inside the FastAPI container:

```bash
docker exec resource-backend python -m backend.scripts.load_clean_data
```

---

### Step 4: Generate Vector Embeddings (Qdrant Sync)
Compile rich semantic AI Profiles for employees, projects, and pipeline requests, generate high-dimensional vectors, and synchronize them into Qdrant collections.

*Note: This script runs with sequence limiting and chunk processing to keep memory footprint under 250MB (safe for standard CPUs).*
```bash
docker exec resource-backend python -m backend.embeddings.generate_embeddings
```

---

### Step 5: Pull LLM Weights in Ollama
Trigger Ollama inside its container to fetch and cache the `qwen2.5:7b` instruct model:

```bash
docker exec resource-ollama ollama pull qwen2.5:7b
```

---

## Step 6: Testing & Query Verification

### 1. Run Complete Test Suite
Assert that database connections, vector indexes, local embedding generations, and API route states pass criteria:
```bash
docker exec resource-backend pytest
```

### 2. Verify System Health Check
Query the health route to verify operational status of core systems:
```bash
curl http://localhost:8000/api/health
```
**Expected Response**:
```json
{
  "relational_db": "healthy",
  "vector_db": "healthy",
  "llm_orchestrator": "healthy",
  "status": "all_services_operational"
}
```

### 3. Run Semantic Search Query
Perform a vector similarity search for candidates (e.g. searching for a "data engineer"):
```bash
curl -X POST http://localhost:8000/api/search/employees \
  -H "Content-Type: application/json" \
  -d '{"query": "data engineer", "limit": 2}'
```
*(Returns matching employee profiles sorted by cosine similarity).*

### 4. Execute RAG Query
Explain a resource recommendation allocation:
```bash
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"type": "explain", "employee_id": "EMP101", "project_id": "CLIENT_101_005"}'
```
*(Returns natural language explanation justifying staffing suitability).*
