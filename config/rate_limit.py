"""
Rate Limit Configuration
"""

import os

rate_limit_config = {
    "limit": int(os.getenv("RATE_LIMIT", "100")),
    "window": int(os.getenv("RATE_LIMIT_WINDOW", "60")),
}
