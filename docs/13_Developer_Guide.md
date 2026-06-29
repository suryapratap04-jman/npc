# Developer Guide

This guide describes how to set up the development environment, load databases, trigger profile indexing, and verify compilation.

---

## 1. Local Environment Requirements
- Python 3.10+
- Node.js 18+ (with npm)
- Docker & Docker Compose

---

## 2. Setting Up Backend Services
1. **Initialize virtual environment**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Configure environment Variables**:
   Copy `.env.example` in root to `.env` and configure credentials.
3. **Database initialization and seeding**:
   - Clean data: `python scripts/cleaning/clean_data.py` (saves processed CSVs).
   - Sync Relational database schemas: Seeding is executed automatically during backend startup, or run database setup scripts in `scripts/ops/`.

---

## 3. Setting Up Frontend Client
1. **Install Node packages**:
   ```bash
   cd frontend
   npm install
   ```
2. **Launch dev environment**:
   ```bash
   npm run dev
   ```
   The client compiles local files and becomes available at `http://localhost:3000`.

---

## 4. Embedding Generation & Vector Sync
To rebuild Qdrant vector indices, trigger indexing using the settings page sync buttons, or execute manually:
```bash
python -m backend.embeddings.generate_embeddings
```

---

## 5. Build Verification
Run standard package audits before committing changes:
```bash
# Verify TypeScript compilation and packaging
cd frontend
npm run build
```
Ensure compile and lint stages execute with zero warnings or errors.
