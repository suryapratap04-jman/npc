# Database Design

This document details the PostgreSQL relational database design, SQLAlchemy models, columns, types, and constraints configured in `backend/database/models.py`.

---

## 1. Relational Schema & Tables

### Employee Table (`employees`)
Stores master records of employees.
- `employee_id` (String, Primary Key)
- `location` (String)
- `date_of_join` (Date)
- `date_of_resignation` (Date, Nullable)
- `job_name` (String, e.g. "Senior Consultant")
- `department_name` (String, CoE)
- `manager_id` (String)
- `account_status` (Integer)
- `is_active_version` (Integer)
- `impossible_value_flag` (Integer)

### Project Table (`projects`)
Tracks client contracts and delivery statuses.
- `project_id` (String, Primary Key)
- `project_key` (String, Unique Project Code)
- `project_start_date` (Date)
- `project_end_date` (Date)
- `type_of_project` (String, e.g. "T&M", "Fixed Bid")
- `project_status` (String, e.g. "ACTIVE", "CLOSED")
- `reporter_id` (String, PM)
- `approver_id` (String)
- `client_id` (String)
- `tech_coe` (String)
- `proposition_coe` (String)
- `is_active_version` (Integer)
- `impossible_value_flag` (Integer)

### Allocation Table (`allocations`)
Maps resources to projects with a timeline and commitment ratio.
- `id` (Integer, Primary Key)
- `allocation_id` (String)
- `employee_id` (String, Foreign Key to employees)
- `project_id` (String, Foreign Key to projects)
- `allocation_start_date` (Date)
- `allocation_end_date` (Date)
- `allocation_by_percentage` (Float)
- `is_allocation_active` (Integer, 1 = Active, 0 = Inactive)
- `allocation_status` (String)
- `billable_status` (String)
- `fte` (Float)
- `is_active_version` (Integer)

### Skill Table (`skills`)
Catalogs technical and functional skillsets per employee.
- `id` (Integer, Primary Key)
- `employee_id` (String, Foreign Key to employees)
- `skill` (String, Skill Name)
- `subskill` (String)
- `experience_numeric` (Float, Experience in years)
- `experience_level` (String)
- `competency_level` (String)

### Competency Table (`competencies`)
Stores detailed scorecards of employee consulting competencies.
- `employee_id` (String, Primary Key, Foreign Key to employees)
- `stakeholder_management_score` (Float)
- `consultative_guidance_score` (Float)
- `techno_functional_score` (Float)
- `communication_score` (Float)
- `ambiguity_navigation_score` (Float)
- `capabilities_articulation_score` (Float)
- `solution_architecture_score` (Float)
- `project_planning_score` (Float)

### Weekly Status Table (`weekly_status`)
Tracks historical delivery status updates.
- `id` (Integer, Primary Key)
- `project_id` (String, Foreign Key to projects)
- `week_date` (Date)
- `schedule_status` (String, Green/Amber/Red)
- `resourcing_status` (String)
- `budget_status` (String)
- `highlight` (String)
- `lowlight` (String)

### Pipeline Table (`pipeline`)
Tracks Hubspot pipeline deal logs.
- `id` (Integer, Primary Key)
- `deal_id` (String)
- `client` (String)
- `project_name` (String)
- `solution` (String)
- `status` (String)
- `likely_start_date` (Date)
- `original_requested_start_date` (Date)
- `number_of_weeks` (Integer)
- `probability` (Float)
- `estimated_value` (Float)
- `skillset` (String)
- `comments` (String)
