# Database design — MVP (Postgres + pgvector)

This document describes a compact, implementation-focused database schema for the Notesgram RAG MVP using PostgreSQL with the `pgvector` extension.

Goals
- Store documents and derived text chunks
- Persist embeddings (vectors) for semantic search
- Track processing lifecycle and citations for explainability

Assumptions
- Embedding dimension is fixed and known (example: 1536). Set at ingestion time.
- Embeddings are produced by an external service (worker or API) and written into the DB.

---

Entities (overview)

1) Document
- Purpose: store metadata about an uploaded file and track processing state.
- Core fields: `id`, `filename`, `file_path`, `status`, `created_at`, `processed_at`, `metadata`

2) Chunk
- Purpose: store text chunks derived from a Document, plus their embeddings for vector search.
- Core fields: `id`, `document_id`, `chunk_index`, `content`, `embedding`, `created_at`

3) Citation
- Purpose: record which document/chunk(s) were used as sources for a generated answer (RAG citation). Keeps provenance and optional offsets/page numbers.
- Core fields: `id`, `document_id`, `chunk_id`, `source_metadata`, `created_at`

---

Processing status lifecycle

Allowed states (MVP):
- `UPLOADED` — file received but not yet processed
- `PROCESSING` — ingestion / chunking / embedding in progress
- `COMPLETED` — ingestion finished successfully and chunks+embeddings persisted
- `FAILED` — processing error; store error details in `metadata` or logs

Typical transitions:
- `UPLOADED` -> `PROCESSING` -> `COMPLETED`
- `UPLOADED` -> `PROCESSING` -> `FAILED` (retry possible)

Implementation notes:
- Use a background worker (Celery, RQ, or a simple job queue) to process uploads and update `documents.status` and `processed_at`.
- Use transactions: create `documents` row in UPLOADED, then set PROCESSING when worker picks it up.

---

ER-style relationships (text)
- One `Document` has many `Chunk` rows (1:N).
- One `Chunk` may have many `Citation` rows referring to it (1:N).
- A `Citation` references both a `Document` and a `Chunk`. This lets citations point to the original document (document-level) and the exact chunk(s) used for an answer.

Diagram (conceptual):

Document (1) --- (N) Chunk (1) --- (N) Citation
Document (1) --- (N) Citation

Cascade semantics: deleting a document should cascade-delete chunks and citations (MVP behaviour).

---

Rationale for each table (MVP)
- `documents`: Single place to track file metadata and processing lifecycle. Keeps per-file provenance and source URI/path.
- `chunks`: Normalized storage of text fragments with embedding vectors for retrieval. Storing chunk index preserves order to map back to the original document location.
- `citations`: Keeps links between generated answers and the original sources for explainability and auditability.

---

SQL DDL (MVP-ready)

-- Enable extensions (run once in migration)
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()

-- Optional enum for processing status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'processing_status') THEN
        CREATE TYPE processing_status AS ENUM ('UPLOADED','PROCESSING','COMPLETED','FAILED');
    END IF;
END $$;

-- Documents
CREATE TABLE documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    filename text NOT NULL,
    file_path text, -- path or object storage key
    status processing_status NOT NULL DEFAULT 'UPLOADED',
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz
);

CREATE INDEX ON documents (status);
CREATE INDEX ON documents (created_at);

-- Chunks
-- NOTE: Set the vector dimension to the embedding size you use (example: 1536)
CREATE TABLE chunks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    embedding vector(1536),
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);

-- Indexes for chunks
CREATE INDEX ON chunks (document_id, chunk_index);
-- Full-text index for fallback text search (optional but useful)
CREATE INDEX chunks_content_fts_idx ON chunks USING gin (to_tsvector('english', content));

-- Vector index (choose one based on pgvector version and workload)
-- HNSW (recommended for robust recall / latency tradeoffs when supported):
-- CREATE INDEX chunks_embedding_hnsw_idx ON chunks USING hnsw (embedding) WITH (m=16, ef_construction=200);

-- IVFFlat (alternative; requires tuning `lists` and ANALYZE):
-- CREATE INDEX chunks_embedding_ivfflat_idx ON chunks USING ivfflat (embedding) WITH (lists = 100);

-- Citations
CREATE TABLE citations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id uuid NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    page_number integer,
    start_offset integer,
    end_offset integer,
    source_metadata jsonb DEFAULT '{}'::jsonb, -- e.g. {"uri":"s3://...","confidence":0.8}
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ON citations (document_id);
CREATE INDEX ON citations (chunk_id);

---

Sample queries (MVP)

-- Insert a document record (app-level):
INSERT INTO documents (filename, file_path) VALUES ($1, $2) RETURNING id;

-- Insert a chunk and its embedding (embedding is a float array passed as parameter):
INSERT INTO chunks (document_id, chunk_index, content, embedding)
VALUES ($1, $2, $3, $4::vector)
RETURNING id;

-- Semantic search: nearest neighbours by L2 (example, parameterized embedding)
SELECT id, document_id, chunk_index, content
FROM chunks
ORDER BY embedding <-> $1::vector
LIMIT 5;

-- Alternative: retrieve with document metadata join
SELECT c.id, c.chunk_index, c.content, d.filename
FROM chunks c
JOIN documents d ON d.id = c.document_id
ORDER BY c.embedding <-> $1::vector
LIMIT 5;

---

Indexing considerations and tuning (practical)
- Vector index: HNSW is recommended for its general-purpose accuracy and latency tradeoffs; IVFFlat can be faster with more tuning but requires reindexing and careful `lists` and `probe` parameters.
- After creating an IVFFlat index, run `ANALYZE chunks;` so the planner has statistics.
- Keep embedding dimension consistent across the DB. If you change model/dimension, you must migrate the column type.
- Add a partial index on `documents(status)` for queries that frequently scan `PROCESSING` records:
  CREATE INDEX documents_processing_idx ON documents (id) WHERE (status = 'PROCESSING');
- Use a GIN index on `metadata` if you query JSON fields frequently.
- Use `to_tsvector` + GIN for fast text-based fallback search.

pgvector usage notes
- Store embeddings in `vector(N)` where `N` is the embedding dimension.
- Query operators: `embedding <-> query` (L2), `embedding <=> query` (cosine when vectors normalized), and functions in `pgvector` for similarity.
- Parameterize embedding inputs; send the embedding as a typed parameter (binary/array) from the application layer.

Migration ordering (recommended)
1. Enable extensions (`pgvector`, `pgcrypto`).
2. Create `processing_status` type.
3. Create `documents`, then `chunks`, then `citations` tables.
4. Create text and vector indexes.
5. Run ANALYZE and any index-specific tuning.

Operational notes (MVP)
- Background worker writes chunk rows and embeddings in batches (transaction per document or per N chunks).
- Update `documents.status` to `PROCESSING` at worker start, and to `COMPLETED`/`FAILED` at finish.
- For large files, chunk and write iteratively to avoid long transactions.
- Consider storing the original file in object storage (S3) and keeping `file_path` as a pointer.

Next steps (implementation)
- Add a DB migration to create the above objects.
- Implement a small repository layer in the backend to insert documents, chunks, and perform vector search.
- Add a background worker to process uploaded files and call an embedding service.

---

Document history
- Created: 2026-06-01
