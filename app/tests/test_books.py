"""
Unit tests for Book API
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.models.user import User


@pytest.mark.asyncio
async def test_create_book(client: AsyncClient, auth_headers: dict):
    """Test creating a book."""
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "genre": "Fiction",
        "year_published": 2024,
        "summary": "A test book summary",
    }
    response = await client.post(
        "/api/v1/books",
        json=book_data,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == book_data["title"]
    assert data["author"] == book_data["author"]


@pytest.mark.asyncio
async def test_get_books(client: AsyncClient, auth_headers: dict):
    """Test getting all books."""
    response = await client.get("/api/v1/books", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_book_by_id(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """Test getting a book by ID."""
    # Create a book first
    book = await Book.create(
        db,
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024,
    )
    
    response = await client.get(
        f"/api/v1/books/{book.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book.id
    assert data["title"] == "Test Book"


@pytest.mark.asyncio
async def test_update_book(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """Test updating a book."""
    book = await Book.create(
        db,
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024,
    )
    
    update_data = {"title": "Updated Book Title"}
    response = await client.put(
        f"/api/v1/books/{book.id}",
        json=update_data,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Book Title"


@pytest.mark.asyncio
async def test_delete_book(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """Test deleting a book."""
    book = await Book.create(
        db,
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024,
    )
    
    response = await client.delete(
        f"/api/v1/books/{book.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_review(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """Test creating a review."""
    book = await Book.create(
        db,
        title="Test Book",
        author="Test Author",
        genre="Fiction",
        year_published=2024,
    )
    
    review_data = {
        "book_id": book.id,
        "review_text": "Great book!",
        "rating": 5,
    }
    response = await client.post(
        f"/api/v1/books/{book.id}/reviews",
        json=review_data,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["review_text"] == "Great book!"
    assert data["rating"] == 5
