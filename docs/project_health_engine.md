# Project Health & Capacity Intelligence Engine - Design Document

This document outlines the architecture, pipeline stages, mathematical heuristics, and API specifications for the **Project Health & Capacity Intelligence Engine** (Use Case 1b).

---

## 1. Engine Pipeline Architecture

The engine queries timesheets, allocations, project master data, and weekly status report indicators (WSR) from PostgreSQL to identify delivery delays, resource burnout risks, shadow resource costs, and candidates for resource ramp-down.

```
                  PostgreSQL
                      │
            [Health Feature Builder]
                      │
     ┌────────────────┼────────────────┐
     ▼                ▼                ▼
[Risk Engine]   [Util Engine]   [Billability Engine]
     │                │                │
     └────────────────┼────────────────┘
                      ▼
              [Rampdown Engine]
                      ▼
         [Action Recommendation Engine]
                      ▼
           [RAG Explanation Layer]
                      ▼
                 FastAPI HTTP
```

---

## 2. Mathematical Heuristics

### Risk Scoring ($Score_{\text{risk}}$)
Calculates overall delivery and timeline risk on a scale of `0.0 - 100.0`:
- **Weekly Status Statuses**: Convert `scope_status`, `schedule_status`, `quality_status`, and `csat_status` (Red/Amber/Green) into numeric flags:
  - $\text{Red} \rightarrow +20.0$ points
  - $\text{Amber} \rightarrow +10.0$ points
  - $\text{Green} \rightarrow 0.0$ points
- **Schedule Delay**:
  - Overdue (project end date is in the past and status is not complete): $+15.0$ points
  - Delay days $> 14$: $+10.0$ points
- **Resource Constraints**:
  - Overallocated resources count $> 0$: $+10.0$ points
- **Capping**: The overall risk score is capped at $100.0$.
- **Risk Level Classification**:
  - $Score \ge 75 \rightarrow$ Critical (Red Overall Health)
  - $50 \le Score < 75 \rightarrow$ High (Red Overall Health)
  - $25 \le Score < 50 \rightarrow$ Medium (Amber Overall Health)
  - $Score < 25 \rightarrow$ Low (Green Overall Health)

---

## 3. Capacity & Billing Analytics

### Utilization Metrics
- **Average Workload**: $\sum \text{Allocations} / N$
- **Idle Capacity**: $100.0 - \text{Average Utilization}$
- **Releasable Capacity**: Percentage of team allocated at $<40\%$ global utilization.

### Cost Recovery
- **Billable Hour Ratio**:
  $$\text{Billability \%} = 100 \cdot \frac{\text{Billable Hours}}{\text{Billable Hours} + \text{Non-Billable Hours}}$$
- **Shadow Resources**: Count of resources logging 0 billable hours over the past 2 weeks.

---

## 4. API Spec

### GET `/api/health/projects`
Returns summary status for all active projects.
*Response Format*:
```json
[
  {
    "project_id": "CLIENT_101_005",
    "overall_health": "Amber",
    "risk_score": 30.0,
    "risk_level": "Medium"
  }
]
```

### GET `/api/health/projects/{project_id}`
Returns diagnostic details for a single project.

### POST `/api/health/analyze`
Triggers an analysis and returns detailed metrics.

### GET `/api/health/rampdown`
Lists projects suitable for releasing capacity.
*Response Format*:
```json
[
  {
    "project_id": "CLIENT_101_005",
    "is_suitable": true,
    "estimated_release_count": 1,
    "earliest_release_date": "2026-06-27",
    "skills_released": ["Python", "SQL"]
  }
]
```
