from sqlalchemy import Column, String, Integer, Float, Date, Boolean, Text
from backend.database.session import Base

class Employee(Base):
    __tablename__ = "employees"
    
    employee_id = Column(String(100), primary_key=True)
    location = Column(String(200))
    date_of_join = Column(Date, nullable=True)
    date_of_resignation = Column(Date, nullable=True)
    job_name = Column(String(200))
    department_name = Column(String(200))
    manager_id = Column(String(100))
    account_status = Column(Integer)
    is_active_version = Column(Integer)
    impossible_value_flag = Column(Integer, default=0)

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(String(100), primary_key=True)
    project_key = Column(String(512))
    project_start_date = Column(Date, nullable=True)
    project_end_date = Column(Date, nullable=True)
    type_of_project = Column(String(200))
    project_status = Column(String(100))
    reporter_id = Column(String(100), nullable=True)
    approver_id = Column(String(100), nullable=True)
    client_id = Column(String(100))
    tech_coe = Column(String(200), nullable=True)
    proposition_coe = Column(String(200), nullable=True)
    is_active_version = Column(Integer)
    impossible_value_flag = Column(Integer, default=0)

class Allocation(Base):
    __tablename__ = "allocations"
    
    project_rolebased_user_id = Column(String(100), primary_key=True)
    project_id = Column(String(100), index=True, nullable=True)
    employee_id = Column(String(100), index=True, nullable=True)
    resourcing_status = Column(String(100))
    allocated_start_date = Column(Date, nullable=True)
    allocated_end_date = Column(Date, nullable=True)
    is_allocation_active = Column(Integer)
    allocation_by_percentage = Column(Float, nullable=True)
    is_active_version = Column(Integer)
    impossible_value_flag = Column(Integer, default=0)

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(100), index=True, nullable=True)
    designation = Column(String(200))
    coe = Column(String(200))
    coe_skill = Column(String(200))
    skill = Column(String(200))
    subskill = Column(Text) # changed to Text to support long descriptions without truncation
    experience = Column(String(100))
    score = Column(Float)
    experience_numeric = Column(Float, nullable=True)

class Competency(Base):
    __tablename__ = "competencies"
    
    employee_id = Column(String(100), primary_key=True)
    designation = Column(String(200))
    coe_dep = Column(String(200))
    stakeholder_management_status = Column(String(50), nullable=True)
    stakeholder_management_score = Column(Float, nullable=True)
    consultative_guidance_status = Column(String(50), nullable=True)
    consultative_guidance_score = Column(Float, nullable=True)
    techno_functional_status = Column(String(50), nullable=True)
    techno_functional_score = Column(Float, nullable=True)
    communication_status = Column(String(50), nullable=True)
    communication_score = Column(Float, nullable=True)
    ambiguity_navigation_status = Column(String(50), nullable=True)
    ambiguity_navigation_score = Column(Float, nullable=True)
    capabilities_articulation_status = Column(String(50), nullable=True)
    capabilities_articulation_score = Column(Float, nullable=True)
    solution_architecture_status = Column(String(50), nullable=True)
    solution_architecture_score = Column(Float, nullable=True)
    project_planning_status = Column(String(50), nullable=True)
    project_planning_score = Column(Float, nullable=True)

class Timesheet(Base):
    __tablename__ = "timesheets"
    
    timesheet_surrogate_key = Column(String(100), primary_key=True)
    employee_id = Column(String(100), index=True, nullable=True)
    timesheet_id = Column(String(100))
    manager_id = Column(String(100), nullable=True)
    job_name = Column(String(200), nullable=True)
    project_id = Column(String(100), index=True, nullable=True)
    project_task_id = Column(String(100))
    pru_id = Column(String(100), nullable=True)
    is_billable = Column(Boolean, nullable=True)
    type = Column(String(100), nullable=True)
    date = Column(Date, nullable=True)
    time = Column(Float)
    status = Column(String(100))
    created_at = Column(Date, nullable=True)
    updated_at = Column(Date, nullable=True)
    submitted_on = Column(Date, nullable=True)
    data_loaded_at = Column(String(100))
    impossible_value_flag = Column(Integer, default=0)

class WeeklyStatus(Base):
    __tablename__ = "weekly_status"
    
    wsr_key = Column(String(100), primary_key=True)
    wsr_id = Column(String(100))
    project_id_masked = Column(String(100))
    scope_status = Column(String(100))
    schedule_status = Column(String(100))
    quality_status = Column(String(100))
    csat_status = Column(String(100))
    team_status = Column(String(100))
    week_start_date = Column(Date, nullable=True)
    week_end_date = Column(Date, nullable=True)
    created_at = Column(Date, nullable=True)
    updated_at = Column(Date, nullable=True)

class Pipeline(Base):
    __tablename__ = "pipeline"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster = Column(String(100), nullable=True)
    request_received = Column(Date, nullable=True)
    original_requested_start_date = Column(Date, nullable=True)
    request_type = Column(String(100), nullable=True)
    client_priority = Column(String(100), nullable=True)
    client = Column(String(200), nullable=True)
    em = Column(String(200), nullable=True)
    likely_start_date = Column(Date, nullable=True)
    start_date_confirmed = Column(String(50), nullable=True)
    number_of_weeks = Column(String(100), nullable=True)
    deal_stage_hubspot = Column(String(200), nullable=True)
    solution = Column(String(200), nullable=True)
    priority = Column(String(100), nullable=True)
    status = Column(String(200), nullable=True)
    resources_requested = Column(String(200), nullable=True)
    percentage = Column(String(100), nullable=True)
    resource_recommended = Column(String(200), nullable=True)
    percentage_available = Column(String(100), nullable=True)
    skillset = Column(Text, nullable=True)
    skillset_match = Column(String(100), nullable=True)
    sow_signed = Column(String(50), nullable=True)
    comments = Column(Text, nullable=True)
