"""
JWT Configuration
"""

import os

jwt_config = {
    "secret": os.getenv("JWT_SECRET", "your-jwt-secret-key-here-change-in-production"),
    "algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
    "expiration": int(os.getenv("JWT_EXPIRATION", "3600")),
}
