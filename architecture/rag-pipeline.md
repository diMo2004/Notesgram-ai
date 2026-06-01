# RAG Pipeline — Implementation Guide (MVP)

This document describes the Retrieval-Augmented Generation (RAG) pipeline for the Notesgram MVP. Each stage lists Input, Output, Purpose and concise failure/operational notes. An ASCII flow diagram summarizes the end-to-end flow.

Overview
- Goal: ingest PDFs → extract text → chunk → embed → persist vectors → enable semantic retrieval + LLM generation with citations.
- Components: Frontend uploader, Backend API, Background worker (ingestion + embedding), Embedding service (external or local), PostgreSQL+pgvector store, Generator (LLM provider)

Stages

1) PDF Upload
- Input: PDF file bytes, filename, uploader metadata
- Output: `documents` row (id, filename, file_path), file stored (local disk or object storage), HTTP 202 accepted
- Purpose: accept user file and persist a source pointer; enqueue processing job
- Failure handling: validate file size/type; on failure return 4xx; if storage fails set document status `FAILED` and record error in metadata

2) Text Extraction
- Input: stored PDF file path / bytes
- Output: raw extracted text (or per-page text array), raw OCR metadata if applicable
- Purpose: convert binary PDF → plain text for chunking
- Failure handling: if extraction fails, mark document `FAILED`; try fallback (OCR) for scanned PDFs; log page-level errors

3) Chunking
- Input: extracted text (string or pages)
- Output: ordered list of chunks [{chunk_index, content, metadata}]
- Purpose: split long text into retrieval-sized fragments preserving provenance (page, offsets)
- Implementation notes: use token-based chunk size (~500–1000 tokens) + overlap (10–30%) to preserve context; record `chunk_index` and source offsets
- Failure handling: if a chunk exceeds size limits, truncate and log; skip empty chunks

4) Embedding Generation
- Input: chunk content (text)
- Output: embedding vector (float array) per chunk
- Purpose: convert chunks to vector space for semantic similarity
- Implementation notes: batch embedding requests for throughput; keep embedding dimension constant; record model name and dimension in chunk metadata
- Failure handling: retry transient errors with backoff; on persistent failure mark chunk embedding failed and surface to monitoring

5) Vector Storage
- Input: chunk rows with embedding vectors
- Output: persisted `chunks` rows with `embedding` (pgvector) and indexes updated
- Purpose: make embeddings queryable via pgvector; keep chunk metadata to map hits back to source
- Implementation notes: write in batches, use transactions per document or per N chunks; ensure `vector(N)` column matches embedding size
- Failure handling: on DB constraint error rollback batch, mark document `FAILED` if unrecoverable; keep retries idempotent

6) Query Processing
- Input: user natural-language query text
- Output: normalized query (optionally expanded), query embedding vector
- Purpose: prepare query for semantic retrieval
- Implementation notes: optionally perform simple normalization (lowercase, strip) and optionally expand using query rewriters; generate query embedding using same model used for chunks
- Failure handling: on embedding service error return a user-friendly error or fallback to text search

7) Semantic Retrieval
- Input: query embedding (and optional filters/metadata)
- Output: ranked candidate chunks (id, score, content, document_id, metadata)
- Purpose: find relevant chunks via vector nearest-neighbors + optional hybrid (text) reranking
- Implementation notes: use `ORDER BY embedding <-> query` with LIMIT K (e.g. 50) then rerank top N by heuristic (BM25 on content, recency, doc status)
- Failure handling: if vector search fails, fallback to text search using `to_tsvector` GIN index

8) Context Assembly
- Input: top retrieved chunks, document metadata, request context (max tokens)
- Output: assembled context (trimmed concatenation of chunks) and citation list mapping content ranges → sources
- Purpose: select and format retrieved facts to provide to the LLM as context while respecting token limits
- Implementation notes: prefer highest-scoring chunks but maintain source diversity (limit 1–2 chunks per document initially); build context until token budget reached; include chunk identifiers for citation
- Failure handling: if no candidates found, return empty context and proceed (LLM should be instructed to say 'no sources found')

9) Prompt Construction
- Input: user question, assembled context, prompt templates, system instructions
- Output: final LLM prompt payload (system + context + user question + citation instructions)
- Purpose: create a deterministic, auditable prompt that instructs the LLM to answer using retrieved context and include citations
- Implementation notes: use a template that asks for concise answers and explicit citations (e.g., bracketed chunk ids) and a final 'sources' section

10) LLM Generation
- Input: final prompt payload
- Output: generated answer text, token usage, LLM debug data
- Purpose: synthesize an answer grounded in provided context
- Failure handling: handle API rate limits/retries; if LLM returns hallucinated sources, post-process to check that cited chunk ids exist; fallback to shorter or safer reply when LLM fails

11) Citation Creation
- Input: LLM output and the list of retrieved chunk ids used for context
- Output: structured citation objects (document_id, chunk_id, snippet, page_number, confidence)
- Purpose: expose provenance for each claim in the answer and enable source linking
- Implementation notes: produce a citations array alongside the answer; include `source_metadata` (filename, file_path, page)
- Failure handling: if mapping from cited text to chunk fails, return best-effort citations and mark as partial

ASCII Flow Diagram

Upload -> Extract -> Chunk -> Embed -> Store ->
    Query -> EmbedQuery -> Retrieve -> Assemble -> Prompt -> LLM -> Answer + Citations

More detailed linear diagram:

 [User Upload]
     |
     v
 [Store file] -> [Enqueue job]
     |
     v
 [Text Extraction]
     |
     v
 [Chunking] ---> [Chunk metadata]
     |
     v
 [Embedding Service]
     |
     v
 [Persist Chunks + Embeddings (pgvector)]

-- Query time --
 [User Query]
     |
     v
 [Query Embedding] -> [Vector Search (pgvector)] -> [Top candidates]
     |
     v
 [Context Assembly (trim & dedupe)] -> [Construct Prompt with citations]
     |
     v
 [LLM] -> [Answer + Citation List] -> [Return to user]

Failure Handling (global)
- Observability: log per-document and per-chunk errors, track processing durations and failure rates
- Retries: exponential backoff for embedding and LLM API calls; idempotent writes using document+chunk identifiers
- Partial results: allow returning partial ingestion results (some chunks persisted) and mark document `COMPLETED_PARTIAL` or keep `COMPLETED` while flagging missing chunks
- Alerts: surface high failure rates to monitoring and fail fast for systemic issues

Retrieval quality considerations (MVP)
- Chunk size & overlap: tune chunk token size (500–1000 tokens) and overlap (10–30%) to balance context and precision
- Embedding model: use a single stable model for both chunks and queries; evaluate recall on sample QA pairs
- Candidate pool & reranking: retrieve a larger set (K=50) then rerank top N (e.g., 10) with hybrid signals (BM25, recency, doc status)
- Diversity: limit top results per document to avoid single-source dominance
- Evaluation: add offline tests (human-labeled Q→relevant chunks) and automated metrics (MRR, recall@k)

Future extension points
- Vector DB alternatives: swap pgvector for specialized vector DBs (Milvus, Weaviate, Pinecone) if scale/ops warrant
- Incremental embeddings: update or re-embed chunks when embedding model changes; store model version in metadata
- Adaptive chunking: create variable-length chunks based on semantic boundaries (sections, headings)
- Rerankers & feedback: integrate trained cross-encoders or user feedback loops to improve ranking
- Caching: query embedding/result caching and LRU of recent retrievals
- Multilingual support: detect language and use appropriate embedding models or translation+embedding flow

Implementation checklist (quick)
- [ ] Add ingestion worker (enqueue on upload)
- [ ] Implement extractor (pdfminer/pdfplumber + Tesseract fallback)
- [ ] Implement chunker with token counting and overlap
- [ ] Add embedding client and batcher
- [ ] Persist `chunks` with `vector(N)` column and create vector index
- [ ] Implement query pipeline with reranking and context assembly
- [ ] Create prompt templates that require explicit citations

Document history
- Created: 2026-06-01
