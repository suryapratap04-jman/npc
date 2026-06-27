# Workforce Demand Forecasting & Capacity Planning Engine

This document details the forecasting methodology, feature engineering, role mix derivation, capacity planning logic, and hiring vs. redeployment algorithms implemented in the forecasting engine.

---

## 1. Forecasting Methodology

The forecasting engine supports a modular time-series architecture for projecting future project volume and headcount demand. All models implement the `BaseForecastModel` interface, permitting seamless substitution of models:

* **Trend Extrapolation Model (Active Default)**: Fits a linear regression line ($y = mx + c$) over the historical monthly series using ordinary least squares (OLS) to project trends.
* **Exponential Smoothing Model**: Implements simple exponential smoothing (SES) with a configurable smoothing factor ($\alpha = 0.3$) to project weighted rolling states.
* **Rolling Average Model**: Uses a moving window (default: 3 months) to project the next state as the mean of the window.

### Pipeline Deals Overlay
In addition to baseline statistical trends, the engine scans the `pipeline` table for active sales deals that are in HubSpot stages. If a deal has a `likely_start_date` falling within the 6-month forecasting window, the engine overlays its projected headcount and project volume directly onto that month's baseline forecast, ensuring time-series predictions remain grounded in real sales opportunities.

---

## 2. Feature Engineering & Historical Aggregation

To forecast demand for a new project, the system inspects past projects to learn staffing profiles. Key metrics computed include:

* **Project Duration**: The exact lifespan in months derived from `project_start_date` and `project_end_date`, falling back to allocation dates if missing.
* **Average Team Size**: Distinct count of delivery resources allocated to the project.
* **Resource Mix**: The specific proportions of standard roles assigned.
* **Average Allocation Percentage**: The typical percentage load (FTE ratio) of each role.
* **Ramp-Up Period**: The average duration (in days) from the project start date until resources begin their allocations.
* **Ramp-Down Period**: The average duration (in days) from the end of resource allocations until the formal project completion date.

These features are aggregated and grouped by:
1. **Project Type** (`type_of_project`)
2. **Technology** (parsed from `tech_coe`)
3. **Business Domain** (from `proposition_coe`)
4. **Client ID** (`client_id`)

---

## 3. Role Mix Derivation

The organization defines 8 standard delivery roles:
1. **Architect**
2. **Consultant**
3. **Backend Engineer**
4. **Frontend Engineer**
5. **Data Engineer**
6. **Data Scientist**
7. **QA**
8. **DevOps**

### Heuristic Role Classification
Since raw employee database records contain varied job titles, the system classifies employees into these 8 roles using an in-memory two-tier mapping heuristic:
1. **Majority COE**: Evaluates all skills for an employee in the `skills` table and determines the dominant Center of Excellence (`coe`).
2. **Deterministic Hash Split**: When profiles are overloaded (e.g., full-stack engineers showing backend, frontend, and QA/automation skills), a deterministic hash based on their `employee_id` splits them proportionally to maintain balanced availability pools.

### Confidence Scoring
When generating a team mix recommendation:
* **High Confidence (Sample Size $\ge$ 5)**: Uses the exact average role mix of similar historical projects.
* **Medium Confidence (Sample Size 1–4)**: Employs historical averages from the small sample.
* **Low Confidence (Sample Size = 0)**: Falls back to configurable pre-defined domain templates (e.g., AI/LLM template, Data Engineering template, BI Reporting template).

---

## 4. Capacity Planning Logic

Projected capacity is evaluated across four horizons: **Today, 30 Days, 60 Days, and 90 Days**.

$$\text{Employee Capacity}(T) = 1.0 - \sum \text{Allocation Percentage}(T)$$

The capacity engine adjusts the timeline of resource release by incorporating:
* **Planned Ramp-Downs**: If a project is identified as a candidate for ramp-down by the `ProjectHealthService`, its resources are released at the `earliest_release_date` instead of the scheduled end date.
* **Project Health Risks**: Resources allocated to projects flagged as **Red (High Risk)** are assumed to become available in 15 days due to early completion/curtailment.
* **Employee Availability**: Excludes employees who are inactive or have scheduled resignation dates.

---

## 5. Hiring vs. Redeployment Algorithm

For every required role in a new project request, the engine executes a matching algorithm to decide whether to redeploy existing staff or hire externally:

```
For each required role:
  1. Determine required slots.
  2. Find available capacity in FTEs at the project start date.
  3. Query redeployment candidates:
     - Mapped role matches the required role.
     - Candidate's current allocation ends within [-60, +15] days of the new start date.
     - Rank candidates by:
       * Skill Match Score (overlap between candidate skills and required project skills).
       * Availability Date (earliest available first).
  4. Fill slots with redeployment candidates up to their capacity.
  5. If deficit remains:
     - Suggest external hiring for: Deficit - Redeploy Count.
```

---

## 6. Model Assumptions & Limitations

* **FTE Default**: The cost estimator assumes that each recommended slot represents a 1.0 FTE load (100% allocation), using predefined internal monthly cost rates per role.
* **Stable Pool Assumption**: Six-month capacity surplus/deficit projections assume the base employee count remains stable (excluding resignations).
* **Skills Database Coverage**: Role mapping relies on the `skills` table. For employees with no skill records, classification defaults to job title keywords, falling back to "Consultant".
