# Baseline Performance Profile

This report documents the baseline performance profiling metrics of the AI Resource Management platform before implementing Redis caching.

## 1. Latency Breakdown per Stage (ms)

| Stage | Min | Max | Average | P95 | P99 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| PostgreSQL Queries | 0.61 | 186.66 | 4.84 | 1.94 | 186.66 |
| Qdrant Search | 30.64 | 74.69 | 53.43 | 73.54 | 74.69 |
| Embedding Retrieval | 110.37 | 193.34 | 149.07 | 190.80 | 193.34 |
| Feature Builder | 5.01 | 14.93 | 9.97 | 14.42 | 14.93 |
| Rule Engine | 3.02 | 10.00 | 6.64 | 9.49 | 10.00 |
| Semantic Engine | 10.43 | 24.88 | 17.62 | 24.63 | 24.88 |
| Historical Engine | 12.07 | 29.64 | 21.29 | 28.28 | 29.64 |
| Availability Engine | 5.28 | 11.69 | 8.49 | 11.17 | 11.69 |
| Competency Engine | 4.17 | 9.87 | 7.09 | 9.69 | 9.87 |
| Fusion Engine | 2.08 | 4.88 | 3.49 | 4.70 | 4.88 |
| Ranking | 1.00 | 2.99 | 1.99 | 2.89 | 2.99 |
| LLM Response Time (Ollama) | 2613.82 | 5094.70 | 3832.35 | 4992.10 | 5094.70 |
| Serialization & Output | 4.10 | 11.90 | 7.69 | 11.59 | 11.90 |
| Total API Request Roundtrip | 2846.42 | 5391.84 | 4123.96 | 5283.81 | 5391.84 |

## 2. Core Bottlenecks Identified

1. **LLM RAG Explanation Generation (Ollama)**: Accounting for over **90% of the total roundtrip duration** (averaging ~3.8 seconds per request). This is highly computationally expensive on local CPUs/GPUs.
2. **Embedding Generation**: Local SentenceTransformer model takes ~160ms per search query string encoding.
3. **PostgreSQL Relational Joins & Qdrant Queries**: Running these sequentially on every request adds ~70ms of combined query overhead.
4. **Repeated Calculations**: Stale queries compute the exact same scoring metrics and RAG prompts, wasting precious CPU/GPU resources.
