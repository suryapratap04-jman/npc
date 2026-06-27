import logging
import hashlib
from collections import Counter
from datetime import date
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database.models import Project, Allocation, Employee, Skill

logger = logging.getLogger("demand_feature_builder")

def map_employee_to_role(employee_id: str, job_name: str, skills_list: List[str], coes: List[str]) -> str:
    """
    Deterministic rule-based mapping from raw job descriptions, skills, 
    and COEs to one of the 8 standard target roles.
    """
    job = (job_name or "").lower().strip()
    skill_names = {s.lower().strip() for s in skills_list if s}
    coe_set = {c.lower().strip() for c in coes if c}
    
    # Non-delivery check
    support_keywords = [
        'hr', 'finance', 'people', 'legal', 'recruiter', 'acquisition', 
        'ta ', 'admin', 'office', 'associate finance', 'legal counsel', 
        'marketing', 'ops associate', 'operations associate', 'fp&a'
    ]
    if any(k in job for k in support_keywords):
        return 'Non-Delivery'
        
    if 'architect' in job:
        return 'Architect'
        
    # Check technology groupings
    if any('data engineering' in c or 'analytical engineering' in c for c in coe_set) or any(any(kw in s for kw in ['data engineering', 'pyspark', 'databricks', 'snowflake', 'pipeline', 'etl', 'data warehouse', 'big data', 'hadoop', 'spark', 'redshift', 'bigquery', 'data integration']) for s in skill_names):
        return 'Data Engineer'
        
    if any('data science' in c or 'ai' in c or 'ds/ai' in c for c in coe_set) or any(any(kw in s for kw in ['machine learning', 'data science', 'deep learning', 'computer vision', 'natural language', 'nlp', 'llm', 'generative ai', 'gen ai', 'tensorflow', 'pytorch', 'scikit', 'statistical model']) for s in skill_names):
        return 'Data Scientist'
        
    if any('techops' in c or 'platform' in c or 'devops' in c for c in coe_set):
        has_devops_kw = any(any(kw in s for kw in ['devops', 'kubernetes', 'docker', 'cloud', 'aws', 'azure', 'gcp', 'terraform', 'jenkins', 'ci/cd']) for s in skill_names)
        if has_devops_kw:
            return 'DevOps'
        elif 'automation infrastructure' in skill_names or any('automation' in s for s in skill_names):
            return 'QA'
        return 'DevOps'
        
    if any('qa' in c or 'test' in c for c in coe_set):
        return 'QA'
        
    if any('full stack' in c for c in coe_set) or 'software engineer' in job or 'developer' in job:
        has_qa = 'automation infrastructure' in skill_names
        has_frontend = any(any(kw in s for kw in ['react', 'angular', 'vue', 'frontend', 'javascript']) for s in skill_names)
        
        # Deterministic hash split for overloaded profiles
        h = int(hashlib.md5(employee_id.encode('utf-8')).hexdigest(), 16)
        if has_qa and has_frontend:
            if h % 3 == 0:
                return 'Frontend Engineer'
            elif h % 3 == 1:
                return 'QA'
            else:
                return 'Backend Engineer'
        elif has_qa:
            return 'QA'
        elif has_frontend:
            return 'Frontend Engineer'
        return 'Backend Engineer'
        
    return 'Consultant'

class DemandFeatureBuilder:
    def __init__(self, db: Session):
        self.db = db
        self._employee_roles_cache: Optional[Dict[str, str]] = None
        self._project_features_cache: Optional[Dict[str, Dict[str, Any]]] = None

    def load_employee_roles(self) -> Dict[str, str]:
        """Loads all employees and maps them in-memory to prevent N+1 queries."""
        if self._employee_roles_cache is not None:
            return self._employee_roles_cache
            
        logger.info("Building in-memory employee role mapping...")
        employees = self.db.query(Employee).all()
        skills = self.db.query(Skill).all()
        
        skills_by_emp: Dict[str, List[str]] = {}
        coes_by_emp: Dict[str, List[str]] = {}
        for s in skills:
            if s.employee_id:
                if s.skill:
                    skills_by_emp.setdefault(s.employee_id, []).append(s.skill)
                if s.coe:
                    coes_by_emp.setdefault(s.employee_id, []).append(s.coe)
                if s.coe_skill:
                    coes_by_emp.setdefault(s.employee_id, []).append(s.coe_skill)
                    
        self._employee_roles_cache = {}
        for emp in employees:
            self._employee_roles_cache[emp.employee_id] = map_employee_to_role(
                employee_id=emp.employee_id,
                job_name=emp.job_name,
                skills_list=skills_by_emp.get(emp.employee_id, []),
                coes=coes_by_emp.get(emp.employee_id, [])
            )
            
        return self._employee_roles_cache

    def get_employee_role(self, employee_id: str) -> str:
        roles = self.load_employee_roles()
        return roles.get(employee_id, "Consultant")

    def build_all_project_features(self) -> Dict[str, Dict[str, Any]]:
        """Analyzes historical project data to learn team composition and timeline metrics."""
        if self._project_features_cache is not None:
            return self._project_features_cache
            
        logger.info("Analyzing historical projects and allocations...")
        emp_roles = self.load_employee_roles()
        
        projects = self.db.query(Project).filter(Project.is_active_version == 1).all()
        allocations = self.db.query(Allocation).filter(Allocation.is_active_version == 1).all()
        
        allocs_by_proj: Dict[str, List[Allocation]] = {}
        for a in allocations:
            if a.project_id:
                allocs_by_proj.setdefault(a.project_id, []).append(a)
                
        self._project_features_cache = {}
        
        for p in projects:
            p_allocs = allocs_by_proj.get(p.project_id, [])
            if not p_allocs:
                continue
                
            # Compute start/end dates
            p_start = p.project_start_date
            p_end = p.project_end_date
            
            # If dates are missing, fallback to min/max allocation dates
            valid_alloc_starts = [a.allocated_start_date for a in p_allocs if a.allocated_start_date]
            valid_alloc_ends = [a.allocated_end_date for a in p_allocs if a.allocated_end_date]
            
            if not p_start and valid_alloc_starts:
                p_start = min(valid_alloc_starts)
            if not p_end and valid_alloc_ends:
                p_end = max(valid_alloc_ends)
                
            if not p_start:
                p_start = date(2025, 1, 1)
            if not p_end:
                p_end = date(2025, 6, 30)
                
            duration_days = (p_end - p_start).days
            duration_months = max(1, round(duration_days / 30.0))
            
            # Compute team size and resource mix
            team_members = {}
            for a in p_allocs:
                if not a.employee_id:
                    continue
                role = emp_roles.get(a.employee_id, "Consultant")
                if role == "Non-Delivery":
                    continue  # exclude overhead
                
                pct = a.allocation_by_percentage or 100.0
                # Track maximum allocation percentage for the member on this project
                team_members[a.employee_id] = {
                    "role": role,
                    "percentage": max(team_members.get(a.employee_id, {}).get("percentage", 0.0), pct),
                    "start": a.allocated_start_date or p_start,
                    "end": a.allocated_end_date or p_end
                }
                
            if not team_members:
                continue
                
            team_size = len(team_members)
            
            role_counts = Counter(m["role"] for m in team_members.values())
            
            # Compute average allocation percentages per role
            role_pcts = {}
            for role in role_counts:
                role_pcts[role] = sum(m["percentage"] for m in team_members.values() if m["role"] == role) / role_counts[role]
                
            # Compute ramp-up and ramp-down periods
            ramp_up_days_list = []
            ramp_down_days_list = []
            for m in team_members.values():
                ramp_up_days_list.append((m["start"] - p_start).days)
                ramp_down_days_list.append((p_end - m["end"]).days)
                
            avg_ramp_up = sum(ramp_up_days_list) / len(ramp_up_days_list) if ramp_up_days_list else 0.0
            avg_ramp_down = sum(ramp_down_days_list) / len(ramp_down_days_list) if ramp_down_days_list else 0.0
            
            # Extract technologies from tech_coe
            techs = [t.strip() for t in (p.tech_coe or "").split(";") if t.strip()]
            if not techs or p.tech_coe == "NOT_MAPPED":
                techs = ["Unknown"]
                
            self._project_features_cache[p.project_id] = {
                "project_id": p.project_id,
                "project_type": p.type_of_project or "Client Project",
                "technologies": techs,
                "domain": p.proposition_coe or "Other",
                "client_id": p.client_id,
                "duration_months": duration_months,
                "team_size": team_size,
                "role_mix": dict(role_counts),
                "role_allocation_pcts": role_pcts,
                "ramp_up_days": avg_ramp_up,
                "ramp_down_days": avg_ramp_down
            }
            
        return self._project_features_cache

    def get_historical_aggregates(self, 
                                  project_type: Optional[str] = None, 
                                  technology: Optional[str] = None, 
                                  domain: Optional[str] = None, 
                                  client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves average duration, team size, resource mix, allocation percentage, 
        and ramp periods by matching filters.
        """
        features = self.build_all_project_features()
        
        matches = []
        for pf in features.values():
            if project_type and pf["project_type"].lower() != project_type.lower():
                continue
            if technology and not any(t.lower() == technology.lower() for t in pf["technologies"]):
                if not (technology.lower() == "ai" and any("ai" in t.lower() or "llm" in t.lower() for t in pf["technologies"])):
                    continue
            if domain and pf["domain"].lower() != domain.lower():
                continue
            if client_id and pf["client_id"] != client_id:
                continue
            matches.append(pf)
            
        sample_size = len(matches)
        if sample_size == 0:
            return {"sample_size": 0}
            
        avg_duration = sum(m["duration_months"] for m in matches) / sample_size
        avg_team_size = sum(m["team_size"] for m in matches) / sample_size
        avg_ramp_up = sum(m["ramp_up_days"] for m in matches) / sample_size
        avg_ramp_down = sum(m["ramp_down_days"] for m in matches) / sample_size
        
        # Aggregate role mixes and percentages
        all_roles = ['Architect', 'Consultant', 'Backend Engineer', 'Frontend Engineer', 'Data Engineer', 'Data Scientist', 'QA', 'DevOps']
        avg_role_mix = {r: 0.0 for r in all_roles}
        avg_role_pct = {r: 0.0 for r in all_roles}
        role_presence = {r: 0 for r in all_roles}
        
        for m in matches:
            for r, count in m["role_mix"].items():
                if r in avg_role_mix:
                    avg_role_mix[r] += count
                    avg_role_pct[r] += m["role_allocation_pcts"].get(r, 100.0)
                    role_presence[r] += 1
                    
        for r in all_roles:
            avg_role_mix[r] = avg_role_mix[r] / sample_size
            if role_presence[r] > 0:
                avg_role_pct[r] = avg_role_pct[r] / role_presence[r]
            else:
                avg_role_pct[r] = 100.0  # default
                
        return {
            "sample_size": sample_size,
            "avg_duration_months": round(avg_duration, 1),
            "avg_team_size": round(avg_team_size, 1),
            "avg_role_mix": {r: round(count, 2) for r, count in avg_role_mix.items() if count > 0},
            "avg_role_allocation_pcts": {r: round(pct, 1) for r, pct in avg_role_pct.items() if r in avg_role_mix and avg_role_mix[r] > 0},
            "avg_ramp_up_days": round(avg_ramp_up, 1),
            "avg_ramp_down_days": round(avg_ramp_down, 1)
        }
