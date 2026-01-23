from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_async import AsyncBase

# Import User for relationship resolution
try:
    from app.models.user import User  # noqa: F401
except ImportError:
    pass


class Book(AsyncBase):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=False, index=True)
    genre = Column(String, nullable=False, index=True)
    year_published = Column(Integer, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )

    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

    @classmethod
    async def get(cls, db: AsyncSession, id: int) -> Optional["Book"]:
        """Get a book by ID."""
        from sqlalchemy import select
        result = await db.execute(select(cls).filter(cls.id == id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_all(
        cls, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list["Book"]:
        """Get all books with pagination."""
        from sqlalchemy import select
        result = await db.execute(select(cls).offset(skip).limit(limit))
        return list(result.scalars().all())

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> "Book":
        """Create a new book."""
        db_obj = cls(**kwargs)
        db.add(db_obj)
        await db.flush()  # Flush to get the ID without committing
        await db.refresh(db_obj)
        return db_obj

    @classmethod
    async def update(cls, db: AsyncSession, db_obj: "Book", **kwargs) -> "Book":
        """Update a book."""
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        db_obj.updated_at = datetime.utcnow()
        await db.flush()  # Flush instead of commit (commit handled by dependency)
        await db.refresh(db_obj)
        return db_obj

    @classmethod
    async def delete(cls, db: AsyncSession, db_obj: "Book") -> None:
        """Delete a book."""
        await db.delete(db_obj)
        await db.flush()  # Flush instead of commit (commit handled by dependency)


class Review(AsyncBase):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    review_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # Rating from 1 to 5
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )

    # Relationships
    book = relationship("Book", back_populates="reviews")
    # User relationship - using string reference to avoid circular import
    # User model will be imported when needed via alembic/env.py

    @classmethod
    async def get(cls, db: AsyncSession, id: int) -> Optional["Review"]:
        """Get a review by ID."""
        from sqlalchemy import select
        result = await db.execute(select(cls).filter(cls.id == id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_book(
        cls, db: AsyncSession, book_id: int, skip: int = 0, limit: int = 100
    ) -> list["Review"]:
        """Get all reviews for a book."""
        from sqlalchemy import select
        result = await db.execute(
            select(cls).filter(cls.book_id == book_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> "Review":
        """Create a new review."""
        db_obj = cls(**kwargs)
        db.add(db_obj)
        await db.flush()  # Flush to get the ID without committing
        await db.refresh(db_obj)
        return db_obj

    @classmethod
    async def get_average_rating(
        cls, db: AsyncSession, book_id: int
    ) -> Optional[float]:
        """Get average rating for a book."""
        from sqlalchemy import select, func
        result = await db.execute(
            select(func.avg(cls.rating)).filter(cls.book_id == book_id)
        )
        return result.scalar()
