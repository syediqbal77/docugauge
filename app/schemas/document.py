import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class DocumentBase(BaseModel):
    filename: str
    file_size_bytes: int
    mime_type: str


class DocumentResponse(DocumentBase):
    id: uuid.UUID
    file_hash: str
    status: str
    total_pages: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    query: str
    document_id: Optional[uuid.UUID] = None
    top_k: int = 5


class Citation(BaseModel):
    chunk_id: str
    chunk_index: int
    page_number: Optional[int]
    score: float


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
