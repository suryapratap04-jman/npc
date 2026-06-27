# Vector Database & Embedding Layouts

The semantic search features of the platform are powered by the **Qdrant Vector Database**. This document describes Qdrant collections, profile payloads, and vector dimensions.

---

## 1. Vector Specifications

- **Vector Database**: Qdrant (hosted in the `resource-qdrant` container, port `6333`).
- **Embedding Model**: `nomic-ai/nomic-embed-text-v1.5` (loaded via Python's `SentenceTransformer` module).
- **Vector Dimension**: 768 dimensions.
- **Distance Metric**: **Cosine Similarity** (used to evaluate similarity between search queries and indexed profiles).

---

## 2. Collections and Payloads

Qdrant is configured with three collections. Each collection stores vectors representing rich text profiles, along with payload fields to enable SQL-like filtering.

### A. `employees` Collection
Stores employee profiles compiled from skills, roles, and competencies.
- **Key Identifier**: Derived from `employee_id` (converted into a deterministic UUID).
- **Indexed Profile Text Format**:
  ```
  Employee ID: EMP102
  Role Designation: Lead React Developer
  Department: Delivery
  Location: Gurugram
  Skills & Experience: React - Redux Toolkit (Advance) score 5; TypeScript - CSS (Intermediate)
  Qualitative Core Competencies: Stakeholder Management: 4/5; Consultative Guidance: 3/5; Techno-Functional Expertise: 4/5; Communication Skills: 5/5
  Current Utilization Rate: 80%
  Active Projects: Project CLI-201 (allocation 80%)
  ```
- **Payload Structure**:
  ```json
  {
    "employee_id": "EMP102",
    "job_name": "Lead React Developer",
    "department_name": "Delivery",
    "location": "Gurugram",
    "skills": ["React", "TypeScript", "Redux Toolkit", "CSS"],
    "profile_text": "Employee ID: EMP102\n..."
  }
  ```

### B. `projects` Collection
Stores project specifications and delivery logs.
- **Key Identifier**: Derived from `project_id` (converted into a deterministic UUID).
- **Indexed Profile Text Format**:
  ```
  Project ID: CLI-201
  Client: Delta Retail Accounts
  Type: AI
  Status: Active
  Technical Center of Excellence: Advanced Analytics
  Description: Staffing vacancy for Lead React Architect to manage dashboard layout panels.
  ```
- **Payload Structure**:
  ```json
  {
    "project_id": "CLI-201",
    "client_id": "Delta Retail Accounts",
    "type_of_project": "AI",
    "project_status": "Active",
    "tech_coe": "Advanced Analytics",
    "profile_text": "Project ID: CLI-201\n..."
  }
  ```

### C. `pipeline` Collection
Stores sales pipeline opportunities and upcoming contracts.
- **Key Identifier**: Derived from `deal_id` (converted into a deterministic UUID).
- **Indexed Profile Text Format**:
  ```
  Opportunity ID: DEAL-012
  Client Name: Alpha E-Commerce Corp
  Project Name: Delta Web Platform
  Roles Needed: React Developer, Python Developer
  Estimated Value: $120,000
  Probability: 85%
  Expected Start Date: 2026-08-15
  ```
- **Payload Structure**:
  ```json
  {
    "pipeline_id": "DEAL-012",
    "client": "Alpha E-Commerce Corp",
    "solution": "Delta Web Platform",
    "status": "In Progress",
    "profile_text": "Opportunity ID: DEAL-012\n..."
  }
  ```

---

## 3. Retrieval Flow

When a search query is submitted (e.g., `"Need a React Developer with stakeholder management skills"`):
1. The backend encodes the query into a 768-dimension vector using `SentenceTransformer`.
2. The vector is sent to Qdrant's `/collections/employees/points/search` endpoint.
3. Qdrant returns matching employee records, ranked by their cosine similarity scores.
4. The backend filters these results using business rules (e.g., checking active availability and location) before returning them to the client.
