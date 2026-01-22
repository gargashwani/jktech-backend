"""
Document Management API Controller
"""

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
    """Get storage path for uploaded file."""
    storage_dir = os.path.join(settings.FILESYSTEM_ROOT, "documents")
    os.makedirs(storage_dir, exist_ok=True)
    return os.path.join(storage_dir, filename)


async def extract_text_from_file(file_path: str, mime_type: str) -> str:
    """Extract text content from file."""
    try:
        if mime_type.startswith("text/"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                logger.debug(
                    f"Extracted text from file",
                    context={"file_path": file_path, "content_length": len(content)},
                )
                return content
        elif mime_type == "application/pdf":
            # For PDF, you'd use PyPDF2 or similar
            # For now, return placeholder
            logger.warning(
                "PDF extraction not implemented, using placeholder",
                context={"file_path": file_path},
            )
            return "PDF content extraction not implemented. Please use text files."
        else:
            logger.warning(
                f"Unsupported file type: {mime_type}",
                context={"file_path": file_path, "mime_type": mime_type},
            )
            return f"Content extraction not supported for {mime_type}"
    except Exception as e:
        logger.exception(
            "Error extracting text from file",
            e,
            context={"file_path": file_path, "mime_type": mime_type},
        )
        return ""


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    *,
    db: AsyncSession = Depends(get_async_db),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Upload a document. Only .txt files are allowed."""
    try:
        # Validate file extension - only .txt files allowed
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )
        
        filename_lower = file.filename.lower()
        if not filename_lower.endswith('.txt'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .txt files are allowed. Please upload a text file.",
            )
        
        # Validate MIME type (optional check, but helpful)
        if file.content_type and file.content_type not in ['text/plain', 'text/plain; charset=utf-8']:
            logger.warning(
                f"Unexpected MIME type for .txt file: {file.content_type}",
                context={"filename": file.filename},
            )
            # Don't reject based on MIME type alone, as it can be unreliable
        
        # Save file
        file_path = get_storage_path(file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Extract text content
        text_content = await extract_text_from_file(file_path, file.content_type or "")

        # Create document record
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
    except Exception as e:
        logger.exception(
            "Error uploading document",
            e,
            context={
                "user_id": current_user.id,
                "filename": file.filename,
                "file_size": len(content) if 'content' in locals() else 0,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.get("", response_model=List[DocumentResponse])
async def get_documents(
    *,
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
    status: IngestionStatus = None,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Get all documents."""
    try:
        documents = await Document.get_all(db, skip=skip, limit=limit, status=status)
        return documents
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch documents",
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    *,
    db: AsyncSession = Depends(get_async_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Get a specific document by ID."""
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
    """Delete a document."""
    try:
        document = await Document.get(db, id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check ownership or admin
        if document.uploaded_by != current_user.id and not current_user.is_superuser:
            logger.warning(
                f"Unauthorized delete attempt for document {document_id}",
                context={"user_id": current_user.id, "document_owner": document.uploaded_by},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this document",
            )

        # Delete from vector store
        try:
            rag_service.delete_document(document_id)
            logger.debug(f"Document {document_id} deleted from vector store")
        except Exception as e:
            logger.warning(
                f"Error deleting document from vector store",
                context={"document_id": document_id, "error": str(e)},
            )

        # Delete file
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
                logger.debug(f"File deleted: {document.file_path}")
        except Exception as e:
            logger.warning(
                f"Error deleting file",
                context={"file_path": document.file_path, "error": str(e)},
            )

        await Document.delete(db, document)
        logger.info(f"Document {document_id} deleted by user {current_user.id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error deleting document",
            e,
            context={"document_id": document_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )


@router.post("/{document_id}/ingest", response_model=IngestionResponse, status_code=status.HTTP_201_CREATED)
async def trigger_ingestion(
    *,
    db: AsyncSession = Depends(get_async_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Trigger ingestion for a document."""
    document = await Document.get(db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if already processing
    existing_ingestion = await Ingestion.get_by_document(db, document_id)
    if existing_ingestion and existing_ingestion.status == IngestionStatus.PROCESSING:
        raise HTTPException(
            status_code=400, detail="Document is already being processed"
        )

    # Create ingestion record
    from datetime import datetime
    ingestion = await Ingestion.create(
        db,
        document_id=document_id,
        status=IngestionStatus.PROCESSING,
        progress=0,
        started_at=datetime.utcnow(),
    )

    # Update document status
    await Document.update(
        db, document, ingestion_status=IngestionStatus.PROCESSING
    )

    # Process ingestion asynchronously (in production, use Celery)
    try:
        if document.content:
            logger.info(
                f"Starting ingestion for document {document_id}",
                context={"filename": document.filename, "content_length": len(document.content)},
            )
            # Add to vector store
            rag_service.add_document(
                document_id=document_id,
                content=document.content,
                metadata={
                    "filename": document.filename,
                    "uploaded_by": str(document.uploaded_by),
                },
            )

            # Update ingestion status
            ingestion = await Ingestion.update(
                db,
                ingestion,
                status=IngestionStatus.COMPLETED,
                progress=100,
                completed_at=datetime.utcnow(),
            )

            await Document.update(
                db, document, ingestion_status=IngestionStatus.COMPLETED
            )
            logger.info(f"Ingestion completed for document {document_id}")
        else:
            raise ValueError("Document has no content to ingest")
    except Exception as e:
        logger.exception(
            "Error during ingestion",
            e,
            context={"document_id": document_id, "filename": document.filename},
        )
        ingestion = await Ingestion.update(
            db,
            ingestion,
            status=IngestionStatus.FAILED,
            error_message=str(e),
        )
        await Document.update(
            db, document, ingestion_status=IngestionStatus.FAILED, ingestion_error=str(e)
        )

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
    """Get all ingestions."""
    try:
        ingestions = await Ingestion.get_all(db, skip=skip, limit=limit, status=status)
        return ingestions
    except Exception as e:
        logger.error(f"Error fetching ingestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch ingestions",
        )


@router.get("/ingestions/{ingestion_id}", response_model=IngestionResponse)
async def get_ingestion(
    *,
    db: AsyncSession = Depends(get_async_db),
    ingestion_id: int,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Get a specific ingestion by ID."""
    ingestion = await Ingestion.get(db, id=ingestion_id)
    if not ingestion:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    return ingestion
