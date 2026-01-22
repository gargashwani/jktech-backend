import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.database import Base
from config import settings

# Import all models so Alembic can detect them
from app.models.user import User  # noqa
from app.models.book import Book, Review  # noqa
from app.models.document import Document, Ingestion  # noqa

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    """
    Construct database URL for migrations.
    Supports PostgreSQL and MySQL similar to Laravel's database configuration.
    """
    connection = settings.DB_CONNECTION.lower()

    # PostgreSQL connection strings
    if connection in ["postgresql", "postgres"]:
        return f"postgresql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"

    # MySQL connection strings
    elif connection in ["mysql", "mysql+pymysql"]:
        return f"mysql+pymysql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"

    # SQLite (if needed in future)
    elif connection == "sqlite":
        return f"sqlite:///{settings.DB_DATABASE}"

    # Default: use the connection string as-is
    else:
        return f"{settings.DB_CONNECTION}://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"


def get_connect_args():
    """
    Get connection arguments for migrations based on database type.
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


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=get_connect_args(),
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
