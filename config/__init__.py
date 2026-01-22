"""
Configuration Package
Laravel-like configuration structure for FastAPI Boilerplate
"""

import json
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import root_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main settings class - combines all configuration"""

    # Database Configuration
    DB_CONNECTION: str = os.getenv("DB_CONNECTION", "postgresql")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_DATABASE: str = os.getenv("DB_DATABASE", "fastapi_boilerplate")
    DB_USERNAME: str = os.getenv("DB_USERNAME", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_UNIX_SOCKET: str | None = os.getenv("DB_UNIX_SOCKET")
    DB_SSL_MODE: str | None = os.getenv("DB_SSL_MODE")

    # Application Configuration
    APP_NAME: str = os.getenv("APP_NAME", "FastAPI Boilerplate")
    APP_ENV: str = os.getenv("APP_ENV", "local")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")
    APP_KEY: str = os.getenv("APP_KEY", "your-secret-key-here-change-in-production")
    APP_TIMEZONE: str = os.getenv("APP_TIMEZONE", "UTC")
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"

    # JWT Configuration
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", "your-jwt-secret-key-here-change-in-production"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION: int = int(os.getenv("JWT_EXPIRATION", "3600"))

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD")

    # Cache Configuration
    CACHE_PREFIX: str = os.getenv("CACHE_PREFIX", "cache:")
    CACHE_DEFAULT_TTL: int = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))
    CACHE_SERIALIZER: str = os.getenv("CACHE_SERIALIZER", "json")

    # Rate Limiting Configuration
    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # CORS Configuration
    BACKEND_CORS_ORIGINS: list[str] = json.loads(
        os.getenv(
            "BACKEND_CORS_ORIGINS", '["http://localhost:3000","http://localhost:8000"]'
        )
    )

    # Email Configuration
    MAIL_HOST: str = os.getenv("MAIL_HOST", "smtp.mailtrap.io")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "2525"))
    MAIL_USERNAME: str | None = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: str | None = os.getenv("MAIL_PASSWORD")
    MAIL_ENCRYPTION: str = os.getenv("MAIL_ENCRYPTION", "tls")
    MAIL_FROM_ADDRESS: str = os.getenv("MAIL_FROM_ADDRESS", "hello@example.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "FastAPI Boilerplate")

    # Celery Configuration
    CELERY_BROKER_URL: str | None = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str | None = os.getenv("CELERY_RESULT_BACKEND")
    CELERY_WORKER_CONCURRENCY: int = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))
    CELERY_TASK_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_TIME_LIMIT", "1800"))
    CELERY_TASK_SOFT_TIME_LIMIT: int = int(
        os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "1200")
    )

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    LOG_MAX_SIZE: int = int(os.getenv("LOG_MAX_SIZE", "10485760"))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Broadcasting Configuration
    BROADCAST_DRIVER: str = os.getenv("BROADCAST_DRIVER", "redis")
    BROADCAST_CONNECTION: str = os.getenv("BROADCAST_CONNECTION", "default")
    PUSHER_APP_ID: str | None = os.getenv("PUSHER_APP_ID")
    PUSHER_APP_KEY: str | None = os.getenv("PUSHER_APP_KEY")
    PUSHER_APP_SECRET: str | None = os.getenv("PUSHER_APP_SECRET")
    PUSHER_APP_CLUSTER: str = os.getenv("PUSHER_APP_CLUSTER", "mt1")
    PUSHER_HOST: str | None = os.getenv("PUSHER_HOST")
    PUSHER_PORT: int = int(os.getenv("PUSHER_PORT", "443"))
    PUSHER_SCHEME: str = os.getenv("PUSHER_SCHEME", "https")
    PUSHER_ENCRYPTED: bool = os.getenv("PUSHER_ENCRYPTED", "true").lower() == "true"
    ABLY_KEY: str | None = os.getenv("ABLY_KEY")

    # Filesystem Configuration
    FILESYSTEM_DISK: str = os.getenv("FILESYSTEM_DISK", "local")
    FILESYSTEM_ROOT: str = os.getenv("FILESYSTEM_ROOT", "storage/app")
    FILESYSTEM_PUBLIC_ROOT: str = os.getenv("FILESYSTEM_PUBLIC_ROOT", "public/storage")
    FILESYSTEM_URL: str | None = os.getenv("FILESYSTEM_URL")
    AWS_ACCESS_KEY_ID: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    AWS_BUCKET: str | None = os.getenv("AWS_BUCKET")
    AWS_ENDPOINT: str | None = os.getenv("AWS_ENDPOINT")
    FTP_HOST: str = os.getenv("FTP_HOST", "localhost")
    FTP_PORT: int = int(os.getenv("FTP_PORT", "21"))
    FTP_USERNAME: str | None = os.getenv("FTP_USERNAME")
    FTP_PASSWORD: str | None = os.getenv("FTP_PASSWORD")
    SFTP_HOST: str = os.getenv("SFTP_HOST", "localhost")
    SFTP_PORT: int = int(os.getenv("SFTP_PORT", "22"))
    SFTP_USERNAME: str | None = os.getenv("SFTP_USERNAME")
    SFTP_PASSWORD: str | None = os.getenv("SFTP_PASSWORD")
    SFTP_KEY: str | None = os.getenv("SFTP_KEY")

    # OpenRouter (Llama3) Configuration
    OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    OPENROUTER_MODEL: str = os.getenv(
        "OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct:free"
    )

    # RAG Configuration
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    @root_validator(skip_on_failure=True)
    def validate_secrets(cls, values):
        """Validate that secrets are set and not using defaults in production."""
        insecure_defaults = [
            "your-secret-key-here",
            "your-jwt-secret-key-here",
            "your-secret-key-here-change-in-production",
            "your-jwt-secret-key-here-change-in-production",
        ]

        # Only validate in production
        if values.get("APP_ENV") == "production":
            app_key = values.get("APP_KEY", "")
            jwt_secret = values.get("JWT_SECRET", "")

            if app_key in insecure_defaults:
                raise ValueError(
                    "APP_KEY must be set to a secure random value in production. "
                    'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
                )
            if jwt_secret in insecure_defaults:
                raise ValueError(
                    "JWT_SECRET must be set to a secure random value in production. "
                    'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
                )

            if len(app_key) < 32:
                raise ValueError(
                    "APP_KEY must be at least 32 characters long for security"
                )
            if len(jwt_secret) < 32:
                raise ValueError(
                    "JWT_SECRET must be at least 32 characters long for security"
                )

        return values

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
