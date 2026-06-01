# Milestone 1 — RAG MVP Tasks

1. Project setup
   - Initialize repo structure (backend, frontend, infra)
   - Add `docker-compose.yml` and `.env.example`
2. Database (Postgres + pgvector)
   - Add postgres service with pgvector enabled
   - Create initial schema: documents table (id, content, embedding vector, metadata)
   - Add basic migration SQL (seed optional)
3. Backend (FastAPI)
   - Create minimal FastAPI app with health endpoint
   - Add API route to ingest documents (POST /api/v1/docs)
   - Add API route to query documents (POST /api/v1/query) — returns nearest neighbours
   - Wire DB connection (placeholder using DATABASE_URL env)
4. Frontend (Next.js)
   - Minimal page showing status and a simple query form
   - Connect to backend health endpoint
5. Local infra
   - Add `docker-compose.yml` with db + optional mock-llm
   - Add `.env.example` with credentials and ports
6. Tests & verification
   - Smoke test backend health endpoint
   - Smoke test frontend loads page
7. Documentation
   - Short README for backend explaining how to run locally
