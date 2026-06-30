# 12. Repository Structure

This document details the folder layout and files of the repository.

```
├── backend/                  # FastAPI Application
│   ├── cache/                # Redis Caching Services
│   │   ├── cache_keys.py     # Namespace definitions
│   │   └── cache_service.py  # Cache get/set/invalidate helpers
│   ├── config/               # Settings & Variables
│   ├── database/             # Postgres Schemas & Connections
│   │   ├── models.py         # SQLAlchemy definitions
│   │   └── session.py        # DB session initializer
│   ├── embeddings/           # Vector Indexing
│   │   └── generate_embeddings.py # Vector generation
│   ├── forecast/             # Forecast Engine
│   │   └── service.py        # Supply/demand calculations
│   ├── health/               # Project Health Engine
│   │   └── service.py        # Risk analytics calculations
│   ├── llm/                  # AI/LLM Provider Classes
│   ├── recommendation/       # Candidate Scoring Engine
│   │   ├── scoring_engine.py # Blended metric scorer
│   │   └── utilization.py    # Audited utilization engine
│   └── main.py               # Application Gateway
├── datasets/                 # Datasets
│   ├── cleaned/              # Cleaned CSV data tables
│   └── raw/                  # Raw CSV files
├── docs/                     # Documentation files
├── frontend/                 # Next.js UI App
└── scripts/                  # Cleaning & Pipeline Scripts
```
