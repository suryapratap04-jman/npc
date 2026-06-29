# Recommendation Engine

This document details the architecture, hybrid retrieval strategies, and generative explanation pipelines of the AI Resource Recommendation Engine (`backend/recommendation/`).

---

## 1. Candidate Retrieval Pipeline
The retrieval phase operates in two stages:
1. **Relational PostgreSQL Filtering**: Fetches active employees (excluding resigned workers) and extracts active project allocations map to filter capacity availability rates.
2. **Qdrant Vector Similarity Spotlighting**: Encodes the requested required skills and queries the `employees` Qdrant collection to retrieve the top 50 semantically matched profiles.

---

## 2. Hybrid Scoring Strategy
Matches are scored using a weighted multi-dimensional index (defaulting to the configuration weights in Platform Settings):
- **Core Skills Compatibility (40%)**: Calculates intersection counts between candidate skillsets and requested skills.
- **Role Competency Index (30%)**: Scores candidates' soft/hard consulting competencies (scores >= 3 are proficient).
- **FTE Capacity Availability (20%)**: Measures remaining unallocated workload ratios during the project window.
- **Historical Account Similarity (10%)**: Ranks candidates based on whether they have successfully delivered similar projects in Qdrant historically.

---

## 3. RAG Fit Explanation Pipeline
For the top recommendation candidates, the Explanation Engine (`explanation_engine.py`) builds diagnostics summaries:
- **Prompt Synthesis**: Assembles the candidate profile details (skills, competencies, current workload) and the project specifications into a diagnostic prompt context.
- **Ollama Generation**: Calls the local LLM (`qwen2.5:7b` or similar) to generate a professional markdown report explaining the fit matches, highlighting strengths, and identifying gaps.
