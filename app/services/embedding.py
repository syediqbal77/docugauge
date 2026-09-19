import httpx
from typing import List
from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.model_name = settings.EMBEDDING_MODEL_NAME

    async def get_embedding(self, text: str) -> List[float]:
        """Generate an embedding vector for a single string."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model_name,
                    "input": text
                }
            )
            response.raise_for_status()
            data = response.json()
            # Ollama /api/embed returns {"embeddings": [[...]]}
            return data["embeddings"][0]

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batch for a list of texts."""
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model_name,
                    "input": texts
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["embeddings"]


embedding_service = EmbeddingService()
