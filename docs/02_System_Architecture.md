# System Architecture

This document describes the high-level system architecture, components, and data paths of the platform.

---

## 1. Overall Architecture Diagram

```mermaid
graph TD
    frontend[Next.js Client SPA] <==>|HTTP Requests| backend[FastAPI Service Gateway]
    backend <==>|SQLAlchemy queries| db[(PostgreSQL Relational DB)]
    backend <==>|Vector operations| qdrant[(Qdrant Vector DB)]
    backend <==>|Prompt completions| ollama[(Ollama Local LLM Service)]
```

---

## 2. Data Flow Diagram

```mermaid
graph LR
    datasets[Raw Datasets] -->|cleaning pipeline| postgres[(PostgreSQL DB)]
    postgres -->|indexing scripts| qdrant[(Qdrant Vector DB)]
    qdrant -->|semantic match| backend[FastAPI Backend]
    postgres -->|relational joins| backend
    backend -->|JSON payload| frontend[Next.js Client]
```

---

## 3. Recommendation Pipeline

```mermaid
graph TD
    UI[Project Request Selected] --> Service[recommendationService]
    Service -->|POST /api/recommend/resources| FastAPI[FastAPI route]
    FastAPI --> Retriever[CandidateRetriever]
    Retriever -->|Postgres query| SQL[Fetch Active Employees & Allocations]
    Retriever -->|Qdrant query| Vector[Fetch Semantic Profile Matches]
    SQL --> Fuse[Hybrid Score Fusion Engine]
    Vector --> Fuse
    Fuse --> RAG[Explanation Engine via Ollama]
    RAG --> Response[RecommendationResponse JSON]
    Response --> MappedUI[Card Layout Renders]
```

---

## 4. Forecast Pipeline

```mermaid
graph TD
    sixMonth[Six-Month Forecast Route] -->|Query allocations| SQL[Sum FTE allocations per month]
    sixMonth -->|Query pipeline opportunities| CRM[HuBSport CRM Deals]
    SQL & CRM --> Compute[Capacity Deficits & Surpluses]
    Compute --> Charts[Render Recharts Area Diagram]
```

---

## 5. Project Health Pipeline

```mermaid
graph TD
    HealthRoute[Project Health Details Route] --> FeatureBuilder[HealthFeatureBuilder]
    FeatureBuilder -->|Query Postgres| Delay[Calculated Delay Days]
    FeatureBuilder -->|Query Postgres| Active[Allocated Active Hours]
    Delay & Active --> Engine[Risk, Utilization, Billability & Ramp-down Engines]
    Engine --> Actions[Generate Action Recommendations]
    Engine --> LLM[Ollama Explanation Diagnostics Generator]
    LLM & Actions --> Output[ProjectHealthDetail JSON]
```

---

## 6. Copilot Pipeline

```mermaid
graph TD
    ChatUI[Copilot Chat Input] -->|POST /api/copilot/chat| FastAPI[FastAPI copilot]
    FastAPI --> Classifier[Intent Classifier]
    Classifier -->|Intent: Recommendation| Recs[Fetch Recommendation API]
    Classifier -->|Intent: Health| Health[Fetch Project Health API]
    Classifier -->|Intent: Forecast| Fore[Fetch Capacity Forecast API]
    Recs & Health & Fore --> Prompt[Synthesize Context Prompt]
    Prompt --> Ollama[Local Ollama Model Completion]
    Ollama --> Answer[Markdown Response + Structured Widgets]
```

---

## 7. Docker Architecture

```mermaid
graph TD
    subgraph Custom Bridge: resource-network
        frontend[resource-frontend :3000]
        backend[resource-backend :8000]
        db[resource-postgres :5432]
        qdrant[resource-qdrant :6333]
        ollama[resource-ollama :11434]
    end
    
    frontend --> backend
    backend --> db
    backend --> qdrant
    backend --> ollama
```

---

## 8. Deployment Flow

```mermaid
graph TD
    Git[Git Pull Latest] --> Compose[docker-compose up -d]
    Compose --> DBReady[Verify Postgres Healthcheck]
    Compose --> OllamaReady[Verify Ollama Healthcheck]
    DBReady & OllamaReady --> Index[Run run_indexing script]
    Index --> ServiceReady[Services fully operational]
```
