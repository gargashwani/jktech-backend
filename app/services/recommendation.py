"""
Book Recommendation Service
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.logging import get_logger
from app.models.book import Book, Review
from app.schemas.book import BookResponse

logger = get_logger("recommendations")


class RecommendationService:
    """Service for generating book recommendations."""

    @staticmethod
    async def get_recommendations(
        db: AsyncSession,
        user_id: Optional[int] = None,
        genre: Optional[str] = None,
        limit: int = 10,
    ) -> tuple[List[Book], str]:
        """
        Get book recommendations based on user preferences.

        Args:
            db: Database session
            user_id: Optional user ID for personalized recommendations
            genre: Optional genre filter
            limit: Maximum number of recommendations

        Returns:
            Tuple of (list of books, reason string)
        """
        try:
            # Strategy 1: If user_id provided, recommend based on their review history
            if user_id:
                # Get user's reviewed books and their ratings
                user_reviews_query = select(Review).filter(Review.user_id == user_id)
                user_reviews_result = await db.execute(user_reviews_query)
                user_reviews = list(user_reviews_result.scalars().all())

                if user_reviews:
                    # Get genres of highly rated books
                    highly_rated_book_ids = [
                        r.book_id for r in user_reviews if r.rating >= 4
                    ]
                    if highly_rated_book_ids:
                        # Get books in similar genres
                        similar_books_query = (
                            select(Book)
                            .filter(Book.id.notin_(highly_rated_book_ids))
                            .limit(limit)
                        )
                        if genre:
                            similar_books_query = similar_books_query.filter(
                                Book.genre == genre
                            )
                        result = await db.execute(similar_books_query)
                        books = list(result.scalars().all())
                        if books:
                            return (
                                books,
                                f"Based on your highly rated books in similar genres",
                            )

            # Strategy 2: Recommend highly rated books
            # Get average ratings for all books
            avg_ratings_query = (
                select(
                    Review.book_id,
                    func.avg(Review.rating).label("avg_rating"),
                    func.count(Review.id).label("review_count"),
                )
                .group_by(Review.book_id)
                .having(func.count(Review.id) >= 3)  # At least 3 reviews
                .order_by(func.avg(Review.rating).desc())
                .limit(limit)
            )
            avg_ratings_result = await db.execute(avg_ratings_query)
            top_rated_book_ids = [
                row.book_id for row in avg_ratings_result.fetchall()
            ]

            if top_rated_book_ids:
                books_query = select(Book).filter(Book.id.in_(top_rated_book_ids))
                if genre:
                    books_query = books_query.filter(Book.genre == genre)
                result = await db.execute(books_query)
                books = list(result.scalars().all())
                if books:
                    return (
                        books,
                        "Highly rated books with at least 3 reviews",
                    )

            # Strategy 3: Fallback - recent books in genre or all recent books
            books_query = select(Book).order_by(Book.created_at.desc()).limit(limit)
            if genre:
                books_query = books_query.filter(Book.genre == genre)
            result = await db.execute(books_query)
            books = list(result.scalars().all())

            reason = f"Recent books" + (f" in {genre} genre" if genre else "")
            return books, reason

        except Exception as e:
            logger.exception(
                "Error generating recommendations",
                e,
                context={"user_id": user_id, "genre": genre, "limit": limit},
            )
            # Fallback to recent books
            books_query = select(Book).order_by(Book.created_at.desc()).limit(limit)
            if genre:
                books_query = books_query.filter(Book.genre == genre)
            result = await db.execute(books_query)
            books = list(result.scalars().all())
            return books, "Recent books (fallback)"


# Singleton instance
recommendation_service = RecommendationService()
