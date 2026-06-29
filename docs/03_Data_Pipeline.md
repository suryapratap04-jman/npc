# Data Pipeline

This document describes the data cleaning and loading pipeline configured inside `scripts/cleaning`.

---

## 1. Raw Datasets Overview
The platform processes raw organization datasets (located in `datasets/raw/`):
- **Employees**: Payroll listings, locations, and hiring dates.
- **Skills**: Skill catalogs, subskills, and experience mappings.
- **Competencies**: Scorecards tracking consultant soft/hard competencies.
- **Projects**: Active and closed project keys, PM allocations, and types.
- **Allocations**: Resource assignments, durations, and active ratios.
- **Pipeline**: Hubspot deals tracking expected solution demands.

---

## 2. Cleaning & Validation Pipeline
The main processing entry points are:
1. **`clean_data.py`**:
   - Parses date columns, normalizes casing, and filters NaN values.
   - Cleans duplicate primary keys and establishes unique identifiers.
   - Saves clean files in `datasets/processed/` and calls SQL seeding.
2. **`validation.py`**:
   - Validates that date boundaries match (e.g. `project_start_date` before `project_end_date`).
   - Ensures no orphan records exist (e.g. allocations without existing employee IDs).
3. **`feature_engineering.py`**:
   - Computes composite profiles, experience levels, and skill combinations.
