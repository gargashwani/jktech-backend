"""
Application Configuration
Similar to Laravel's config/app.php
"""

import os

app_config = {
    "name": os.getenv("APP_NAME", "FastAPI Boilerplate"),
    "env": os.getenv("APP_ENV", "local"),
    "debug": os.getenv("APP_DEBUG", "false").lower() == "true",
    "url": os.getenv("APP_URL", "http://localhost:8000"),
    "key": os.getenv("APP_KEY", "your-secret-key-here-change-in-production"),
    "timezone": os.getenv("APP_TIMEZONE", "UTC"),
}
