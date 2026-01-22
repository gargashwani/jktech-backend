from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings


def get_database_url() -> str:
    """
    Construct database URL based on connection type.
    Supports PostgreSQL and MySQL similar to Laravel's database configuration.
    """
    connection = settings.DB_CONNECTION.lower()
    user = quote_plus(settings.DB_USERNAME)
    password = quote_plus(settings.DB_PASSWORD)

    # PostgreSQL connection strings
    if connection in ["postgresql", "postgres"]:
        return f"postgresql://{user}:{password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"

    # MySQL connection strings
    elif connection in ["mysql", "mysql+pymysql"]:
        return f"mysql+pymysql://{user}:{password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"

    # SQLite (if needed in future)
    elif connection == "sqlite":
        return f"sqlite:///{settings.DB_DATABASE}"

    # Default: use the connection string as-is
    else:
        return f"{settings.DB_CONNECTION}://{user}:{password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"


def get_connect_args() -> dict:
    """
    Get connection arguments based on database type.
    Similar to Laravel's database configuration options.
    """
    connection = settings.DB_CONNECTION.lower()
    connect_args = {}

    # MySQL-specific: Unix socket (for MAMP or local MySQL)
    if connection in ["mysql", "mysql+pymysql"]:
        if hasattr(settings, "DB_UNIX_SOCKET") and settings.DB_UNIX_SOCKET:
            connect_args["unix_socket"] = settings.DB_UNIX_SOCKET

    # PostgreSQL-specific: SSL mode
    if connection in ["postgresql", "postgres"]:
        if hasattr(settings, "DB_SSL_MODE") and settings.DB_SSL_MODE:
            connect_args["sslmode"] = settings.DB_SSL_MODE

    return connect_args


# Construct database URL
SQLALCHEMY_DATABASE_URL = get_database_url()

# Create engine with connection pool settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Maximum overflow connections
    connect_args=get_connect_args(),
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


# Dependency to get DB session (used by FastAPI dependency injection)
def get_db():
    """
    Database session dependency for FastAPI routes.
    Automatically handles session lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
