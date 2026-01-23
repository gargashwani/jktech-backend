from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
import enum

from app.core.database_async import AsyncBase


class IngestionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(AsyncBase):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False, index=True)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String, nullable=True)
    content = Column(Text, nullable=True)  # Extracted text content
    ingestion_status = Column(
        SQLEnum(IngestionStatus),
        default=IngestionStatus.PENDING,
        nullable=False,
        index=True,
    )
    ingestion_error = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )

    @classmethod
    async def get(cls, db: AsyncSession, id: int) -> Optional["Document"]:
        from sqlalchemy import select
        result = await db.execute(select(cls).filter(cls.id == id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_all(
        cls, db: AsyncSession, skip: int = 0, limit: int = 100, status: Optional[IngestionStatus] = None
    ) -> list["Document"]:
        from sqlalchemy import select
        query = select(cls)
        if status:
            query = query.filter(cls.ingestion_status == status)
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> "Document":
        db_obj = cls(**kwargs)
        db.add(db_obj)
        await db.flush()  # Flush to get the ID without committing
        await db.refresh(db_obj)
        return db_obj

    @classmethod
    async def update(cls, db: AsyncSession, db_obj: "Document", **kwargs) -> "Document":
        """Update a document."""
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        db_obj.updated_at = datetime.utcnow()
        await db.flush()  # Flush instead of commit (commit handled by dependency)
        await db.refresh(db_obj)
        return db_obj

    @classmethod
    async def delete(cls, db: AsyncSession, db_obj: "Document") -> None:
        """Delete a document."""
        await db.delete(db_obj)
        await db.flush()  # Flush instead of commit (commit handled by dependency)


class Ingestion(AsyncBase):
    __tablename__ = "ingestions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    status = Column(
        SQLEnum(IngestionStatus),
        default=IngestionStatus.PENDING,
        nullable=False,
        index=True,
    )
    progress = Column(Integer, default=0)  # Progress percentage 0-100
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )

    @classmethod
    async def get(cls, db: AsyncSession, id: int) -> Optional["Ingestion"]:
        """Get an ingestion by ID."""
        from sqlalchemy import select
        result = await db.execute(select(cls).filter(cls.id == id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_document(
        cls, db: AsyncSession, document_id: int
    ) -> Optional["Ingestion"]:
        """Get the latest ingestion for a document."""
        from sqlalchemy import select
        result = await db.execute(
            select(cls)
            .filter(cls.document_id == document_id)
            .order_by(cls.created_at.desc())
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_all(
        cls,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[IngestionStatus] = None,
    ) -> list["Ingestion"]:
        """Get all ingestions with optional status filter."""
        from sqlalchemy import select
        query = select(cls)
        if status:
            query = query.filter(cls.status == status)
        result = await db.execute(query.offset(skip).limit(limit).order_by(cls.created_at.desc()))
        return list(result.scalars().all())

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> "Ingestion":
        """Create a new ingestion."""
        db_obj = cls(**kwargs)
        db.add(db_obj)
        await db.flush()  # Flush to get the ID without committing
        await db.refresh(db_obj)
        return db_obj

    @classmethod
    async def update(cls, db: AsyncSession, db_obj: "Ingestion", **kwargs) -> "Ingestion":
        """Update an ingestion."""
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        db_obj.updated_at = datetime.utcnow()
        await db.flush()  # Flush instead of commit (commit handled by dependency)
        await db.refresh(db_obj)
        return db_obj
