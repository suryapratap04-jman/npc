# Repository Cleanup Audit

This audit document identifies the unused pages, duplicate components, experimental modules, incomplete features, obsolete services, and redundant APIs to be removed from the AI Resource Management Platform to align it with the core hackathon objectives.

---

## 1. Experimental and Obsolete Modules (To Be Removed)

### Frontend (App Routes & Components)
* **AI Copilot (`/copilot`)**: Completely unused. The right side AI sliding drawer and full page assistant are experimental chatbot modules that deviate from the enterprise analytics dashboard goal.
* **Search Page (`/search`)**: Redundant. Simple filter options on pages replace global search.
* **Reports Page (`/reports`)**: Non-functional placeholder page containing mock charts.
* **Settings Page (`/settings`)**: Unnecessary for the hackathon presentation.
* **Copilot Service (`frontend/src/services/copilot.service.ts`)**: Obsolete API caller.
* **Search Service (`frontend/src/services/search.service.ts`)**: Obsolete API caller.
* **Report Service (`frontend/src/services/report.service.ts`)**: Obsolete API caller.

### Backend (Folders & Services)
* **Copilot Service Module (`backend/copilot/`)**: Complete folder containing orchestrator, planner, tool registry, memory, and chatbot logic.
* **RAG Search Module (`backend/rag/`)**: Contains prompt generators and vector retriever subclasses used only by the chat and semantic search features.
* **Copilot Tests (`backend/tests/test_copilot.py`)**: Obsolete tests.
* **Copilot Metrics (`experiments/copilot_metrics.csv`)**: Obsolete CSV log.

---

## 2. Unused API Endpoints (To Be Removed from `backend/main.py`)

* **Copilot Routes**:
  * `POST /api/copilot/chat`
  * `POST /api/copilot/query`
  * `POST /api/copilot/explain`
  * `GET /api/copilot/history`
* **RAG Q&A Route**:
  * `POST /api/rag/query`
* **Semantic Search Routes**:
  * `POST /api/search/employees`
  * `POST /api/search/projects`
* **Unused Health & Diagnostic Routes**:
  * `GET /api/health/rampdown`
  * `POST /api/health/analyze`
* **Unused Recommendation Benchmarking**:
  * `POST /api/recommend/benchmark`
* **Unused Skill Queries**:
  * `GET /api/skills`

---

## 3. UI/UX Refactoring & Simplification

### Navigation Sidebar (`frontend/src/components/dashboard-shell.tsx`)
* Keep ONLY:
  * **Dashboard** (`/dashboard`)
  * **Resource Recommendation** (`/recommendation`)
  * **Project Health** (`/project-health`)
  * **Capacity & Forecast** (`/forecast`)
* Remove **AI Insights** sliding context drawer from the right side.
* Remove **Theme switcher** and other non-essential headers if they create noise, or style them cleanly.

### Command Palette (`frontend/src/components/command-palette.tsx`)
* Remove search options referring to "AI Copilot Center", "Reports", "Settings", or global search.

---

## 4. Documentation Synchronization (To Be Updated/Removed)
* Update `README.md` to map to the new database, routing, and directory structure.
* Delete:
  * `docs/09_AI_Copilot.md`
  * `docs/cache_metrics.md` (or keep it if cache management is kept, but simplify)
