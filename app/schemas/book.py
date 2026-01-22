"""
Book Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    author: str = Field(..., min_length=1, max_length=255, description="Book author")
    genre: str = Field(..., min_length=1, max_length=100, description="Book genre")
    year_published: int = Field(
        ...,
        ge=1000,
        le=2100,
        description="Year published (must be between 1000 and 2100)",
    )
    summary: Optional[str] = Field(None, max_length=5000, description="Book summary")
    
    @field_validator("year_published")
    @classmethod
    def validate_year_published(cls, v):
        """Validate year published is within reasonable range."""
        if v < 1000:
            raise ValueError("Year published must be 1000 or later")
        if v > 2100:
            raise ValueError("Year published must be 2100 or earlier")
        return v
    
    @field_validator("summary", mode="before")
    @classmethod
    def validate_summary(cls, v):
        """Convert empty string to None."""
        if v == "":
            return None
        return v


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    genre: Optional[str] = Field(None, min_length=1, max_length=100)
    year_published: Optional[int] = Field(None, ge=1000, le=2100)
    summary: Optional[str] = None


class BookResponse(BookBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewBase(BaseModel):
    review_text: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewCreate(ReviewBase):
    book_id: int


class ReviewResponse(ReviewBase):
    id: int
    book_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookSummaryResponse(BaseModel):
    book: BookResponse
    average_rating: Optional[float] = None
    total_reviews: int
    summary: Optional[str] = None  # AI-generated summary


class BookRecommendationRequest(BaseModel):
    user_id: Optional[int] = None
    genre: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)


class BookRecommendationResponse(BaseModel):
    books: list[BookResponse]
    reason: str  # Why these books were recommended
