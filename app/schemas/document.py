"""
Document Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.document import IngestionStatus


class DocumentBase(BaseModel):
    filename: str
    file_path: str
    file_size: int
    mime_type: Optional[str] = None


class DocumentCreate(DocumentBase):
    uploaded_by: int


class DocumentResponse(DocumentBase):
    id: int
    content: Optional[str] = None
    ingestion_status: IngestionStatus
    ingestion_error: Optional[str] = None
    uploaded_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IngestionResponse(BaseModel):
    id: int
    document_id: int
    status: IngestionStatus
    progress: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QAResponse(BaseModel):
    question: str
    answer: str
    sources: list[dict] = Field(default_factory=list)  # Document excerpts with metadata
    confidence: Optional[float] = None


class QARequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_ids: Optional[list[int]] = None  # Filter by specific documents
