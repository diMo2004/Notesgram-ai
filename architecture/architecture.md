## Plan: AI Knowledge Workspace MVP

Build the MVP from a blank workspace: scaffold a FastAPI backend, a Next.js frontend, and local infrastructure for PostgreSQL with pgvector. The implementation should follow the spec’s three prioritized flows in order: PDF ingestion, question answering, and citations. Because the repo currently has no application code, the plan includes foundational project setup, data model design, the RAG pipeline, prompt management, UI wiring, architecture decision records, and end-to-end validation.

**Steps**
1. Establish the application skeletons first, with a backend service and frontend app as separate top-level areas, plus Docker Compose for local PostgreSQL with pgvector. This is the base dependency for every feature that follows.
2. Define the core domain and storage model for documents, chunks, processing status, questions, answers, citations, and prompt versions. This includes the PostgreSQL schema and the service boundaries needed for ingestion, retrieval, and response generation.
3. Implement the ingestion pipeline end to end: accept PDF uploads, store the file, extract text, chunk it, generate embeddings, and persist chunk metadata plus vector representations in PostgreSQL. This step should also define failure handling for unreadable files, partial processing, and explicit document processing status transitions.
4. Implement the retrieval and answering flow: convert user questions into embeddings, perform semantic search over chunk embeddings, assemble context, call the LLM, and return grounded answers with citations. Keep the generation layer isolated behind a provider interface so the LLM provider can be swapped without changing business logic.
5. Add a prompt management layer that stores and resolves versioned prompts for ingestion, retrieval, and answer generation. Treat prompts as first-class operational artifacts so changes can be reviewed and rolled out independently of application code.
6. Build the frontend workflow: upload documents, show processing status, provide a question input, render the answer, and display citations in a readable source list. This is the user-facing slice that exercises the backend APIs.
7. Add API versioning to the backend routes and response contracts so the public surface can evolve without breaking existing clients. Keep version-specific behavior isolated at the routing boundary.
8. Add observability and validation for the MVP slice: request logging, processing status visibility, retrieval quality validation, and tests for upload, retrieval, no-answer handling, prompt resolution, and citation coverage. Finish with an end-to-end check that proves the full user flow works.
9. Write architecture decision records for the major design choices, including pgvector over ChromaDB, API versioning, prompt management, retrieval validation, and the LLM abstraction. Keep ADRs lightweight but explicit so future changes stay traceable.

**Relevant files**
- `backend/pyproject.toml` — backend dependency and tooling setup for FastAPI, Pydantic, PDF processing, database access, vector search, and test tooling
- `backend/app/main.py` — API application entrypoint and route registration
- `backend/app/api/v1/uploads.py` — versioned PDF upload endpoint and processing trigger
- `backend/app/api/v1/questions.py` — versioned question-answer endpoint for retrieval and generation
- `backend/app/services/ingestion.py` — text extraction, chunking, metadata preservation, and persistence orchestration
- `backend/app/services/retrieval.py` — semantic search against pgvector-backed embeddings
- `backend/app/services/generation.py` — prompt assembly and response generation with citations
- `backend/app/services/prompts.py` — prompt resolution, versioning, and prompt template loading
- `backend/app/services/llm.py` — provider abstraction for swappable model execution
- `backend/app/validation/retrieval.py` — retrieval quality checks, evaluation harness, and regression rules
- `backend/app/models/` — domain models and Pydantic schemas for documents, processing status, chunks, questions, answers, citations, and prompts
- `backend/app/db/` — PostgreSQL session, repositories, pgvector integration, and migration-ready schema helpers
- `frontend/package.json` — Next.js app setup and scripts
- `frontend/app/page.tsx` — MVP user flow entry page
- `frontend/components/` — upload form, question form, status display, answer display, and citation display components
- `docker-compose.yml` — local PostgreSQL services with pgvector enabled
- `architecture/database-design.md` — data model, status lifecycle, and persistence design notes
- `architecture/rag-pipeline.md` — ingestion, retrieval, generation, and prompt pipeline design notes
- `architecture/adr/` — decision records for storage, API versioning, prompt management, retrieval validation, and provider abstraction
- `specs/mvp-rag.md` — source of truth for scope, priorities, and success criteria

**Verification**
1. Run backend unit and integration tests for upload processing, status transitions, chunk creation, pgvector retrieval, prompt resolution, and citation formatting.
2. Run retrieval quality validation against a small golden set to confirm the top-k results and answer grounding meet the expected threshold.
3. Run frontend checks for build and route rendering after the upload, status, and question UI are wired.
4. Run an end-to-end smoke test that uploads a sample PDF, asks a question, and confirms the answer includes citations tied to the uploaded source.
5. Confirm a negative-path test where an unsupported or unreadable PDF fails gracefully, updates processing status correctly, and does not block other documents.

**Decisions**
- Treat the spec as the primary authority because the architecture docs are currently empty.
- Keep the backend and frontend as separate top-level applications to match the stated FastAPI plus Next.js stack.
- Use PostgreSQL with pgvector for document metadata and vector similarity search so storage and retrieval stay in one operational boundary.
- Expose document processing status as a first-class concept so the UI can show progress and failure states clearly.
- Keep prompts, retrieval logic, and LLM execution behind dedicated service layers so provider swaps and prompt changes do not alter business logic.
- Exclude authentication, multi-user workspace support, OCR, flashcards, quizzes, summaries, and agent workflows from this MVP.

**Further Considerations**
1. The current repo has no application scaffolding, so the first implementation pass should focus on project bootstrap before feature logic.
2. If you want the plan broken into execution tasks next, the next step is to generate `tasks.md` from this spec and plan.