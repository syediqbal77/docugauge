import httpx
from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.vector_store import vector_store_service


class RAGService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.model = settings.LLM_MODEL_NAME

    def _build_context_prompt(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        formatted_context = []
        for c in context_chunks:
            page_info = f"Page {c['page_number']}" if c.get("page_number") else "N/A"
            formatted_context.append(
                f"[Chunk {c['chunk_index']} | {page_info}]:\n{c['content']}"
            )

        context_str = "\n\n---\n\n".join(formatted_context)

        system_instruction = (
            "You are DocuGauge, an accurate document intelligence assistant. "
            "Answer the user's question using ONLY the provided context blocks. "
            "When stating facts, cite the source using the chunk format [Chunk X, Page Y]. "
            "If the answer cannot be found in the context, explicitly state that the documents "
            "do not contain sufficient information.\n\n"
            f"Context:\n{context_str}\n\n"
            f"User Question: {query}\n\n"
            "Answer:"
        )
        return system_instruction

    async def answer_query(
        self,
        session: AsyncSession,
        query: str,
        document_id: Optional[uuid.UUID] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Retrieve relevant chunks and generate a cited response."""
        chunks = await vector_store_service.similarity_search(
            session=session,
            query=query,
            limit=top_k,
            document_id=document_id
        )

        if not chunks:
            return {
                "answer": "No relevant context found in uploaded documents.",
                "citations": []
            }

        prompt = self._build_context_prompt(query, chunks)

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()

        citations = [
            {
                "chunk_id": c["chunk_id"],
                "chunk_index": c["chunk_index"],
                "page_number": c["page_number"],
                "score": round(c["score"], 4)
            }
            for c in chunks
        ]

        return {
            "answer": result.get("response", "").strip(),
            "citations": citations
        }


rag_service = RAGService()
