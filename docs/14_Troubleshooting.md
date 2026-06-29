# Troubleshooting Guide

This guide details diagnostics steps and recovery actions for common platform setup and execution issues.

---

## 1. Relational Database Sync Failures
- **Symptom**: Startup loops with messages like "PostgreSQL is not accepting connections".
- **Diagnosis**: The Postgres container is still initializing its raw data volumes.
- **Action**: Check postgres logs using `docker logs resource-postgres`. If health checks fail repeatedly, reset the volume using `docker-compose down -v` and restart.

---

## 2. Ollama / LLM Connectivity & Timeout Exceptions
- **Symptom**: AI Insights drawers or candidate match score explanations return generic fallbacks or throw network timeouts.
- **Diagnosis**: The local Ollama model (`qwen2.5:7b` or similar) is not pulled, or Ollama service is not running.
- **Action**:
  - Run `docker exec -it resource-ollama ollama pull qwen2.5:7b` inside the Ollama container to verify model availability.
  - Test connectivity from the backend container: `curl http://ollama:11434/api/tags`.

---

## 3. Qdrant Index Reload or Vector Out Of Memory (OOM) Errors
- **Symptom**: Embeddings synchronization scripts fail with payload structure errors.
- **Diagnosis**: Vector collection properties do not match model dimensions (384 vs. 512).
- **Action**:
  - Verify that the SentenceTransformers model configured matches settings definitions.
  - Delete collections via Qdrant dashboard: `DELETE http://localhost:6333/collections/employees` and trigger synchronization.

---

## 4. Frontend Cross-Origin Resource Sharing (CORS) or API Failures
- **Symptom**: All dashboard widget totals display zero, or resource recommendations tables remain blank.
- **Diagnosis**: The browser client is unable to fetch data from `NEXT_PUBLIC_API_URL` (usually `http://localhost:8000`).
- **Action**: Open browser inspect console logs and verify network errors. If the backend is running, verify port bindings using `netstat -ano | findstr 8000` (on Windows) to ensure no conflicting servers are running.
