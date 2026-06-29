# AI Copilot Engine

This document details the backend architectures, intent routing engines, and generative pipelines of the AI Copilot assistant (`backend/copilot/`).

---

## 1. Intent Classification Routing
Every user query sent to the Copilot (`/api/copilot/chat`) passes through a router:
1. **Intent Analysis**: The input text is classified using the local LLM or heuristics:
   - `intent == "recommendation"`: Triggered by resource matching keywords.
   - `intent == "health"`: Triggered by project risk or budget keywords.
   - `intent == "forecast"`: Triggered by capacity planning keywords.
2. **Context Enrichment**: The system fetches corresponding database tables (health summaries, forecast timelines, or candidate profiles) and injects them into the RAG context.
3. **Structured Response Synthesis**: Generates a conversational response along with structured chart, table, or card data widgets for UI rendering.

---

## 2. Fit Diagnostics & RAG Explanation
The Copilot exposes a dedicated diagnostics endpoint `POST /api/copilot/explain`:
- **Function**: Invoked when a user requests an in-depth fit report for a specific employee on a project.
- **Context Injection**: Gathers candidate's skills, competencies, and current project allocations.
- **Output**: Returns a detailed markdown analysis explaining the fit.

---

## 3. Session & History Logs
- **Session Keys**: Chat sessions are tracked via a `session_id` query parameter (default: "default").
- **Persistence**: Maintains conversation histories to support multi-turn dialogues and context retention.
