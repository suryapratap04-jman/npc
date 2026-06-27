# Repository Audit Report

This report outlines the cleanup, consolidation, and refactoring actions taken across the repository to ensure production-level quality, eliminate dead code, and standardize the folder layout.

| Path | Category | Reason | Action | Detail / Resolution |
| :--- | :--- | :--- | :--- | :--- |
| `rawData/` | Obsolete Folder | Unstructured hackathon inputs. | **Delete / Move** | Moved to `datasets/raw/` to standardize the data directory layout. |
| `cleanedData/` | Obsolete Folder | Cleaned CSV files used for database seeding. | **Delete / Move** | Moved to `datasets/cleaned/` to align with enterprise structure. |
| `cleaning/` | Obsolete Folder | Modular python scripts for dataset profiling, cleaning, and validating. | **Delete / Move** | Moved to `scripts/cleaning/` to separate operational code from source modules. Updated `config.py` with dynamic parent path resolution. |
| `notebooks/` | Obsolete Folder | Jupyter notebooks for initial data profiling. | **Delete / Move** | Moved to `scripts/notebooks/` to group all script assets. |
| `experiments/` | Obsolete Folder | CSV files containing model quality comparison logs. | **Delete / Move** | Moved to `datasets/experiments/` to group output metrics with data directories. |
| `scratch/` | Obsolete Folder | Temporary developer scratch scripts. | **Delete / Move** | Moved to `scripts/scratch/` and cleaned hardcoded path overrides to ensure execution safety. |
| `implementation/` | Obsolete Folder | Step-by-step developer guidelines for phases 1-6. | **Delete / Move** | Moved to `docs/archive/implementation_plans/` as historical records. |
| `frontend/src/components/demo-controller.tsx` | Dead Component | React UI component managing automatic walkthrough tour simulation. | **Delete** | Removed to ensure the application runs purely on live backend APIs. |
| `frontend/src/store/useDemoStore.ts` | Dead Component | Zustand state store driving the demo page transitions. | **Delete** | Removed completely. |
| `frontend/src/app/forecast/page.tsx` | Commented Code | Contained a `useEffect` hook referencing demo state to override selected scenario. | **Modify** | Removed `useDemoStore` imports and state logic. |
| `frontend/src/app/project-health/page.tsx` | Commented Code | Contained a `useEffect` hook referencing demo state to auto-open project drawers. | **Modify** | Removed demo-store variables and hooks. |
| `frontend/src/app/copilot/page.tsx` | Commented Code | Contained a `useEffect` hook triggering automatic search prompts during the tour. | **Modify** | Removed tour hooks and effects. |
| `frontend/src/app/recommendation/page.tsx` | Commented Code | Declared but unused `useDemoStore` hooks. | **Modify** | Cleaned up unused imports and state variables. |
| `frontend/src/components/dashboard-shell.tsx` | Duplicate/Demo | Rendered demo buttons and overlay elements. | **Modify** | Cleaned up the layout menu, leaving only "AI Insights" and global toast overlays. |
| `backend/Dockerfile` | Unoptimized | Copied the entire project including frontend and virtual environments. | **Modify** | Optimized with a `.dockerignore` file, restricting copy to backend modules, and changed start command to use the startup orchestrator. |
| `docker-compose.yml` | Incomplete Stack | Excluded the Next.js frontend and lacked service health dependency locks. | **Modify** | Productionized to include the `frontend` container, healthchecks, network segmentation, named volumes, and service start ordering. |
| `.gitignore` | Incomplete | Did not cover Next.js build folders, database files, and model files. | **Modify** | Expanded to comprehensively block Node/Next/Python/IDE/Database artifacts. |
