# 11. Deployment

This document describes how to deploy the platform using Docker and local scripts.

## 1. Multi-Container Orchestration
Using `docker-compose.yml`:
- **resource-postgres**: Relational PostgreSQL 16 database.
- **resource-redis**: Caching store.
- **resource-qdrant**: Vector search engine.
- **resource-backend**: FastAPI application.
- **resource-frontend**: Next.js client dashboard.

## 2. Execution Commands
```bash
# Build and run containers
docker-compose up --build -d

# Verify system logs
docker-compose logs -f
```
