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

---

## Retrieval & Reranking Architecture

DocuGauge uses a **two-stage hybrid retrieval and reranking engine** to eliminate lexical blind spots (e.g., exact part numbers, acronyms, section headers) while preserving deep semantic search precision.

```text
User Query
    │
    ├───► [Embedding Model] ───► pgvector HNSW Search (Cosine Distance)  ──┐
    │                                                                      │ (Top-20)
    └───► [plainto_tsquery] ───► tsvector Sparse Search (GIN Index)       ──┴──► Reciprocal Rank Fusion (RRF)
                                                                                   │
                                                                                   ▼ (Top-15 Candidates)
                                                                          FlashRank Cross-Encoder
                                                                          (ms-marco-TinyBERT-L-2-v2)
                                                                                   │
                                                                                   ▼ (Top-K Re-scored)
                                                                          Grounded LLM Synthesis + Citations
```

### 1. Stage 1: Dual-CTE Hybrid Retrieval with RRF
Search queries run concurrently inside PostgreSQL via a single Common Table Expression (CTE):
* **Dense Semantic Search:** Uses `pgvector` to compute vector distances over embeddings.
* **Sparse Lexical Search:** Uses a generated `tsvector` column (`content_fts`) backed by a PostgreSQL GIN index with `ts_rank`.
* **Reciprocal Rank Fusion:** Fuses disparate score scales using rank-based weighting:
  $$RRF(d) = \sum_{m \in M} rac{1}{60 + r_m(d)}$$

### 2. Stage 2: In-Process Cross-Encoder Reranking
Top RRF candidate chunks pass into **FlashRank** (`ms-marco-TinyBERT-L-2-v2`), a lightweight ONNX-quantized cross-encoder running directly in-process on CPU:
* Computes token-level cross-attention across `(query, document_chunk)` pairs.
* Re-scores candidates into calibrated relevance confidences (e.g., `0.99+` precision) prior to LLM prompt injection.
* Operates locally with sub-10ms overhead, ensuring zero third-party data egress.

---

## Retrieval & Reranking Architecture

DocuGauge uses a **two-stage hybrid retrieval and reranking engine** to eliminate lexical blind spots (e.g., exact part numbers, acronyms, section headers) while preserving deep semantic search precision.

```text
User Query
    │
    ├───► [Embedding Model] ───► pgvector HNSW Search (Cosine Distance)  ──┐
    │                                                                      │ (Top-20)
    └───► [plainto_tsquery] ───► tsvector Sparse Search (GIN Index)       ──┴──► Reciprocal Rank Fusion (RRF)
                                                                                   │
                                                                                   ▼ (Top-15 Candidates)
                                                                          FlashRank Cross-Encoder
                                                                          (ms-marco-TinyBERT-L-2-v2)
                                                                                   │
                                                                                   ▼ (Top-K Re-scored)
                                                                          Grounded LLM Synthesis + Citations
```

### 1. Stage 1: Dual-CTE Hybrid Retrieval with RRF
Search queries run concurrently inside PostgreSQL via a single Common Table Expression (CTE):
* **Dense Semantic Search:** Uses `pgvector` to compute vector distances over embeddings.
* **Sparse Lexical Search:** Uses a generated `tsvector` column (`content_fts`) backed by a PostgreSQL GIN index with `ts_rank`.
* **Reciprocal Rank Fusion:** Fuses disparate score scales using rank-based weighting:
  $$RRF(d) = \sum_{m \in M} rac{1}{60 + r_m(d)}$$

### 2. Stage 2: In-Process Cross-Encoder Reranking
Top RRF candidate chunks pass into **FlashRank** (`ms-marco-TinyBERT-L-2-v2`), a lightweight ONNX-quantized cross-encoder running directly in-process on CPU:
* Computes token-level cross-attention across `(query, document_chunk)` pairs.
* Re-scores candidates into calibrated relevance confidences (e.g., `0.99+` precision) prior to LLM prompt injection.
* Operates locally with sub-10ms overhead, ensuring zero third-party data egress.
