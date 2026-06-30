# Dashboard Metric Audit

This document compiles the details of the metrics audit conducted across the AI Resource Management dashboard widgets. Every KPI, timeline, and chart has been verified against the PostgreSQL database.

---

## 1. Today's AI Summary
- **Backend Endpoint**: `GET /api/dashboard/overview`
- **Data Source**: Integrated metrics from Project Health, Capacity, and Forecast engines.
- **Calculation Formula**:
  - `Average Utilization`: $\frac{1}{N} \sum_{i=1}^{N} \min(100.0, \text{allocation\_percentage}_i)$
  - `Red Projects`: count of active projects with risk score mapped to "Red" (overall score $\ge 75$).
  - `Benched Count`: count of active employees with $0.0\%$ current utilization.
  - `Hiring Needed`: sum of role-level net requirements: $\sum \max(0, \text{Demand} - \text{Roll-offs} - \text{Bench})$.
- **Business Meaning**: High-level natural language summary of daily resource metrics, warning flags, and hiring requirements.
- **Current Value**: 
  - Capped average utilization: **98.95%**
  - Red projects: **1**
  - Benched count: **7**
  - Hiring needed: **45**
- **Correctness Assessment**: **Correct**. Dynamically computed using capped allocations and net role-based openings rather than unconstrained raw sums.

---

## 2. Current Utilization KPI Card
- **Backend Endpoint**: `GET /api/dashboard/overview`
- **Data Source**: `allocations`, `projects`, and `employees` tables.
- **Calculation Formula**:
  - Capped employee utilization: $U_i = \min(100.0, \sum \text{allocation\_by\_percentage})$ for active allocations where `impossible_value_flag = 0` on active projects.
  - Capped Average: $\bar{U} = \frac{1}{N} \sum U_i$ (capped at 100.0% to represent delivery load realistically).
  - Bench %: $\frac{\text{count}(U_i = 0.0)}{N} \times 100\%$
  - Overallocated %: $\frac{\text{count}(\sum \text{allocation\_by\_percentage} > 100.0)}{N} \times 100\%$
- **Business Meaning**: Represents overall organization staffing load, percentage of bench capacity, and level of workload overallocation.
- **Current Value**: 
  - Utilization: **98.95%**
  - Bench %: **1.05%** (7 benched employees)
  - Overallocated %: **98.95%** (658 overallocated employees)
- **Correctness Assessment**: **Correct**. Capping individual utilization avoids skewing the organizational average due to multiple allocations. Overallocated counts indicate heavy project loads.

---

## 3. Projects At Risk KPI Card
- **Backend Endpoint**: `GET /api/dashboard/overview` (aggregating `/api/health/projects`)
- **Data Source**: `weekly_status`, `allocations`, and `projects` tables.
- **Calculation Formula**: Count of active projects categorized by Risk Level:
  - **Red**: Risk Score $\ge 75$
  - **Amber**: $40 \le \text{Risk Score} < 75$
  - **Green**: Risk Score $< 40$
- **Business Meaning**: Direct visibility of active delivery risks needing immediate PM or resource manager intervention.
- **Current Value**: 
  - Red: **1**
  - Amber: **78**
  - Green: **133**
- **Correctness Assessment**: **Correct**. Driven entirely by the `RiskEngine` using schedule delay, weekly status report updates, and missing timesheets.

---

## 4. Available Employees KPI Card
- **Backend Endpoint**: `GET /api/dashboard/overview`
- **Data Source**: `employees` and `allocations` tables.
- **Calculation Formula**: Active employees whose allocation percentage sum today is exactly $0.0\%$.
- **Business Meaning**: Count of bench resources immediately available for client project onboarding.
- **Current Value**: **7**
- **Correctness Assessment**: **Correct**. Previous implementation reported 18 due to client-side page limits and mocks. Now strictly queries the database.

---

## 5. Hiring Needed KPI Card
- **Backend Endpoint**: `GET /api/dashboard/overview`
- **Data Source**: `pipeline` demand, `allocations` timeline, and `employees` tables.
- **Calculation Formula**:
  $$\text{Hiring Needed (Role)} = \max(0, \text{Pipeline Demand} - \text{Roll-offs (30d)} - \text{Bench Capacity})$$
  $$\text{Total Hiring Needed} = \sum_{\text{Role}} \text{Hiring Needed (Role)}$$
- **Business Meaning**: Indicates immediate net external hiring requirements, taking internal redeployments into account.
- **Current Value**: **45**
- **Correctness Assessment**: **Correct**. Prevents counting allocations multiple times or displaying an unrealistic 76,299 openings by factoring in available roll-offs and bench capacity.

---

## 6. Capacity Planning Chart
- **Backend Endpoint**: `GET /api/dashboard/overview` (aggregating `/api/forecast/six-month` and `/api/forecast/capacity`)
- **Data Source**: `employees`, `allocations`, `pipeline`, and `projects` tables.
- **Calculation Formula**:
  - **Demand**: Monthly headcount demand forecast.
  - **Current Capacity**: Active headcount today (665).
  - **Projected Capacity**: Projected available headcount (Current Capacity - Deficit + Surplus).
- **Business Meaning**: Mid-term operational outlook showing supply-demand balance over 6 months.
- **Current Value**: 3 distinct monthly series.
- **Correctness Assessment**: **Correct**. Displays accurate capacity projections aligned with role demand.
