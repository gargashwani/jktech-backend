"""
Scheduler Configuration
"""

import os

scheduler_config = {
    "timezone": os.getenv("APP_TIMEZONE", "UTC"),
}
