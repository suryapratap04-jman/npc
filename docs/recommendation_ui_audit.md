# AI Recommendation UI Controls Audit

This document audits every control on the AI Resource Recommendation page (`frontend/src/app/recommendation/page.tsx`), detailing whether it connects to the backend, affects recommendations, has business value, and how it should be restructured.

---

| UI Control | Current Connection | Affects Recommendation? | Business Value | Classification | Action / Redesign Plan |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Target Project Pipeline** Dropdown | Partial. Calls `/api/pipeline` to populate, sends `project_id` and parsed `rolesNeeded` (skills) in the request body. | Yes. Changes required skills and project similarity base. | High. Represents the real project demand that requires staffing. | **Modify** | Redesign to show complete metadata: Client, Technology, Domain (Cluster), Project Type, Expected Start Date, and Resource Demand. |
| **Department** Filter Dropdown | **None**. Value is saved in React state but never sent to the backend. | No. Candidates are not filtered by department. | High. Resource managers operate within departmental boundaries. | **Modify / Connect** | Add `department` to the backend `RecommendationRequest` schema. Filter candidates by `employee.department_name` in retrieval. |
| **Experience Level** Radios | **None**. Value is saved in React state but never sent to the backend. | No. Experience is not used to filter candidates. | High. Project budgets and requirements dictate seniority (e.g., senior vs. mid vs. junior). | **Modify / Connect** | Add `experience_range` to the request model. Filter candidates in `BusinessRulesEngine` (Senior: >= 5 yrs, Mid: 3-5 yrs, Junior: < 3 yrs, All: no filter). |
| **Min. Availability** Slider | **None**. Value is saved in React state but never sent to the backend. | No. Scoring uses availability, but candidates are never filtered out by this slider. | Low (as slider). | **Replace / Connect** | Replace the percentage slider with business-focused options: *Available Now*, *Available Within 2 Weeks*, *Available Within 30 Days*, *Allocation <50%*, *Bench Resources*. Map these to backend filtering. |
| **Explain Match** Button / Drawer | Partial. Recharts radar chart uses hardcoded fallback category scores if keys do not match backend. LLM narrative is a global project summary rather than candidate-specific. | No. Interactive details only. | High. Explainability is critical for Resource Managers to trust AI recommendations. | **Modify** | Return detailed scoring breakdowns, candidate-specific strengths, potential risks, and "why recommended" directly from backend calculations. |
| **Compare Selection** Checkboxes & Modal | Partial. Uses frontend-enriched employee details and fallback metrics. | No. Display only. | High. Helps compare top candidates side-by-side. | **Modify** | Redesign the comparison table/grid to use verified backend fields, including exact category scores and historical allocations. |
| **Assign Talent** Button | **None**. Displays a mock success toast notification. | No. Action trigger only. | High. The final step in the resource allocation business workflow. | **Keep** | Retain button with clear allocation flow and success states. |

---

## Redesign Summary

1. **Backend Integration**: Every filter (Department, Experience, Availability, Location) will be added to the backend request schema and applied during retrieval and scoring.
2. **Unified Data Model**: Redesign the recommendation API response to return fully enriched candidate data, removing the need for a secondary frontend call to `/api/employees`.
3. **Enterprise Dashboard UI**: Redesign the page into a guided wizard-like workflow:
   - **Step 1**: Select Target Project Demand (rich info card).
   - **Step 2**: Review Automated Staffing Gaps & Target Skills.
   - **Step 3**: Fine-Tune Parameters (Department, Experience, Location, Availability, Competencies).
   - **Step 4**: Run Matching Engine (detailed candidates cards with confidence scores, strengths, and risks).
   - **Step 5**: Compare Talent side-by-side.
   - **Step 6**: Confirm Allocation.
