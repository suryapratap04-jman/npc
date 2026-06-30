# Dashboard Validation Report

This report validates the dashboard KPIs and metrics computed by the unified overview API against their respective business rules and database parameters.

| Metric / KPI Card | Source API / Model | Core Business Formula / Rule | Valid Range | Actual Value | Confidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Current Utilization** | `GET /api/dashboard/overview` | Mean of capped active allocations:<br>$\bar{U} = \frac{1}{N} \sum \min(100.0, U_i)$ | $0.0\% - 100.0\%$ | **98.95%** | **High** |
| **Available Employees** | `employees`, `allocations` | Active headcount with exactly $0.0\%$ allocation | $\ge 0$ | **7** | **High** |
| **Hiring Needed** | `Pipeline`, `allocations` | Role-based net requirements:<br>$\sum \max(0, \text{Demand} - \text{Roll-offs} - \text{Bench})$ | $\ge 0$ | **45** | **High** |
| **Projects At Risk** | `weekly_status`, `allocations` | Active projects where `Risk Score` $\ge 75$ | $\ge 0$ | **1** | **High** |
| **Amber project warnings** | `weekly_status`, `allocations` | Active projects where $40 \le \text{Risk Score} < 75$ | $\ge 0$ | **78** | **High** |
| **Green project health** | `weekly_status`, `allocations` | Active projects where `Risk Score` $< 40$ | $\ge 0$ | **133** | **High** |

---

## Metric Invalidation & Cache Integrity
- All computed values are cached under the `dashboard` Redis namespace.
- SQLAlchemy listeners automatically invalidate the cache upon any update to `Employee`, `Allocation`, `Project`, `Pipeline`, `WeeklyStatus`, or `Timesheet` records, preventing stale or dirty dashboard reads.
