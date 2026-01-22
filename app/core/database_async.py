"""
Async Database Configuration
Supports async operations with asyncpg for PostgreSQL
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from config import settings


def get_async_database_url() -> str:
    """
    Construct async database URL for PostgreSQL with asyncpg.
    """
    connection = settings.DB_CONNECTION.lower()
    user = settings.DB_USERNAME
    password = settings.DB_PASSWORD

    # PostgreSQL async connection with asyncpg
    if connection in ["postgresql", "postgres"]:
        # Replace postgresql:// with postgresql+asyncpg://
        return (
            f"postgresql+asyncpg://{user}:{password}@"
            f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"
        )

    raise ValueError(
        f"Async database only supports PostgreSQL. Got: {connection}"
    )


# Construct async database URL
ASYNC_DATABASE_URL = get_async_database_url()

# Create async engine
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for async models
# Use the same metadata as Base to allow foreign keys between sync and async models
from app.core.database import Base
AsyncBase = Base


# Dependency to get async DB session
async def get_async_db():
    """
    Async database session dependency for FastAPI routes.
    Automatically handles session lifecycle.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
