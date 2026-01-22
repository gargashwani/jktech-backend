"""
Unit tests for Document API
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, IngestionStatus


@pytest.mark.asyncio
async def test_upload_document(client: AsyncClient, auth_headers: dict):
    """Test uploading a document."""
    # Create a test file
    files = {
        "file": ("test.txt", b"Test document content", "text/plain")
    }
    response = await client.post(
        "/api/v1/documents",
        files=files,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["ingestion_status"] == IngestionStatus.PENDING.value


@pytest.mark.asyncio
async def test_get_documents(client: AsyncClient, auth_headers: dict):
    """Test getting all documents."""
    response = await client.get("/api/v1/documents", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_document_by_id(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """Test getting a document by ID."""
    from app.models.user import User
    from sqlalchemy import select
    
    # Get or create a test user
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    document = await Document.create(
        db,
        filename="test.txt",
        file_path="/tmp/test.txt",
        file_size=100,
        mime_type="text/plain",
        ingestion_status=IngestionStatus.PENDING,
        uploaded_by=user.id,
    )
    
    response = await client.get(
        f"/api/v1/documents/{document.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document.id
