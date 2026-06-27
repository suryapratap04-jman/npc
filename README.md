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

1. **PostgreSQL 16**: Houses the normalized data tables for employees, projects, allocations, skills, competencies, timesheets, and forecasting pipeline.
2. **Qdrant Vector Database**: Houses generated semantic vectors for Employee Profiles, Project Profiles, and Pipeline Opportunities.
3. **Ollama (Qwen2.5 7B)**: Handles the Retrieval-Augmented Generation (RAG) prompts, generating natural-language explanations of resource matches, project summaries, and consultative advice.
4. **FastAPI Backend**: Acts as the microservices entrypoint, offering database resource listings, vector searches, and RAG completion routes.

---

## Setup & Deployment

### Prerequisite
Ensure Docker and Docker Compose are installed and running on your system (or inside WSL2).

### 1. Start Services
Build and launch all services in detached mode:
```bash
docker compose up -d --build
```
This spins up PostgreSQL, Qdrant, Ollama, and the FastAPI application backend.

### 2. Seed Relational Data (ETL)
Ingest the Phase 1 cleaned CSV datasets into PostgreSQL:
```bash
docker exec -it resource-backend python -m backend.scripts.load_clean_data
```

### 3. Generate Semantic Vectors (Qdrant Sync)
Compile rich text AI Profiles for employees, projects, and pipeline requests, generate vector embeddings locally using the cached `nomic-ai/nomic-embed-text-v1.5` model, and index them in Qdrant:
```bash
docker exec -it resource-backend python -m backend.embeddings.generate_embeddings
```

### 4. Pull LLM Weights in Ollama
Trigger Ollama to fetch the preferred `qwen2.5:7b` instruct model:
```bash
docker exec -it resource-ollama ollama pull qwen2.5:7b
```

---

## Testing & Verification

Run the integration test suite inside the container to assert all database connections, vector indexes, embeddings generation, and API layers are operating correctly:
```bash
docker exec -it resource-backend pytest
```

---

## Documentation
- Detailed API routes and parameters are listed in the [API Specification Document](backend/docs/API_SPEC.md).
