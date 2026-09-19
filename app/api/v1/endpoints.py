import uuid
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse, QueryRequest, QueryResponse
from app.services.chunker import chunker_service
from app.services.ingestion import ingestion_service
from app.services.rag import rag_service
from app.services.vector_store import vector_store_service

router = APIRouter()


@router.post("/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    file_hash = ingestion_service.calculate_sha256(contents)

    # Check for deduplication
    existing_doc_query = await db.execute(
        select(Document).where(Document.file_hash == file_hash)
    )
    existing_doc = existing_doc_query.scalars().first()
    if existing_doc:
        return existing_doc

    # Extract text and page count
    filename = file.filename or "unknown_file"
    try:
        _, total_pages = ingestion_service.extract_text(contents, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc = Document(
        filename=filename,
        file_hash=file_hash,
        file_size_bytes=len(contents),
        mime_type=file.content_type or "application/octet-stream",
        status="processing",
        total_pages=total_pages,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Chunk text
    ext = filename.lower().split(".")[-1]
    if ext == "pdf":
        chunks = chunker_service.chunk_pdf(contents)
    else:
        text, _ = ingestion_service.extract_text(contents, filename)
        chunks = chunker_service.chunk_plain_text(text)

    # Embed & persist chunks to pgvector
    if chunks:
        await vector_store_service.add_chunks(
            session=db,
            document_id=doc.id,
            raw_chunks=chunks,
        )

    doc.status = "ready"
    await db.commit()
    await db.refresh(doc)

    return doc


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return result.scalars().all()


@router.post("/rag/query", response_model=QueryResponse)
async def query_rag(
    payload: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await rag_service.answer_query(
        session=db,
        query=payload.query,
        document_id=payload.document_id,
        top_k=payload.top_k,
    )
    return result
