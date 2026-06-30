# 07. Project Health

This document details the calculation methods of the Project Health Engine.

## 1. Health Alert Indicators
- **Timeline Risk**: Calculates project delay days (planned end date vs current date / completed date). Delays > 14 days flag a RED alert.
- **Workload Risk**: Flags overallocated staff (>100% audited utilization) or underutilized staff (<70%).
- **Cost Risk**: Analyzes financial costs by comparing timesheet allocations to budget allocations.

## 2. Diagnostics Explanations
The Health Engine feeds project performance details to Ollama to generate diagnostic alerts (e.g. "Project CLIENT_32 is at risk due to overallocated staff and schedule slippage").
