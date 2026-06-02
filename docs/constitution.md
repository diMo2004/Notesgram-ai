# Vision
Build an AI-powered personal knowledge system where users can upload documents, organize knowledge, perform semantic search, and interact with documents through Retrieval-Augmented Generation (RAG).

The project is a knowledge platform that uses AI, not a chatbot that happens to store documents.

# Core Principles

1. Knowledge First, Chat Second

- Uploaded knowledge is the primary asset.
- Chat is one interface to access knowledge.

2. Explainable Retrieval

- Every answer must be traceable to retrieved document sources.
- Citations are mandatory.

3. AI Augments Learning

- AI should help users understand and learn from documents.
- AI should not replace critical thinking.

4. Backend Quality Over UI Polish

- Correctness, retrieval quality, and architecture take priority over visual features.

5. Technology Choices Must Be Explainable

- Every major component must have a documented reason for existing.

6. Framework Independence

- Concepts and architecture are more important than framework-specific implementations.

7. Measure Quality Over Feature Count

- Retrieval quality, latency, and citation accuracy matter more than the number of features.

8. Incremental Delivery

- Every milestone should produce a working system.

9. Production Mindset

- Handle failures, invalid inputs, and edge cases gracefully.

10. Learn Through Implementation

- The project exists to develop engineering and GenAI skills, not just produce a demo.

# Technical Standards

- FastAPI backend
- PostgreSQL + pgvector
- Next.js frontend
- Docker-based development environment
- API versioning (/api/v1)
- Retrieval-Augmented Generation architecture

# Success Definition
The project succeeds if I can confidently explain:

- embeddings
- chunking
- retrieval
- citations
- vector search
- FastAPI architecture
- database design
- deployment decisions
- system tradeoffs
