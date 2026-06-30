# Deployment

This document details the Docker network, service discovery, container configurations, and environment variables used to deploy the platform.

---

## 1. Docker Compose Configurations
The platform uses Docker Compose (`docker-compose.yml`) to orchestrate six interconnected services:
- **`db`** (`resource-postgres`): Relational store. Port `5432:5432`.
- **`redis`** (`resource-redis`): High-speed key-value cache layer. Port `6379:6379`.
- **`qdrant`** (`resource-qdrant`): Vector search engine. Ports `6333:6333` and `6334:6334`.
- **`ollama`** (`resource-ollama`): Local LLM runtime. Port `11434:11434`.
- **`backend`** (`resource-backend`): FastAPI service gate. Port `8000:8000`.
- **`frontend`** (`resource-frontend`): Next.js SPA client app. Port `3010:3010`.

---

## 2. Docker Networking
All containers run on a custom bridge network called `resource-network`.
- Containers resolve each other using service names (e.g., the backend connects to Postgres via host `db:5432` and Redis via host `redis:6379`).
- The frontend exposes `NEXT_PUBLIC_API_URL=http://localhost:8000` because client requests are processed in the user's browser, which connects to the backend through host port forwarding.

---

## 3. Container Health Checks & Startup Sequence
Startup order is managed using Docker health checks:
1. **`db`**: Verified using `pg_isready -U postgres`.
2. **`redis`**: Verified using `redis-cli ping`.
3. **`ollama`**: Verified using `ollama list || exit 1`.
4. **`backend`**: Launches only after `db`, `redis`, and `ollama` are healthy, verified using `curl -f http://127.0.0.1:8000/api/health || exit 1`.
5. **`frontend`**: Launches only after `backend` is evaluated as healthy.

