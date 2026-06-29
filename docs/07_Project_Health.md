# Project Health Engine

This document details the diagnostic metrics, risk calculations, and evaluation pipelines of the Project Health Engine (`backend/health/`).

---

## 1. Diagnostics Features Builder
The `HealthFeatureBuilder` reads active project status logs, allocations, and timesheets to construct a unified feature set:
- **Timeline Progressions**: Tracks planned durations vs. elapsed dates.
- **Delay Days**: Calculated variance from expected milestones.
- **Extension Count**: Number of times the project timeline was extended.

---

## 2. Health & Risk Analysis Engines
The features are fed into sub-evaluation engines:
1. **Schedule Health (`ScheduleHealth`)**: Determines delay flags (Red if delay exceeds 14 days).
2. **Workload Utilization (`UtilizationEngine`)**: Measures active allocation ratios (average utilization, peak ratios). Flags overallocation (utilization > 100%) or underutilization (utilization < 70%).
3. **Billability Engine (`BillabilityEngine`)**: Compares billable roles vs. shadow resources. Calculates billing leakages and cost recovery statuses.
4. **Ramp-down Suitability (`RampdownEngine`)**: Identifies projects nearing completion or underutilized phases, listing release dates and skill sets that will be freed.

---

## 3. Generative Action Diagnostics
The Health Service compiles these analyses and utilizes Ollama to produce a detailed markdown summary:
- Outlines risk levels (Low, Medium, High, Critical) and health codes (Green, Amber, Red).
- Generates recommended mitigating steps (e.g. rotating shadow resources, re-negotiating deadlines).
- Compiles explanation notes describing core drivers of the project status.
