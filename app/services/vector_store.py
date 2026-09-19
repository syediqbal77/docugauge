from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import DocumentChunk
from app.services.embedding import embedding_service


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
                text = c.get("content", "")
                idx = c.get("chunk_index", i)
                page = c.get("page_number")
            else:
                text = getattr(c, "content", "")
                idx = getattr(c, "chunk_index", i)
                page = getattr(c, "page_number", None)

            contents.append(text)
            parsed_chunks.append({
                "chunk_index": idx,
                "content": text,
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

        distance_col = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")

        stmt = select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
            DocumentChunk.content,
            DocumentChunk.page_number,
            distance_col
        )

        if document_id:
            stmt = stmt.where(DocumentChunk.document_id == document_id)

        stmt = stmt.order_by(distance_col).limit(limit)

        result = await session.execute(stmt)
        rows = result.fetchall()

        retrieved = []
        for row in rows:
            dist = row.distance if row.distance is not None else 1.0
            retrieved.append({
                "chunk_id": str(row.id),
                "document_id": str(row.document_id),
                "chunk_index": row.chunk_index,
                "content": row.content,
                "page_number": row.page_number,
                "score": float(1.0 - dist)
            })

        return retrieved


vector_store_service = VectorStoreService()
