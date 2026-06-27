# Repository Structure

This document outlines the organization and purpose of the directories and files in the AI Resource Management Platform repository.

```
project/
├── .github/                       # GitHub actions pipelines and templates
├── backend/                       # FastAPI Backend application code
│   ├── config/                    # Configuration settings and env parser
│   ├── copilot/                   # AI Conversational Copilot service logic
│   ├── database/                  # SQL database schemas, models, and sessions
│   ├── embeddings/                # Vector profile extraction and indexing
│   ├── forecast/                  # Rolling 6-month forecasting sub-engines
│   ├── health/                    # Project risk heuristics diagnostics
│   ├── llm/                       # Provider adapters (Ollama, Gemini, Grok)
│   ├── rag/                       # RAG retriever and prompt generators
│   ├── recommendation/            # Multi-strategy candidate ranking engine
│   ├── scripts/                   # Seeding and startup scripts
│   ├── tests/                     # Suite of backend validation tests
│   ├── Dockerfile                 # Backend python image builder
│   ├── main.py                    # Root FastAPI router and setup configurations
│   └── requirements.txt           # Python backend dependencies
├── datasets/                      # Directory for data storage (ignored by git)
│   ├── raw/                       # Unstructured raw files
│   ├── cleaned/                   # Deduplicated, standardized CSV inputs
│   └── experiments/               # Metrics and operational performance reports
├── deployment/                    # Cloud deployment scripts and resources
├── docker/                        # Multi-environment docker compose config files
├── docs/                          # Architecture, system, and api guidelines
│   ├── archive/                   # Archived phase implementation plans
│   ├── api.md                     # Endpoint documentation
│   ├── architecture.md            # System layout guide
│   ├── database_design.md         # Database relational model schema
│   ├── deployment.md              # Container networking and volumes guide
│   ├── migration_summary.md       # Migration and validation summaries
│   ├── project_health.md          # Health heuristics details
│   ├── repository_audit.md        # File cleanup registry
│   ├── repository_structure.md    # (This file)
│   └── vector_database.md         # Vector database collections setup
├── frontend/                      # Next.js Frontend application code
│   ├── public/                    # Static assets
│   ├── src/                       # Source code files
│   │   ├── app/                   # App Router pages and CSS layouts
│   │   ├── components/            # Shared UI components and layout shells
│   │   ├── lib/                   # Design token definitions and utility functions
│   │   └── services/              # Client API wrappers calling the backend
│   ├── Dockerfile                 # Next.js multi-stage build script
│   ├── package.json               # Frontend dependencies and npm scripts
│   └── tsconfig.json              # TypeScript configuration
├── scripts/                       # Reusable tooling and pipeline scripts
│   ├── cleaning/                  # Dataset profiling, cleaning, and validation scripts
│   ├── notebooks/                 # Jupyter notebook documentation
│   ├── scratch/                   # Developer sandbox files
│   └── ops/                       # Operational start/stop/reset scripts
├── .dockerignore                  # Docker build ignores
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git tracking ignores
├── docker-compose.yml             # Main Docker Compose configuration
└── README.md                      # Professional master repository guide
```
