# Database Schema Design

The relational database layer is hosted on PostgreSQL. This document describes the database tables, fields, data types, and entity relationships.

---

## 1. Entity Relationship Diagram

The following diagram illustrates how the database tables are connected:

```
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│    employees    │◄──────────┤     skills      │           │    projects     │
├─────────────────┤           ├─────────────────┤           ├─────────────────┤
│ PK employee_id  │           │ PK id           │           │ PK project_id   │
│    location     │           │ FK employee_id  │           │    project_key  │
│    job_name     │           │    skill        │           │    client_id    │
│    dept_name    │           │    subskill     │           │    start_date   │
│    join_date    │           │    experience   │           │    end_date     │
│    resign_date  │           │    score        │           │    status       │
└────────┬────────┘           └─────────────────┘           └────────┬────────┘
         │                                                           │
         │   ┌─────────────────┐                                     │
         │   │  competencies   │                                     │
         ├───├─────────────────┤                                     │
         │   │ PK employee_id  │                                     │
         │   │    stakeholder  │                                     │
         │   │    consultative │                                     │
         │   │    techno_func  │                                     │
         │   │    ...          │                                     │
         │   └─────────────────┘                                     │
         │                                                           │
         │   ┌─────────────────┐                                     │
         │◄──┤   allocations   ├────────────────────────────────────►│
         │   ├─────────────────┤                                     │
         │   │ PK allocation_id│                                     │
         │   │ FK employee_id  │                                     │
         │   │ FK project_id   │                                     │
         │   │    start_date   │                                     │
         │   │    end_date     │                                     │
         │   │    percent      │                                     │
         │   │    is_active    │                                     │
         │   └─────────────────┘                                     │
         │                                                           │
         │   ┌─────────────────┐                                     │
         │◄──┤   timesheets    ├────────────────────────────────────►│
         │   ├─────────────────┤                                     │
         │   │ PK timesheet_id │                                     │
         │   │ FK employee_id  │                                     │
         │   │ FK project_id   │                                     │
         │   │    date         │                                     │
         │   │    hours        │                                     │
         │   └─────────────────┘                                     │
         │                                                           │
         │                                                           │
         │   ┌─────────────────┐                                     │
         │   │  weekly_status  ├────────────────────────────────────►│
         │   ├─────────────────┤                                     │
         │   │ PK wsr_id       │                                     │
         │   │ FK project_id   │                                     │
         │   │    week_start   │                                     │
         │   │    scope_status │                                     │
         │   │    schedule_stat│                                     │
         │   │    ...          │                                     │
         │   └─────────────────┘                                     │
         │                                                           │
         │   ┌─────────────────┐                                     │
         │   │    pipeline     │                                     │
         │   ├─────────────────┤                                     │
         │   │ PK deal_id      │                                     │
         │   │    client       │                                     │
         │   │    project_name │                                     │
         │   │    est_value    │                                     │
         │   │    probabilty   │                                     │
         │   │    start_date   │                                     │
         │   └─────────────────┘                                     │
```

---

## 2. Table Specifications

### A. `employees`
Stores employee profiles and core organization data.
- **`employee_id`** (VARCHAR, Primary Key): Unique employee identifier (e.g., `EMP102`).
- **`location`** (VARCHAR): Geographical location (e.g., `Gurugram`).
- **`job_name`** (VARCHAR): Role or job title (e.g., `Lead React Developer`).
- **`department_name`** (VARCHAR): Department name (e.g., `Delivery`).
- **`date_of_join`** (DATE): Employment start date.
- **`date_of_resignation`** (DATE, Nullable): Resignation date.
- **`current_project_id`** (VARCHAR, Nullable): References `projects(project_id)`.
- **`allocation_percentage`** (INTEGER): Current active allocation percentage across all projects.

### B. `projects`
Stores project specifications and delivery logs.
- **`project_id`** (VARCHAR, Primary Key): Unique project identifier (e.g., `CLI-201`).
- **`project_key`** (VARCHAR): Project name/key.
- **`client_id`** (VARCHAR): Client identifier.
- **`project_start_date`** (DATE): Project start date.
- **`project_end_date`** (DATE): Project scheduled end date.
- **`project_status`** (VARCHAR): Status (e.g., `Active`, `Completed`).
- **`type_of_project`** (VARCHAR): Category (e.g., `AI`, `Data Engineering`).
- **`tech_coe`** (VARCHAR): Technical Center of Excellence (e.g., `Advanced Analytics`).
- **`proposition_coe`** (VARCHAR): Delivery proposition group.
- **`reporter_id`** (VARCHAR): Reporter or manager identifier.

### C. `allocations`
Records allocations of employees to projects.
- **`allocation_id`** (INTEGER, Primary Key, Auto-increment): Unique record ID.
- **`employee_id`** (VARCHAR, Foreign Key): References `employees(employee_id)`.
- **`project_id`** (VARCHAR, Foreign Key): References `projects(project_id)`.
- **`allocated_start_date`** (DATE): Start of allocation.
- **`allocated_end_date`** (DATE): End of allocation.
- **`allocation_by_percentage`** (INTEGER): Allocation percentage (e.g. `50`).
- **`is_allocation_active`** (INTEGER): Active flag (`1` for active, `0` for inactive).

### D. `skills`
Lists skills and technical capabilities for each employee.
- **`id`** (INTEGER, Primary Key, Auto-increment): Unique record ID.
- **`employee_id`** (VARCHAR, Foreign Key): References `employees(employee_id)`.
- **`skill`** (VARCHAR): Skill name (e.g., `React`).
- **`subskill`** (VARCHAR): Specialized subskill (e.g., `Redux Toolkit`).
- **`experience`** (VARCHAR): Qualitative experience level (e.g., `Advance`).
- **`score`** (INTEGER): Rating score (e.g. `5`).

### E. `competencies`
Stores qualitative core competencies scored out of 5.
- **`employee_id`** (VARCHAR, Primary Key, Foreign Key): References `employees(employee_id)`.
- **`stakeholder_management_score`** (INTEGER): Score for stakeholder communication.
- **`consultative_guidance_score`** (INTEGER): Score for client advisory capabilities.
- **`techno_functional_score`** (INTEGER): Score for functional delivery.
- **`communication_score`** (INTEGER): Score for clarity and explanation.
- **`ambiguity_navigation_score`** (INTEGER): Score for handling delivery complexities.
- **`capabilities_articulation_score`** (INTEGER): Score for articulating service offerings.
- **`solution_architecture_score`** (INTEGER): Score for solution estimation and architecture.
- **`project_planning_score`** (INTEGER): Score for agile sprint estimation.

### F. `timesheets`
Stores time tracking logs used to check resource burn rates.
- **`timesheet_id`** (INTEGER, Primary Key, Auto-increment): Unique record ID.
- **`employee_id`** (VARCHAR, Foreign Key): References `employees(employee_id)`.
- **`project_id`** (VARCHAR, Foreign Key): References `projects(project_id)`.
- **`date`** (DATE): Work log date.
- **`hours_logged`** (FLOAT): Hours logged (e.g., `8.0`).
- **`billable_status`** (VARCHAR): Billing category (e.g., `Billable`, `Shadow`).
- **`billing_rate`** (FLOAT): Hourly billing rate in USD.

### G. `weekly_status`
Tracks weekly project status reports (WSR).
- **`id`** (INTEGER, Primary Key, Auto-increment): Unique record ID.
- **`project_id`** (VARCHAR, Foreign Key): References `projects(project_id)`.
- **`week_start_date`** (DATE): Start of reporting week.
- **`week_end_date`** (DATE): End of reporting week.
- **`scope_status`** (VARCHAR): Status flag (`Green`, `Amber`, `Red`).
- **`schedule_status`** (VARCHAR): Status flag (`Green`, `Amber`, `Red`).
- **`quality_status`** (VARCHAR): Status flag (`Green`, `Amber`, `Red`).
- **`csat_status`** (VARCHAR): Status flag (`Green`, `Amber`, `Red`).

### H. `pipeline`
Stores business development deals from HubSpot CRM.
- **`deal_id`** (VARCHAR, Primary Key): HubSpot deal ID (e.g., `DEAL-012`).
- **`client`** (VARCHAR): Client name.
- **`project_name`** (VARCHAR): Deal name.
- **`estimated_value`** (FLOAT): Projected contract value in USD.
- **`probability`** (FLOAT): Closing probability (e.g. `0.85`).
- **`expected_start_date`** (DATE): Projected start date.
- **`roles_needed`** (VARCHAR): Required skills list.
- **`notes`** (VARCHAR, Nullable): Text notes.
