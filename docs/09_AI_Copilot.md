# 09. AI Copilot

This document describes the AI Orchestration layer and the deprecation of the conversational UI.

## 1. Simplified Dashboard Architecture
The conversational chat interface (`/copilot`) was deprecated to provide a cleaner dashboard UX. Users view structured widgets directly in:
- **Resource Recommendation Dashboard**
- **Project Health Monitor**
- **Forecast Workbench**

## 2. Backend LLM Providers
The LLM orchestration engine (`backend/llm`) remains active in the backend:
- File location: `backend/llm/`
- Providers: Ollama (`ollama_provider.py`), Gemini (`gemini_provider.py`), Grok (`grok_provider.py`).
- **Use Case**: Automatically generating fit explanations in the recommendation engine (via `backend/recommendation/explanation_engine.py`) and summary text diagnostics for health and forecasts.
