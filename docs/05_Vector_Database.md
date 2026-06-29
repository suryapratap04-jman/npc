# Vector Database Design

This document details the configuration, collections, payloads, and embeddings sync scripts of the Qdrant vector database (`backend/embeddings/generate_embeddings.py`).

---

## 1. Vector Database Topology
- **Host & Ports**: Running on internal host `qdrant` on port `6333` (HTTP) and `6334` (gRPC).
- **Embedding Model**: Local `SentenceTransformer("all-MiniLM-L6-v2")` model yielding a 384-dimensional vector configuration.
- **Distance Metric**: `COSINE` similarity.

---

## 2. Qdrant Collections & Payloads

### Collection: `employees`
Stores semantic representations of employee profiles (skills, allocations, and competencies).
- **Payload Fields**:
  - `employee_id` (String)
  - `job_name` (String)
  - `department_name` (String)
  - `location` (String)
  - `skills` (List[str])
  - `subskills` (List[str])
  - `profile_text` (String, consolidated text profile used to build the embedding vector).

### Collection: `projects`
Stores semantic project descriptions, timelines, and team structures.
- **Payload Fields**:
  - `project_id` (String)
  - `project_key` (String)
  - `type_of_project` (String)
  - `project_status` (String)
  - `tech_coe` (String)
  - `proposition_coe` (String)
  - `profile_text` (String)

### Collection: `pipeline`
Stores solution requirements, skillset specification summaries, and deal details.
- **Payload Fields**:
  - `id` (String)
  - `solution` (String)
  - `status` (String)
  - `client` (String)
  - `skillset` (String)
  - `profile_text` (String)

---

## 3. Synchronization Pipeline
The vector synchronizer (`generate_embeddings.py`):
1. Deletes the active collections `employees`, `projects`, and `pipeline` if they exist to prevent stale indices.
2. Re-creates clean collections with the dynamic dimension size.
3. Retrieves records from PostgreSQL.
4. Compiles textual representations (e.g. `build_employee_profile`).
5. Generates embeddings using the local model and upserts them to Qdrant.
