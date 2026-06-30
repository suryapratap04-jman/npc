# AI Recommendation End-to-End Flow Audit

This document traces the complete execution flow of the AI Resource Recommendation module, from the user interface down to database retrieval, mathematical scoring, LLM generation, and back to UI rendering.

```mermaid
graph TD
    A[Recommendation Page UI] -->|React State / react-query| B[API Service: recommendation.service.ts]
    B -->|HTTP POST /api/recommend/resources| C[FastAPI Endpoint: main.py]
    C -->|recommend_resources()| D[Recommendation Service]
    D -->|1. retrieve_candidates()| E[Candidate Retriever]
    E -->|SQL query| F[(PostgreSQL)]
    E -->|Vector similarity query| G[(Qdrant Vector DB)]
    D -->|2. filter_candidates()| H[Business Rules Engine]
    D -->|3. precompute_metrics()| I[Historical Engine]
    D -->|4. build_features()| J[Feature Builder]
    D -->|5. calculate_score()| K[Scoring Engine]
    D -->|6. strategy scores routing| L[Semantic / Historical / Availability / Competency / Fusion Engine]
    D -->|7. apply_diversity_filter()| M[Diversity Engine]
    D -->|8. calculate_confidence()| N[Confidence Engine]
    D -->|9. generate_explanation()| O[Explanation Engine / Ollama]
    D -->|10. Return Response| C
    C -->|JSON Response| B
    B -->|Enrich client-side with /api/employees| P[React Query Cache / UI Render]
```

---

## 1. Recommendation Page (UI)
- **Path**: `frontend/src/app/recommendation/page.tsx`
- **Role**: Entry point for Resource Managers. 
- **Interactive Controls**:
  - **Target Project Pipeline Selector**: Dropdown showing projects mapped from the `Pipeline` table.
  - **Match Filters**:
    - *Department*: Dropdown (All, Engineering, Design, QA).
    - *Experience Level*: Radio options (All, Senior 5+ yrs, Mid-Level 3-5 yrs).
    - *Min. Availability*: Percentage slider (0-100%).
  - **Resource Cards Grid**: Renders recommended resources, showing name, role, match score, confidence level, availability percentage, and a brief explanation snippet.
  - **Assign Talent Button**: Allocates the resource to the project (triggers toast notification).
  - **Compare Selection**: Allows selection of up to 3 candidates for side-by-side metric comparison.
  - **Explain Match Drawer**: Detailed modal containing diagnostic scoring (Recharts Radar), skills match, verified competency strengths, availability outlook (Recharts Bar Chart), and the LLM explanation.

---

## 2. React State & Hooks
- **Path**: `frontend/src/app/recommendation/page.tsx`
- **Key State Variables**:
  - `selectedProjectId`: Currently selected target pipeline project ID.
  - `experienceLevel`: Current UI state of the experience level radio (all, senior, mid). Note: **This state is currently not passed to the API request.**
  - `department`: Current UI state of the department dropdown (all, engineering, design, qa). Note: **This state is currently not passed to the API request.**
  - `availabilityThreshold`: Current UI state of availability slider. Note: **This state is currently not passed to the API request.**
  - `compareIds`: IDs of candidates selected for comparison.
  - `selectedCandidate`: The candidate object for the detailed explain drawer.
- **Data Querying**:
  - Uses `@tanstack/react-query` to fetch the list of projects (`projectsList`) and the list of recommendations (`recommendations`).
  - The `recommendations` query triggers whenever `selectedProjectId` changes, but does not bind the UI filters (`experienceLevel`, `department`, `availabilityThreshold`) to the API parameters.

---

## 3. Frontend API Service
- **Path**: `frontend/src/services/recommendation.service.ts`
- **Key Methods**:
  - `getProjects()`: Calls `/api/pipeline?limit=100` to fetch pipeline projects with required skills.
  - `getRecommendations(req)`: Calls `/api/recommend/resources` POST endpoint. After receiving the recommendations list, it performs a secondary call to `/api/employees?limit=100` to match relational fields (`name`, `skills`, `competencies`, `experience_years`, `email`) on the client side since the recommendation endpoint only returns IDs.

---

## 4. FastAPI Endpoint
- **Path**: `backend/main.py`
- **Endpoint**: `@app.post("/api/recommend/resources", response_model=RecommendationResponse)`
- **Behavior**:
  - Instantiates `RecommendationService(db)`.
  - Delegates execution to `service.recommend_resources(req)`.
  - Utilizes `@cache(namespace="recommendation", ttl_seconds=TTL)` to cache recommendations.

---

## 5. Recommendation Service
- **Path**: `backend/recommendation/recommendation_service.py`
- **Execution Orchestration**:
  1. Parses project date parameters (start/end window).
  2. Calls `CandidateRetriever.retrieve_candidates()` to get SQL active candidates + vector similarity candidates.
  3. Filters candidates using `BusinessRulesEngine.filter_candidates()`.
  4. Precomputes `skills_idf` mappings from PostgreSQL for rarity scoring.
  5. Computes historical metrics for the candidate pool via `HistoricalEngine.precompute_metrics()`.
  6. Computes normalized features via `FeatureBuilder.build_features()`.
  7. Scores candidates with `ScoringEngine.calculate_score()` and routes strategies (hybrid, semantic, historical, availability, competency).
  8. Enforces diversity limits via `DiversityEngine.apply_diversity_filter()`.
  9. Evaluates candidate list confidence using `ConfidenceEngine.calculate_confidence()`.
  10. Generates natural language explanation narrative using `ExplanationEngine.generate_explanation()` (delegated to Ollama or a deterministic fallback).
  11. Logs evaluation run details using `RecommendationEvaluator`.
  12. Returns a `RecommendationResponse` model.

---

## 6. Sub-Engines & Pipeline Details

### A. Candidate Retrieval
- **Path**: `backend/recommendation/candidate_retriever.py`
- **Logic**:
  - Queries active employees from PostgreSQL (`employees` table).
  - Retrieves relational dependencies (Skills, Competencies, Allocations).
  - Computes billable utilization (overlapping allocations with client_id != "CLIENT_127" and type_of_project != "BAU Activity" during project start-end window).
  - Queries Qdrant vector database (`employees` collection) for similarity against requested skills string.
  - Queries Qdrant (`projects` collection) to find similar historical projects, and identifies employee IDs who historically worked on those projects.

### B. Business Rules Engine
- **Path**: `backend/recommendation/business_rules.py`
- **Hard Constraints**:
  - Account status check (`account_status == 1` and `is_active_version == 1`).
  - Resignation check (`date_of_resignation` is null or in the future).
  - High utilization check (`utilization < 100%`).
  - Mandatory skills check (discards candidates missing any of the required skills if `require_mandatory_skills` is enabled).
  - Pre-start date overlap lock (discards candidates with active allocations overlapping the start date if total utilization matches or exceeds 100%).

### C. Feature Builder
- **Path**: `backend/recommendation/feature_builder.py`
- **Feature Extraction & Normalization (0-100 scale)**:
  - **Skill Match Score**: Weighted IDF match of required skills in employee profile.
  - **Competency Match Score**: Normalized average rating (1-5 scaled to 0-100) of requested competencies (fallback to average of all competencies if none requested).
  - **Project Experience Score**: Combination of normalized max experience years (cap: 15.0 years) and normalized historical projects count (cap: 10.0 projects).
  - **Availability Score**: Normalized unallocated capability during project window (`100.0 - utilization`).
  - **Project Similarity Score**: Employee semantic similarity score from Qdrant scaled to 0-100.

### D. Scoring & Fusion Engine
- **Path**: `backend/recommendation/scoring_engine.py` & `fusion_engine.py`
- **Logic**:
  - Applies configurable weights from `config.yaml` to candidate features.
  - Defaults: `skill_match` 40%, `competency_match` 20%, `project_experience` 15%, `availability` 15%, `project_similarity` 10%.
  - Under `hybrid_v1` strategy, the `FusionEngine` ensembles weighted strategy scores: Rule-based (40%), Semantic (20%), Historical (15%), Availability (15%), Competency (10%).

### E. Diversity Engine
- **Path**: `backend/recommendation/diversity_engine.py`
- **Logic**:
  - Caps recommendations per department and per manager (default max: 2 of each) to avoid over-depleting specific teams.

### F. Confidence Engine
- **Path**: `backend/recommendation/confidence_engine.py`
- **Logic**:
  - Classifies recommendations as **High**, **Medium**, or **Low** based on:
    - Proportion of matching skills vs. required skills.
    - Semantic vector distance score.
    - Presence of prior similar project experience.
    - Calculated final score.

### G. Explanation Engine
- **Path**: `backend/recommendation/explanation_engine.py`
- **Logic**:
  - Summarizes the project requirements and top 3 recommended candidates.
  - Queries local LLM (Ollama with Qwen-2.5) to produce a structured natural language description of candidate strengths, risks, and overall search reasoning.
  - Falls back to a rule-based deterministic text generator if Ollama is disabled or times out.
