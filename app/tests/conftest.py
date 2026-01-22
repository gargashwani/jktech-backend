"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database_async import AsyncBase, get_async_db
from app.models.user import User
from app.core.security import get_password_hash
from app import app


# Create test database engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db():
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(AsyncBase.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(AsyncBase.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db: AsyncSession):
    """Create a test client."""
    async def override_get_db():
        yield db
    
    app.dependency_overrides[get_async_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db: AsyncSession):
    """Create a test user."""
    from sqlalchemy import select
    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == "test@example.com"))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        return existing_user
    
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture(scope="function")
async def auth_headers(client: AsyncClient, test_user: User):
    """Get authentication headers."""
    # Login to get token
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
