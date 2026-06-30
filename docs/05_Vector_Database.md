# 05. Vector Database

This document details the vector database collection parameters and semantic indexing scripts.

## 1. Qdrant Collection Layout
We maintain a vector catalog for semantic matching of resources:
- **Collection Name**: `employees`
- **Embedding Model**: `nomic-ai/nomic-embed-text-v1.5` (via SentenceTransformers)
- **Vector Dimensions**: **768**
- **Distance Metric**: **Cosine**

## 2. Profile Compilation
Before vector encoding, employees are compiled into rich text summaries in `backend/embeddings/generate_embeddings.py`:
- Profile layout:
  ```
  Job: Senior Data Engineer. Dept: Analytics.
  Skills: Python (Expert, 5.0 yrs), Spark (Intermediate, 3.0 yrs).
  Competencies: Solution Architecture, Consultative Guidance.
  ```

## 3. Vector Similarity Search
During resourcing matching, the project's required skillset is encoded to the same 768-dimension coordinate space. Qdrant returns candidate matches with a similarity score (0.0 to 1.0) which is fused into the final candidate fit score.
