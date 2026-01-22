"""
Cache Configuration
Similar to Laravel's config/cache.php
"""

import os

cache_config = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
    "password": os.getenv("REDIS_PASSWORD"),
    "prefix": os.getenv("CACHE_PREFIX", "cache:"),
    "default_ttl": int(os.getenv("CACHE_DEFAULT_TTL", "3600")),
    "serializer": os.getenv("CACHE_SERIALIZER", "json"),
}
