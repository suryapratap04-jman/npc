# Deployment & Docker Architecture

The AI Resource Management Platform runs in a containerized environment managed by Docker Compose. This configuration isolates application logic, databases, and AI services, and coordinates container startup using built-in health checks.

---

## 1. Network Topology

All services communicate inside a private virtual bridge network named `resource-network`. This isolates database ports and LLM services, exposing only the frontend and backend ports to the host system.

```
                  ┌──────────────────────────────────────────────┐
                  │                  HOST MACHINE                │
                  │                                              │
                  │      Frontend Port         Backend Port      │
                  │          3000                  8000          │
                  └───────────┬─────────────────────┬────────────┘
                              │                     │
==============================╪=====================╪=============================
                              │                     │
                  ┌───────────▼───────────┐   ┌─────▼─────────────┐
                  │   resource-frontend   │   │  resource-backend │
                  │     (Next.js App)     │   │   (FastAPI App)   │
                  └───────────┬───────────┘   └───────────┬───────┘
                              │                           │
                              │     Private Bridge        │
                              ├───────────────────────────┤
                              │     "resource-network"    │
                              │                           │
                  ┌───────────┴───────────┐   ┌───────────┴───────┐
                  │   resource-postgres   │   │  resource-qdrant  │
                  │   (PostgreSQL 16)     │   │   (Qdrant DB)     │
                  └───────────────────────┘   └───────────┬───────┘
                                                          │
                                              ┌───────────┴───────┐
                                              │  resource-ollama  │
                                              │   (Ollama LLM)    │
                                              └───────────────────┘
```

---

## 2. Ports and Service Interfaces

The following ports are bound to the host and containers:

| Container Name | Service Name | Internal Port | Host Binding | Exposed Access | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `resource-frontend` | `frontend` | `3000` | `3000:3000` | Browser UI (`http://localhost:3000`) | User interface |
| `resource-backend` | `backend` | `8000` | `8000:8000` | API Docs (`http://localhost:8000/docs`) | Router, services, decision engines |
| `resource-postgres` | `db` | `5432` | `5432:5432` | SQL Client (`localhost:5432`) | Relational database storage |
| `resource-qdrant` | `qdrant` | `6333` | `6333:6333` | Web UI (`http://localhost:6333/dashboard`) | Vector database storage and console |
| `resource-ollama` | `ollama` | `11434` | `11434:11434` | HTTP API (`http://localhost:11434`) | Generative language models |

---

## 3. Named Volumes and Persistence

Docker uses named volumes to ensure databases retain data across container restarts and builds:

- **`postgres_data`**: Mounted at `/var/lib/postgresql/data` in `resource-postgres`. Contains SQL schemas and records.
- **`qdrant_data`**: Mounted at `/qdrant/storage` in `resource-qdrant`. Contains indexed employee vectors.
- **`ollama_data`**: Mounted at `/root/.ollama` in `resource-ollama`. Caches language model weights (e.g. `qwen2.5:7b`) to prevent downloading them repeatedly.

---

## 4. Container Health Verification

Containers verify the health of upstream services before starting, using explicit health checks and `depends_on` conditions:

1. **PostgreSQL Health Check**:
   Runs `pg_isready -U postgres` every 5 seconds. The database must be healthy before the backend starts.
2. **Qdrant Health Check**:
   Runs `curl -f http://localhost:6333/readyz` every 5 seconds to ensure the vector database endpoint is active.
3. **Ollama Health Check**:
   Runs `ollama list` every 10 seconds to verify that the model orchestrator is ready.
4. **Backend Health Check**:
   Runs `curl -f http://localhost:8000/api/health` every 10 seconds to confirm the API is ready and connected to PostgreSQL, Qdrant, and Ollama.
5. **Frontend Startup**:
   Runs only after the backend container is healthy. This prevents user actions from failing due to startup delays on the backend.

---

## 5. Startup Orchestrator Sequence

When starting up, the backend container runs `backend/scripts/start_prod.py` to coordinate the following steps:

1. **Postgres Check**: Waits for PostgreSQL to accept SQL queries.
2. **Qdrant Check**: Waits for Qdrant to accept HTTP requests.
3. **Database Seeding Check**: Creates the SQL database schema. Checks if the `employees` table is empty. If it is, the script reads CSVs from `datasets/cleaned/` and seeds the tables.
4. **Vector Embeddings Check**: Checks Qdrant collections. If the collections are empty or missing, the script extracts profiles from PostgreSQL and generates embeddings.
5. **Ollama Connection**: Wait for Ollama. Checks if `qwen2.5:7b` is present. If it is missing, the script pulls it from Ollama's registry automatically.
6. **Launch Server**: Launches uvicorn to start serving requests.
