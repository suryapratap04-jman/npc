# 06. Recommendation Engine

This document details the candidate recommendation scoring, filtering stages, and utilization calculations.

## 1. Candidate Retrieval Stages
The engine processes candidate pools in a structured sequence:
1. **Total Employees**: Loaded from the precomputed cache.
2. **Active Filter**: Excludes resigned/inactive candidates.
3. **Availability Filter**: Excludes candidates with active utilization $\ge 100\%$.
4. **Skill Filter**: Enforces mandatory skills, matching *only* skills with `score > 0.0` (ignores dummy skills).
5. **Experience Filter**: Matches requested seniority boundaries.
6. **Competency Filter**: Verifies competency scores.
7. **Semantic Scoring**: Fetches vector similarity matching.
8. **Final Ranking**: Sorts by total score.

## 2. Centralized Active Utilization Engine
Calculated in `backend/recommendation/utilization.py`:
- Sums active allocations (`is_allocation_active == 1`).
- Excludes expired allocations (where allocated end date is in the past).
- Excludes JMAN internal or BAU allocations (`CLIENT_127` or `BAU Activity`).
- Caps standard resource utilization check at 100%.

## 3. Scoring Model
Scores are calculated via the following weight distribution:
- **Skill Match**: 40% (TF-IDF weighted skill matching)
- **Competency Match**: 20% (average of matching competency scores)
- **Project Experience**: 15% (past project counts and tenure)
- **Availability**: 15% (utilization ratios and ramp-down delays)
- **Project Similarity**: 10% (semantic similarity match)
