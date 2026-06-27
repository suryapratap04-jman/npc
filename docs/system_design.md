# System Design & Data Pipelines

This document describes the design patterns, mathematical formulas, and data pipeline structures powering the decision-intelligence engines of the platform.

---

## 1. Recommendation Engine Pipeline

The recommendation engine matches resources to projects by evaluating skill compatibility, semantic similarity, qualitative competencies, availability, and historical contract metrics.

```mermaid
sequenceDiagram
    autonumber
    participant Client as Frontend client
    participant Router as Backend Router
    participant Service as Recommendation Service
    participant Postgres as PostgreSQL DB
    participant Qdrant as Qdrant Vector DB
    participant LLM as Ollama LLM
    
    Client->>Router: POST /api/recommend/resources (Request matching)
    Router->>Service: recommend_resources(req)
    
    Service->>Postgres: Fetch employees & skills matching mandatory rules
    Postgres-->>Service: Return SQL candidate rows
    
    Service->>Qdrant: Query collection 'employees' with project spec query
    Qdrant-->>Service: Return semantic scores & vector matches
    
    Service->>Service: Combine SQL and Vector sets (Union/Filter)
    Service->>Service: Precompute skills rarity (IDF weights)
    Service->>Service: Calculate availability score (utilization checks)
    Service->>Service: Calculate competency scores (qualitative profiles)
    Service->>Service: Score candidate list using weighted matrix formula
    
    Service->>LLM: Pass ranked candidates & project specs for summary prompt
    LLM-->>Service: Return generated explanation text
    
    Service->>Postgres: Log recommendation evaluation metrics (precision, recall)
    Postgres-->>Service: Acknowledge log
    
    Service-->>Router: Return RecommendationResponse JSON
    Router-->>Client: Return JSON Payload
```

### Hybrid Score Calculation

$$Score_{\text{final}} = w_1 \cdot Score_{\text{skills}} + w_2 \cdot Score_{\text{semantic}} + w_3 \cdot Score_{\text{availability}} + w_4 \cdot Score_{\text{competency}} + w_5 \cdot Score_{\text{history}}$$

Where:
- $Score_{\text{skills}}$ is calculated using skill frequency weighted by their rarity (IDF).
- $Score_{\text{semantic}}$ is the cosine similarity score returned by Qdrant.
- $Score_{\text{availability}}$ measures the developer's allocation buffer (bench time).
- $Score_{\text{competency}}$ is the average score across required qualitative capabilities.
- $Score_{\text{history}}$ evaluates the developer's experience with the required project type.

---

## 2. Capacity & Demand Forecast Pipeline

The forecast engine analyzes time-tracking datasets and pipeline contracts to predict upcoming staffing shortages and identify hiring requirements.

```mermaid
graph LR
    subgraph Input Data
        A[HubSpot CRM Deals]
        B[Active Project Allocations]
        C[Timesheet Hours Logs]
    end
    
    subgraph Forecasting Engine
        D[Pipeline Probability Filter]
        E[FTE Demand Modeler]
        F[Supply Rollout Tracker]
        G[Capacity Deficit Analyzer]
    end
    
    subgraph Outputs
        H[6-Month Supply/Demand Chart]
        I[Prioritized Hiring Needs]
        J[Internal Redeployment List]
    end
    
    A --> D
    B --> E
    C --> F
    
    D --> G
    E --> G
    F --> G
    
    G --> H
    G --> I
    G --> J
```

- **Operational Capacity**: Modeled by tracking active employees' availability timelines, accounting for upcoming contract completions.
- **Projected Demand**: Calculated by aggregating FTE requirements from active projects and adding HubSpot pipeline opportunities, weighted by their closing probability.

---

## 3. Project Health Diagnostic Pipeline

The project health engine assesses delivery risk using hours tracked on timesheets and indicators from Weekly Status Reports (WSR).

```mermaid
graph TD
    Timesheets[Timesheet Hours Logged] -->|Calculate utilization ratios| UtilEngine[Utilization Engine]
    WSR[WSR Red/Amber/Green Flags] -->|Weight scope/schedule warnings| RiskEngine[Risk Engine]
    Billing[Postgres Billing Rates] -->|Calculate shadow resource cost| BillEngine[Billability Engine]
    
    UtilEngine --> Aggregator[Health Service Aggregator]
    RiskEngine --> Aggregator
    BillEngine --> Aggregator
    
    Aggregator -->|Threshold classification| Status[Overall Status: Green/Amber/Red]
    Aggregator -->|Identify underutilized resources| RampDown[Ramp-down Recommendations]
```

### Risk Heuristics Status Capping

- **WSR Status Warnings**: Adds $+20.0$ points for Red statuses and $+10.0$ points for Amber statuses across scope, schedule, quality, and CSAT indicators.
- **Timeline Slippage**: Adds $+15.0$ points if a project is past its scheduled end date without being marked completed.
- **Risk Level**: Capped at $100.0$. Scores $\ge 75.0$ are classified as **Red (Critical)**, $50.0 - 75.0$ as **Red (High Risk)**, $25.0 - 50.0$ as **Amber (Medium Risk)**, and $< 25.0$ as **Green (Healthy)**.

---

## 4. Copilot Conversational Pipeline

The Copilot acts as an intelligent assistant, routing natural language questions to decision sub-engines.

```mermaid
graph TD
    Query[User Chat Query] --> Intent[Intent Classifier]
    
    Intent -->|Keywords matching & pattern checks| Plan[Planner Sequence]
    
    Plan -->|Intent: Recommendation| ToolRec[Recommendation Service]
    Plan -->|Intent: Forecast| ToolFore[Forecast Service]
    Plan -->|Intent: Health| ToolHealth[Project Health Service]
    
    ToolRec --> OutputAgg[Response Builder]
    ToolFore --> OutputAgg
    ToolHealth --> OutputAgg
    
    OutputAgg -->|Construct RAG context| LLM[Ollama Local LLM]
    LLM -->|Generate executive summary| Reply[Markdown Response]
```
- **Session Memory**: Uses regex patterns to identify Project IDs (`CLI-X`) or Employee IDs (`EMP-Y`) from queries and retains them across follow-up conversational questions.
- **Relational Fallback**: If vector search is unavailable, the database adapter executes SQL queries to locate resources.
