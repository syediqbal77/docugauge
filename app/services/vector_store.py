from typing import List, Dict, Any, Optional
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.document import DocumentChunk
from app.services.embedding import embedding_service

logger = logging.getLogger(__name__)

try:
    from flashrank import Ranker, RerankRequest
    reranker = Ranker(model_name="ms-marco-TinyBERT-L-2-v2")
except Exception as e:
    logger.warning(f"FlashRank could not be initialized: {e}. Falling back to standard RRF ranking.")
    reranker = None


class VectorStoreService:
    async def add_chunks(
        self,
        session: AsyncSession,
        document_id: uuid.UUID,
        raw_chunks: Optional[List[Any]] = None,
        chunks: Optional[List[Any]] = None,
        **kwargs
    ) -> None:
        input_chunks = raw_chunks if raw_chunks is not None else (chunks or [])
        if not input_chunks:
            return

        contents = []
        parsed_chunks = []
        for i, c in enumerate(input_chunks):
            if isinstance(c, dict):
                text_val = c.get("content", "")
                idx = c.get("chunk_index", i)
                page = c.get("page_number")
            else:
                text_val = getattr(c, "content", "")
                idx = getattr(c, "chunk_index", i)
                page = getattr(c, "page_number", None)

            contents.append(text_val)
            parsed_chunks.append({
                "chunk_index": idx,
                "content": text_val,
                "page_number": page
            })

        embeddings = await embedding_service.get_embeddings_batch(contents)

        db_chunks = []
        for i, c in enumerate(parsed_chunks):
            db_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=c["chunk_index"],
                content=c["content"],
                page_number=c["page_number"],
                embedding=embeddings[i]
            )
            db_chunks.append(db_chunk)

        session.add_all(db_chunks)
        await session.commit()

    async def similarity_search(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 5,
        document_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        query_embedding = await embedding_service.get_embedding(query)
        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        doc_filter_semantic = "WHERE document_id = :document_id" if document_id else ""
        doc_filter_keyword = "AND document_id = :document_id" if document_id else ""

        rrf_sql = text(f"""
            WITH semantic_search AS (
                SELECT id, document_id, chunk_index, content, page_number,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> cast(:query_embedding as vector)) AS rank
                FROM document_chunks
                {doc_filter_semantic}
                LIMIT 20
            ),
            keyword_search AS (
                SELECT id, document_id, chunk_index, content, page_number,
                       ROW_NUMBER() OVER (
                           ORDER BY ts_rank(content_fts, plainto_tsquery('english', :query_text)) DESC
                       ) AS rank
                FROM document_chunks
                WHERE content_fts @@ plainto_tsquery('english', :query_text)
                {doc_filter_keyword}
                LIMIT 20
            )
            SELECT 
                COALESCE(s.id, k.id) AS id,
                COALESCE(s.document_id, k.document_id) AS document_id,
                COALESCE(s.chunk_index, k.chunk_index) AS chunk_index,
                COALESCE(s.content, k.content) AS content,
                COALESCE(s.page_number, k.page_number) AS page_number,
                (COALESCE(1.0 / (60 + s.rank), 0.0) + COALESCE(1.0 / (60 + k.rank), 0.0)) AS rrf_score
            FROM semantic_search s
            FULL OUTER JOIN keyword_search k ON s.id = k.id
            ORDER BY rrf_score DESC
            LIMIT 15;
        """)

        params: Dict[str, Any] = {
            "query_embedding": embedding_str,
            "query_text": query,
        }
        if document_id:
            params["document_id"] = document_id

        result = await session.execute(rrf_sql, params)
        rows = result.fetchall()

        retrieved = []
        for row in rows:
            retrieved.append({
                "chunk_id": str(row.id),
                "document_id": str(row.document_id),
                "chunk_index": row.chunk_index,
                "content": row.content,
                "page_number": row.page_number,
                "score": float(row.rrf_score)
            })

        if not retrieved:
            return []

        if reranker is not None and len(retrieved) > 1:
            try:
                passages = [{"id": r["chunk_id"], "text": r["content"], "meta": r} for r in retrieved]
                rerank_req = RerankRequest(query=query, passages=passages)
                reranked_results = reranker.rerank(rerank_req)
                
                final_results = []
                for res in reranked_results[:limit]:
                    item = res["meta"]
                    item["score"] = float(res.get("score", item["score"]))
                    final_results.append(item)
                return final_results
            except Exception as e:
                logger.warning(f"Reranking encountered an error: {e}. Using RRF ranking.")

        return retrieved[:limit]


vector_store_service = VectorStoreService()
