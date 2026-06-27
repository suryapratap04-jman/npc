# Hybrid Recommendation Framework - Design & Architecture

This document describes the design, implementation, and scoring models of the **Hybrid Recommendation Framework** integrated within the AI Resource Management backend.

---

## 1. Architectural Layout

The framework supports multiple independent recommendation strategies that evaluate candidate suitability using separate criteria (e.g. skill matching, semantic distance, allocations history, schedules, or capabilities competencies). A downstream ensembling layer merges these rankings using configuration-driven weights.

```
                Project Requirement
                        │
                        ▼
               Candidate Retrieval
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
 Rule Engine     Semantic Engine   Historical Engine
         │              │              │
         └──────────────┼──────────────┘
                        ▼
               Fusion / Ensemble
                        ▼
                Final Ranking
                        ▼
               Diversity Filtering
                        ▼
               Confidence Scoring
                        ▼
                RAG Explanation
```

---

## 2. Recommendation Strategies

Each strategy evaluates candidates independently and maps scores to a standardized `0.0 - 100.0` scale:

### Strategy 1 — Rule-Based (`rule_based_v1`)
Reuses the existing rule-based feature builder and scoring weights:
- **Skill match weight**: $40\%$
- **Competency match weight**: $20\%$
- **Project experience weight**: $15\%$
- **Availability weight**: $15\%$
- **Project similarity weight**: $10\%$

### Strategy 2 — Semantic Similarity (`semantic_only`)
Queries the Qdrant vector database using project details. Computes employee embeddings cosine similarity against current target profiles:
$$Score = 100.0 \times \text{CosineSimilarity}(v_{\text{project}}, v_{\text{employee}})$$

### Strategy 3 — Historical Success (`historical_only`)
Retrieves all historical allocations for the candidates in the relational database.
Computes metrics:
- Similar project count
- Similar technology count (COE)
- Similar domain count (proposition COE or project type)
- Similar client count (client_id matches)
- Average project duration in days ($D_{\text{avg}}$)
- Historical completion rate ($R_{\text{comp}}$)

$$Score = 20 \cdot \min(C_{\text{client}}, 3) + 20 \cdot \min(C_{\text{domain}}, 3) + 20 \cdot \min(C_{\text{tech}}, 3) + 20 \cdot \min\left(\frac{D_{\text{avg}}}{180}, 1.0\right) + 20 \cdot R_{\text{comp}}$$
- **Cold-Start Fallback**: If an employee has no historical records, they receive a default soft-fallback score of `50.0`.

### Strategy 4 — Availability Optimizer (`availability_only`)
Scheduling-oriented ranking:
- **Utilization Score**: `100 - Current Utilization %`.
- **Transition Delay**: Deducts 2 points per day of delay between the project start date and the end of active allocations.
  $$Score = 0.5 \cdot (100 - U_{\text{current}}) + 0.5 \cdot \max(0.0, 100.0 - (\text{Delay Days} \times 2))$$

### Strategy 5 — Competency Optimizer (`competency_only`)
Ranks candidates purely by competency ratings:
$$Score = 100.0 \times \frac{\sum_{cp \in C_c} \text{Rating}(cp)}{5.0 \times |R_{\text{comp}}|}$$
- **Cold-Start Fallback**: Defaults to `70.0` if competency profiles are missing.

---

## 3. Fusion & Ensemble

The ensembled hybrid score is calculated dynamically in the fusion engine using weights loaded from `config.yaml`:
$$Score_{\text{hybrid}} = \sum w_i \times S_i$$
Default weights: Rule-Based (40%), Semantic (20%), Historical (15%), Availability (15%), Competency (10%).

---

## 4. Diversity and Confidence

### Diversity Capping
To ensure candidate diversity, the ensembler caps recommendations to a maximum of `2` candidates from the same department or direct manager. If a candidate exceeds this threshold, they are skipped.

### Recommendation Confidence
Each candidate recommendation is rated `High`, `Medium`, or `Low` using the following scoring heuristic:
$$C_{\text{val}} = 30 \cdot R_{\text{skills}} + 30 \cdot S_{\text{similarity}} + 20 \cdot I_{\text{historical}} + 20 \cdot \left(\frac{\text{FinalScore}}{100}\right)$$
- $C_{\text{val}} \ge 75 \rightarrow$ High
- $50 \le C_{\text{val}} < 75 \rightarrow$ Medium
- $C_{\text{val}} < 50 \rightarrow$ Low

---

## 5. Benchmarking & Experiments Tracking

- Exposes a dedicated benchmarking endpoint: `POST /api/recommend/benchmark`
- Logs all run statistics to `experiments/strategy_comparison.csv` for A/B tracking and metrics profiling (Precision@K, MRR, Response Time).
