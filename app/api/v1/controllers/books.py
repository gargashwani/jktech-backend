from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_async import get_async_db
from app.core.logging import get_logger
from app.core.security_async import get_current_active_user_async
from app.models.book import Book, Review
from app.models.user import User
from app.schemas.book import (
    BookCreate,
    BookUpdate,
    BookResponse,
    ReviewCreate,
    ReviewResponse,
    BookSummaryResponse,
    BookRecommendationRequest,
    BookRecommendationResponse,
)
from app.services.recommendation import recommendation_service

logger = get_logger("books")

router = APIRouter()


@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    *,
    db: AsyncSession = Depends(get_async_db),
    book_in: BookCreate,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    try:
        logger.info(f"Creating book: {book_in.title}")
        book = await Book.create(
            db,
            title=book_in.title,
            author=book_in.author,
            genre=book_in.genre,
            year_published=book_in.year_published,
            summary=book_in.summary,
        )

        # No external AI call here; summary stays as provided in the request
        return book
    except Exception as e:
        logger.exception(
            "Error creating book",
            e,
            context={"user_id": current_user.id, "book_data": book_in.model_dump()},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create book",
        )


@router.get("/books", response_model=List[BookResponse])
async def get_books(
    *,
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Get all books."""
    try:
        books = await Book.get_all(db, skip=skip, limit=limit)
        return books
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch books",
        )


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(
    *,
    db: AsyncSession = Depends(get_async_db),
    book_id: int,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Get a specific book by ID."""
    book = await Book.get(db, id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(
    *,
    db: AsyncSession = Depends(get_async_db),
    book_id: int,
    book_in: BookUpdate,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Update a book."""
    book = await Book.get(db, id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    update_data = book_in.model_dump(exclude_unset=True)
    book = await Book.update(db, book, **update_data)
    return book


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    *,
    db: AsyncSession = Depends(get_async_db),
    book_id: int,
    current_user: User = Depends(get_current_active_user_async),
):
    """Delete a book."""
    try:
        book = await Book.get(db, id=book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        await Book.delete(db, book)
        logger.info(f"Book {book_id} deleted by user {current_user.id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error deleting book",
            e,
            context={"book_id": book_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete book",
        )


@router.post("/books/{book_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    *,
    db: AsyncSession = Depends(get_async_db),
    book_id: int,
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Add a review for a book."""
    # Verify book exists
    book = await Book.get(db, id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Verify book_id matches
    if review_in.book_id != book_id:
        raise HTTPException(
            status_code=400, detail="Book ID in URL does not match review data"
        )

    review = await Review.create(
        db,
        book_id=book_id,
        user_id=current_user.id,
        review_text=review_in.review_text,
        rating=review_in.rating,
    )
    return review


@router.get("/books/{book_id}/reviews", response_model=List[ReviewResponse])
async def get_reviews(
    *,
    db: AsyncSession = Depends(get_async_db),
    book_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Get all reviews for a book."""
    # Verify book exists
    book = await Book.get(db, id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    reviews = await Review.get_by_book(db, book_id=book_id, skip=skip, limit=limit)
    return reviews


@router.get("/books/{book_id}/summary", response_model=BookSummaryResponse)
async def get_book_summary(
    *,
    db: AsyncSession = Depends(get_async_db),
    book_id: int,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Get a summary and aggregated rating for a book."""
    book = await Book.get(db, id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Get reviews
    reviews = await Review.get_by_book(db, book_id=book_id)
    average_rating = await Review.get_average_rating(db, book_id=book_id)

    # Simple local summary based only on ratings (no external AI)
    review_summary = None
    if reviews and average_rating is not None:
        review_summary = (
            f"Average rating: {average_rating:.1f}/5 "
            f"based on {len(reviews)} review(s)."
        )

    return BookSummaryResponse(
        book=book,
        average_rating=average_rating,
        total_reviews=len(reviews),
        summary=review_summary,
    )


@router.post("/generate-summary")
async def generate_summary(
    *,
    content: str,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Generate a very simple local summary for given book content (no external AI)."""
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="Content is required")

    text = content.strip()
    max_len = 200
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return {"summary": text}


@router.post("/recommendations", response_model=BookRecommendationResponse)
async def get_recommendations(
    *,
    db: AsyncSession = Depends(get_async_db),
    request: BookRecommendationRequest,
    current_user: User = Depends(get_current_active_user_async),
) -> Any:
    """Get book recommendations based on user preferences."""
    user_id = request.user_id or current_user.id
    books, reason = await recommendation_service.get_recommendations(
        db,
        user_id=user_id,
        genre=request.genre,
        limit=request.limit,
    )
    return BookRecommendationResponse(books=books, reason=reason)
