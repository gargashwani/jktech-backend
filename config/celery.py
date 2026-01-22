"""
Celery Configuration
"""

import os

celery_config = {
    "broker_url": os.getenv("CELERY_BROKER_URL"),
    "result_backend": os.getenv("CELERY_RESULT_BACKEND"),
    "worker_concurrency": int(os.getenv("CELERY_WORKER_CONCURRENCY", "4")),
    "task_time_limit": int(os.getenv("CELERY_TASK_TIME_LIMIT", "1800")),
    "task_soft_time_limit": int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "1200")),
}
