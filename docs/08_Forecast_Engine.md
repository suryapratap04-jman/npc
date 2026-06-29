# Forecast Engine

This document details the forecasting models, capacity algorithms, and simulation methods of the Capacity planning and Forecasting Engine (`backend/forecast/`).

---

## 1. Rolling Capacity Forecasting
The system calculates future resource supply and demand over a six-month rolling window:
- **Supply Projections**: Computed from active employee databases, accounting for planned roll-offs, hiring targets, and historical resignation rates.
- **Demand Projections**: Aggregated from signed contracts and anticipated pipeline opportunities in Hubspot CRM.
- **Gaps Analysis**: Identifies deficits (demand > supply) or surpluses (supply > demand) per role.

---

## 2. Capacity Brackets & Rotation Lists
- **Availability Brackets**: Tracks resources whose allocations expire within 30, 60, or 90 days.
- **Priority Hiring**: Highlights critical deficits where immediate external recruitment is needed to support upcoming pipeline wins.
- **Redeployment Rotations**: Flags soon-to-be-released resources whose skills match upcoming project requirements, enabling internal transfers and reducing bench time.

---

## 3. "What-If" Simulation Engine
Users can simulate the workforce impact of a new project through the `POST /api/forecast/new-project` route:
- **Inputs**: Request payload defining project type, required team size, start date, and required skills.
- **Output**: Predicts team composition, costs, hiring requirements, and available internal resources for redeployment.
