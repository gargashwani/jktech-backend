"""
CORS Configuration
"""

import json
import os

cors_origins_str = os.getenv(
    "BACKEND_CORS_ORIGINS", '["http://localhost:3000","http://localhost:8000"]'
)
try:
    cors_origins = json.loads(cors_origins_str)
except (json.JSONDecodeError, TypeError):
    cors_origins = ["http://localhost:3000", "http://localhost:8000"]

cors_config = {
    "origins": cors_origins,
}
