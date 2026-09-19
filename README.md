# DocuGauge | High-Precision Document Intelligence Platform

DocuGauge is a privacy-centric, full-stack Retrieval-Augmented Generation (RAG) platform designed to ingest unstructured documents, compute dense vector representations locally, and perform grounded semantic search with verified chunk-level and page-level source citations.

---

## Tech Stack
- Backend: Python 3.11, FastAPI, SQLAlchemy 2.0 (asyncpg), Pydantic v2
- Vector Database: PostgreSQL 16 + pgvector (IVFFlat indexing, cosine distance)
- Embeddings & LLM: Ollama (nomic-embed-text 768-d, llama3.2)
- Frontend: React, Vite, Tailwind CSS, Lucide React, Axios
- DevOps: Docker, Docker Compose, Nginx

---

## Quickstart

`ash
# Deploy via Docker Compose
docker compose up --build
`
