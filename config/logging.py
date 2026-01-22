"""
Logging Configuration
"""

import os

logging_config = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "file": os.getenv("LOG_FILE", "logs/app.log"),
    "max_size": int(os.getenv("LOG_MAX_SIZE", "10485760")),
    "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5")),
}
