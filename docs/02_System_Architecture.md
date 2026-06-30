# 02. System Architecture

This document describes the high-level system architecture, components, and data paths of the platform.

## 1. Overall Architecture Diagram

```mermaid
graph TD
    frontend[Next.js Client SPA] <==>|HTTP Requests| backend[FastAPI Service Gateway]
    backend <==>|Cache lookup| redis[(Redis Cache)]
    backend <==>|SQLAlchemy queries| db[(PostgreSQL Relational DB)]
    backend <==>|Vector operations| qdrant[(Qdrant Vector DB)]
    backend <==>|Prompt completions| ollama[(Ollama Local LLM Service)]
```

## 2. Data Flow Diagram

```mermaid
graph LR
    datasets[Cleaned Datasets] -->|cleaning pipeline| postgres[(PostgreSQL DB)]
    postgres -->|indexing scripts| qdrant[(Qdrant Vector DB)]
    qdrant -->|semantic match| backend[FastAPI Backend]
    postgres -->|relational joins| backend
    backend <==>|check / set| redis[(Redis Cache)]
    backend -->|JSON payload| frontend[Next.js Client]
```

## 3. Recommendation Pipeline

```mermaid
graph TD
    UI[Project Request Selected] --> Service[recommendationService]
    Service -->|POST /api/recommend/resources| FastAPI[FastAPI route]
    FastAPI -->|check cache hit| RedisCache{Redis Cache Hit?}
    RedisCache -->|Yes| Response[RecommendationResponse JSON]
    RedisCache -->|No| Retriever[CandidateRetriever]
    Retriever -->|Check Cache| PrecomputedPool{Has Cached Candidate Pool?}
    PrecomputedPool -->|Yes| LoadCached[Load Candidate Pool from Redis Cache]
    PrecomputedPool -->|No| LoadPostgres[Fetch Active Employees & Allocations from SQL]
    LoadCached & LoadPostgres --> Vector[Fetch Semantic Profile Matches from Qdrant]
    Vector --> Filter[Rules Engine: Active & Availability Filters]
    Filter --> Score[Scoring Engine: Skills, Competencies, Experience, Availability]
    Score --> Rank[Ranking Engine]
    Rank --> RAG[Explanation Engine via Ollama]
    RAG --> WriteCache[Store in Redis Cache]
    WriteCache --> Response
    Response --> MappedUI[Card Layout Renders]
```

## 4. Forecast Pipeline

```mermaid
graph TD
    sixMonth[Six-Month Forecast Route] -->|Query allocations| SQL[Sum FTE allocations per month]
    sixMonth -->|Query pipeline opportunities| CRM[CRM Deals]
    SQL & CRM --> Compute[Capacity Deficits & Surpluses]
    Compute --> Charts[Render Recharts Area Diagram]
```

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

## 6. Docker Architecture

```mermaid
graph TD
    subgraph Custom Bridge: resource-network
        frontend[resource-frontend :3010]
        backend[resource-backend :8000]
        redis[resource-redis :6379]
        db[resource-postgres :5432]
        qdrant[resource-qdrant :6333]
        ollama[resource-ollama :11434]
    end
    
    frontend --> backend
    backend --> redis
    backend --> db
    backend --> qdrant
    backend --> ollama
```

## 7. Deployment & Startup Flow

```mermaid
graph TD
    Git[Git Pull Latest] --> Compose[docker-compose up -d]
    Compose --> DBReady[Verify Postgres Healthcheck]
    Compose --> OllamaReady[Verify Ollama Healthcheck]
    DBReady & OllamaReady --> StartProd[Run precomputation & warming scripts]
    StartProd --> MatchHashes{CSV MD5 Hashes Match Redis?}
    MatchHashes -->|Yes| Skip[Skip Seeding & Precomputation]
    MatchHashes -->|No| Incremental[Sync Postgres & Incremental Qdrant Embeddings & Precompute Warmed Cache]
    Skip & Incremental --> ServiceReady[FastAPI Application Starts]
```

## 8. Offline Precomputation & Caching System
To minimize recommendation latency and relational database overhead:
- **Offline Profile Precomputation**: On startup, structured active employee profiles, allocations, project names, and skill frequencies are compiled into serialized cache pools (`precomputed:candidate_pool` and `precomputed:projects_name_map`).
- **Warm Redis Cache**: The server pre-populates dashboard summary views, forecasting results, and active pipeline recommendation response objects under their respective Redis keys before serving any external user requests.
- **Incremental Updates Check**: The startup orchestrator compares local CSV file MD5 checksums with cached values. Embedding rebuilds and Postgres loads are triggered only for the specific modified datasets, saving processing resources.
