import os
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_async import get_async_db
from app.core.logging import get_logger
from app.core.security_async import (
    get_current_active_user_async,
    get_current_admin_user_async,
)
from app.models.document import Document, Ingestion, IngestionStatus
from app.models.user import User
from app.schemas.document import DocumentResponse, IngestionResponse
from app.services.rag import rag_service
from config import settings

logger = get_logger("documents")

router = APIRouter()


def get_storage_path(filename: str) -> str:
    storage_dir = os.path.join(settings.FILESYSTEM_ROOT, "documents")
    os.makedirs(storage_dir, exist_ok=True)
    return os.path.join(storage_dir, filename)


async def extract_text_from_file(file_path: str, mime_type: str) -> str:
    if mime_type.startswith("text/"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif mime_type == "application/pdf":
        logger.warning("PDF not supported yet", context={"file_path": file_path})
        return "PDF extraction not implemented. Please use text files."
    else:
        logger.warning(f"Unsupported file type: {mime_type}")
        return f"Content extraction not supported for {mime_type}"


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    *,
    db: AsyncSession = Depends(get_async_db),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    if not file.filename.lower().endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")
    
    file_path = get_storage_path(file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    text_content = await extract_text_from_file(file_path, file.content_type or "")
    document = await Document.create(
        db,
        filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        content=text_content,
        ingestion_status=IngestionStatus.PENDING,
        uploaded_by=current_user.id,
    )

    return document


@router.get("", response_model=List[DocumentResponse])
async def get_documents(
    *,
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
    status: IngestionStatus = None,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    documents = await Document.get_all(db, skip=skip, limit=limit, status=status)
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    *,
    db: AsyncSession = Depends(get_async_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    document = await Document.get(db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    *,
    db: AsyncSession = Depends(get_async_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user_async),
):
    document = await Document.get(db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.uploaded_by != current_user.id and not current_user.is_superuser:
        logger.warning(
            f"Unauthorized delete attempt for document {document_id}",
            context={"user_id": current_user.id, "document_owner": document.uploaded_by},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document",
        )

    rag_service.delete_document(document_id)
    logger.debug(f"Document {document_id} deleted from vector store")

    if os.path.exists(document.file_path):
        os.remove(document.file_path)
        logger.debug(f"File deleted: {document.file_path}")

    await Document.delete(db, document)
    logger.info(f"Document {document_id} deleted by user {current_user.id}")


@router.post("/{document_id}/ingest", response_model=IngestionResponse, status_code=status.HTTP_201_CREATED)
async def trigger_ingestion(
    *,
    db: AsyncSession = Depends(get_async_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    document = await Document.get(db, id=document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    existing = await Ingestion.get_by_document(db, document_id)
    if existing and existing.status == IngestionStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Already processing")

    from datetime import datetime
    ingestion = await Ingestion.create(
        db,
        document_id=document_id,
        status=IngestionStatus.PROCESSING,
        progress=0,
        started_at=datetime.utcnow(),
    )

    await Document.update(db, document, ingestion_status=IngestionStatus.PROCESSING)

    if not document.content:
        raise ValueError("No content to ingest")

    logger.info(f"Starting ingestion: {document.filename}")
    rag_service.add_document(
        document_id=document_id,
        content=document.content,
        metadata={"filename": document.filename, "uploaded_by": str(document.uploaded_by)},
    )

    ingestion = await Ingestion.update(
        db, ingestion, status=IngestionStatus.COMPLETED, progress=100, completed_at=datetime.utcnow()
    )
    await Document.update(db, document, ingestion_status=IngestionStatus.COMPLETED)
    logger.info(f"Ingestion done: {document_id}")

    return ingestion


@router.get("/ingestions", response_model=List[IngestionResponse])
async def get_ingestions(
    *,
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
    status: IngestionStatus = None,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    ingestions = await Ingestion.get_all(db, skip=skip, limit=limit, status=status)
    return ingestions


@router.get("/ingestions/{ingestion_id}", response_model=IngestionResponse)
async def get_ingestion(
    *,
    db: AsyncSession = Depends(get_async_db),
    ingestion_id: int,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    ingestion = await Ingestion.get(db, id=ingestion_id)
    if not ingestion:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    return ingestion
