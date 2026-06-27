import logging
from typing import Optional
from backend.rag.retriever import VectorRetriever
from backend.llm import get_llm_provider
from backend.rag.prompt_templates import (
    RECOMMENDATION_EXPLANATION_PROMPT, PROJECT_SUMMARY_PROMPT, SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)

class RAGGenerator:
    """Generates context-aware, explainable responses using RAG pipeline."""
    
    def __init__(self):
        self.retriever = VectorRetriever()
        self.llm = get_llm_provider()
        
    def explain_recommendation(self, employee_id: str, project_id: str) -> str:
        """Explains why an employee fits a project based on vector context profiles."""
        logger.info(f"RAG Explanation: matching {employee_id} to project {project_id}")
        
        # 1. Retrieve employee profile vector payload
        emp_results = self.retriever.retrieve_employees(employee_id, limit=1)
        # Fallback to search query if ID doesn't match directly
        if not emp_results:
            emp_context = f"Employee {employee_id} context missing."
            emp_name = employee_id
            emp_job = "Unknown Designation"
        else:
            payload = emp_results[0]["payload"]
            emp_context = payload.get("profile_text", "")
            emp_name = payload.get("employee_id", employee_id)
            emp_job = payload.get("job_name", "Consultant")
            
        # 2. Retrieve project profile
        proj_results = self.retriever.retrieve_projects(project_id, limit=1)
        if not proj_results:
            proj_context = f"Project {project_id} context missing."
            proj_name = project_id
        else:
            payload = proj_results[0]["payload"]
            proj_context = payload.get("profile_text", "")
            proj_name = payload.get("project_id", project_id)
            
        # 3. Format Prompt
        prompt = RECOMMENDATION_EXPLANATION_PROMPT.format(
            employee_name=emp_name,
            employee_job=emp_job,
            project_name=proj_name,
            employee_context=emp_context,
            project_context=proj_context
        )
        
        # 4. Generate answer
        return self.llm.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)

    def summarize_project(self, project_id: str) -> str:
        """Summarizes project details and timelines."""
        logger.info(f"RAG Summary: analyzing project {project_id}")
        
        proj_results = self.retriever.retrieve_projects(project_id, limit=1)
        if not proj_results:
            return f"Project ID {project_id} was not found in the vector database."
            
        proj_context = proj_results[0]["payload"].get("profile_text", "")
        prompt = PROJECT_SUMMARY_PROMPT.format(project_context=proj_context)
        
        return self.llm.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        
    def query(self, query_text: str, collection_name: str = "employees") -> str:
        """General question answering over vector database collections."""
        logger.info(f"RAG general query: '{query_text}' on collection '{collection_name}'")
        
        # Retrieve top 3 context matches
        if collection_name == "projects":
            matches = self.retriever.retrieve_projects(query_text, limit=3)
        elif collection_name == "pipeline":
            matches = self.retriever.retrieve_pipeline(query_text, limit=3)
        else:
            matches = self.retriever.retrieve_employees(query_text, limit=3)
            
        if not matches:
            return "No matching records found in the semantic vector database to answer your question."
            
        # Combine profile context texts
        contexts = []
        for idx, m in enumerate(matches):
            txt = m["payload"].get("profile_text", "")
            score = m.get("score", 0.0)
            contexts.append(f"Matching Profile #{idx+1} (Similarity Score: {score:.3f}):\n{txt}\n")
            
        context_block = "\n=========================================\n".join(contexts)
        
        prompt = f"""
You are provided with the following matching profiles retrieved from the vector database. Use them as context to answer the user's question:

### Context Profiles:
{context_block}

### User's Question:
{query_text}

Write a professional, detailed, and context-supported answer. If the context does not contain enough information, state that clearly rather than inventing facts.
"""
        return self.llm.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
