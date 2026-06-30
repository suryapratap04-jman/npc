# Pipeline Dataset Quality & Integrity Audit

This document presents a detailed audit of the cleaned pipeline dataset (`datasets/cleaned/pipeline_clean.csv`) and its mapping to the FastAPI/PostgreSQL database model as requested in Phase 1.

---

## 1. Summary Metrics

- **Total Row Count**: 293
- **Duplicate Records**: 1 duplicate row found (Index 78 & Index 282: Client `Unknown`, skillset `NULL`, cluster `5`, likely start date `2026-08-31`).
- **Placeholder Values**: 237 rows (80.9%) have Client name set to `Unknown`.
- **Null Fields**:
  - **Solution (Technology)**: 265 rows (90.4%) have no technology solution defined.
  - **Required Skills (Skillset)**: 156 rows (53.2%) have no skillset specified.
- **Broken Relationships / Empty Rows**:
  - 110 rows are completely blank placeholders where the client is `Unknown` and the skillset is `NULL`. These rows have no functional business purpose and contain no criteria to run resource matching.

---

## 2. Detailed Data Profiling

| Attribute | Data Profiling Status | Placeholders / Nulls | Action |
| :--- | :--- | :--- | :--- |
| **Project ID / ID** | Integer sequence. | None. | Keep. Used as the primary key. |
| **Client** | String. Represents client names. | 237 `Unknown` placeholders. | **Filter/Enrich**. Retain only records with defined skillsets. Discard completely empty placeholder rows. |
| **Technology (Solution)**| String. Represents tech domain. | 265 `NULL` values. | **Enrich**. If null but skillset is present, default to CoE technology fields. |
| **Domain (Cluster)** | Integer (1 to 5). | Standardized. | Keep. Represents business vertical clusters. |
| **Required Skills** | Comma-separated strings. | 156 `NULL` values. | **Filter**. Staffing demands must have skill requirements to generate recommendations. Filter out rows without skillset. |
| **Project Type** | String (e.g. `New`, `Replacement`). | 255 `NULL` values. | Default to `AI` or `General Delivery` if null. |
| **Expected Start Date** | Date format (YYYY-MM-DD). | None. | Standardized. |
| **Status** | String (e.g. `Not Resourced`). | None. | Standardized. |
| **Demand (Percentage)** | String/Midpoint (e.g. `100`, `50`, `12.5`). | None. | Loaded from `Unnamed: 15` in the CSV. |

---

## 3. Database Schema Mappings (Mismatches Identified)

The database seeder `backend/scripts/load_clean_data.py` uses `db.bulk_insert_mappings(Pipeline, df_pipe.to_dict(orient="records"))` which fails silently to load several columns due to header mismatches:

1. **`Unnamed: 15` vs `percentage`**:
   - The CSV column containing allocation percentage demand is named `Unnamed: 15`.
   - The DB model column is named `percentage`.
   - **Result**: Allocation demand percentage is written as `NULL` in the database.
2. **`available` vs `percentage_available`**:
   - The CSV column is named `available`.
   - The DB model column is named `percentage_available`.
   - **Result**: Written as `NULL` in the database.
3. **`skillset_match_complete_partial_no` vs `skillset_match`**:
   - The CSV column is named `skillset_match_complete_partial_no`.
   - The DB model column is named `skillset_match`.
   - **Result**: Written as `NULL` in the database.

---

## 4. Frontend Project Selector Impact

The target project pipeline selector in the frontend displays:
`{id} - {client} - {solution} (Priority: {priority})`

- **Problem**: Because 265 solutions are null and 237 clients are "Unknown", the dropdown is populated with uninformative items like:
  `12 - Unknown - N/A (Priority: Medium)`
- **Solution**:
  1. We will modify the database seeder to rename the CSV columns on load to match the database schema exactly, ensuring that `percentage` (Demand) is populated.
  2. We will filter out the 110 completely empty rows (`client == "Unknown" and skillset is null`) during seeding/database loading, leaving 183 active pipeline requests.
  3. We will modify the frontend project pipeline selector to display a structured project info card detailing: Client, Technology, Domain (Cluster), Required Skills, Estimated Team Size (resources_requested/percentage), Expected Start Date, and Status.
