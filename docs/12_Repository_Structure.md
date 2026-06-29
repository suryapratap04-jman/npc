# Repository Structure

This document details the folder structure, component responsibilities, main modules, and dependencies of the platform.

---

## 1. Directory Tree
```
├── backend/                  # FastAPI Backend Source
│   ├── config/               # Settings & Constants
│   ├── database/             # Relational Models & Sessions
│   ├── embeddings/           # Vector Generation scripts
│   ├── recommendation/       # Matching & Scoring Engines
│   ├── health/               # Diagnostic & Risk Engines
│   ├── forecast/             # Demand Planning & Capacity Projections
│   ├── copilot/              # Conversational RAG Engines
│   └── main.py               # Main API Gateway Router
│
├── frontend/                 # Next.js 15 Frontend Source
│   ├── src/
│   │   ├── app/              # Next.js App Router Page Layouts
│   │   ├── components/       # Shared UI Widgets
│   │   ├── services/         # Centralized API Services Layer
│   │   └── store/            # Global Toast Stores
│   ├── package.json          # Node Dependencies list
│   └── next.config.js        # Next.js settings
│
├── datasets/                 # Raw and Processed dataset tables
├── scripts/                  # Data loading and vector sync scripts
└── docker-compose.yml        # Orchestration descriptor
```

---

## 2. Folder Responsibilities & Core Files

### Backend Service Area (`backend/`)
- **`main.py`**: Intercepts HTTP requests and handles path routing.
- **`database/models.py`**: Defines SQLAlchemy Postgres mappings.
- **`embeddings/generate_embeddings.py`**: Loads the local SentenceTransformer model, transforms relational profiles into text blocks, and syncs vectors to Qdrant.
- **`recommendation/`**:
  - `candidate_retriever.py`: Retrieves resource candidate pools.
  - `recommendation_service.py`: Performs weighted matching.
  - `explanation_engine.py`: Prompts Ollama for candidate diagnostics drawers summaries.

### Frontend Client Area (`frontend/`)
- **`src/services/`**: Centralized service handlers (e.g. `recommendation.service.ts`, `health.service.ts`, `report.service.ts`).
- **`src/app/`**: Route pages rendering React client components.
- **`src/components/`**: Layout panels (e.g., `dashboard-shell.tsx`, breadcrumbs, and command palettes).
