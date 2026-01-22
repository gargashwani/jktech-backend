from celery import Celery

from config import settings


def get_redis_url(db: int = 0) -> str:
    """
    Build Redis URL from settings.
    Supports password authentication.

    Args:
        db: Redis database number

    Returns:
        Redis connection URL
    """
    if settings.REDIS_PASSWORD:
        return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{db}"
    else:
        return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{db}"


# Use configured broker/backend or build from Redis settings
broker_url = settings.CELERY_BROKER_URL or get_redis_url(settings.REDIS_DB)
result_backend = settings.CELERY_RESULT_BACKEND or get_redis_url(settings.REDIS_DB)

celery_app = Celery(
    "worker", broker=broker_url, backend=result_backend, include=["app.jobs.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=1,
)
