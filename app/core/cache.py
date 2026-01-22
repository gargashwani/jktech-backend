"""
Redis Cache Utility
Provides Laravel-like caching interface using Redis.
"""

import json
import logging
import pickle
from collections.abc import Callable
from typing import Any

from redis import ConnectionPool, Redis
from redis.exceptions import RedisError

from config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis Cache implementation similar to Laravel's Cache facade.
    Supports both simple key-value storage and serialized objects.
    """

    def __init__(self):
        """Initialize Redis connection pool."""
        self._pool: ConnectionPool | None = None
        self._redis: Redis | None = None
        self._prefix: str = getattr(settings, "CACHE_PREFIX", "cache:")
        self._default_ttl: int = getattr(settings, "CACHE_DEFAULT_TTL", 3600)
        self._serializer: str = getattr(
            settings, "CACHE_SERIALIZER", "json"
        )  # json or pickle

    @property
    def redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,  # We'll handle encoding/decoding ourselves
                max_connections=50,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            self._redis = Redis(connection_pool=self._pool)
        return self._redis

    def _make_key(self, key: str) -> str:
        """Add prefix to cache key."""
        return f"{self._prefix}{key}"

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if self._serializer == "pickle":
            # WARNING: Pickle is unsafe and should only be used in trusted environments
            # In production, prefer JSON serialization
            if settings.APP_ENV == "production":
                logger.warning(
                    "Using pickle serialization in production is not recommended for security reasons"
                )
            return pickle.dumps(value)
        else:  # json
            try:
                return json.dumps(value).encode("utf-8")
            except (TypeError, ValueError) as e:
                # Don't fallback to pickle - raise error instead for security
                logger.error(
                    f"JSON serialization failed: {e}. Value type: {type(value)}"
                )
                raise ValueError(
                    f"Cannot serialize value of type {type(value)} to JSON. Use pickle serializer explicitly if needed."
                )

    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from storage."""
        if value is None:
            return None

        # Only try JSON - no pickle fallback for security
        try:
            return json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            # If JSON fails and serializer is pickle, try pickle
            if self._serializer == "pickle":
                try:
                    return pickle.loads(value)
                except Exception as pickle_error:
                    logger.error(f"Failed to deserialize cache value: {pickle_error}")
                    return None
            else:
                logger.error(f"Failed to deserialize cache value (JSON only): {e}")
                return None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key doesn't exist

        Returns:
            Cached value or default
        """
        try:
            full_key = self._make_key(key)
            value = self.redis.get(full_key)
            if value is None:
                return default
            return self._deserialize(value)
        except RedisError as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return default

    def put(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        try:
            full_key = self._make_key(key)
            serialized = self._serialize(value)
            ttl = ttl if ttl is not None else self._default_ttl

            if ttl > 0:
                self.redis.setex(full_key, ttl, serialized)
            else:
                self.redis.set(full_key, serialized)

            return True
        except RedisError as e:
            logger.error(f"Redis put error for key {key}: {e}")
            return False

    def remember(self, key: str, ttl: int | None, callback: Callable[[], Any]) -> Any:
        """
        Get value from cache or execute callback and store result.
        Similar to Laravel's Cache::remember().

        Args:
            key: Cache key
            ttl: Time to live in seconds
            callback: Function to call if cache miss

        Returns:
            Cached value or callback result
        """
        value = self.get(key)
        if value is not None:
            return value

        # Cache miss - execute callback
        result = callback()
        self.put(key, result, ttl)
        return result

    def forget(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        try:
            full_key = self._make_key(key)
            return bool(self.redis.delete(full_key))
        except RedisError as e:
            logger.error(f"Redis forget error for key {key}: {e}")
            return False

    def flush(self, pattern: str | None = None) -> bool:
        """
        Clear all cache or cache matching pattern.

        Args:
            pattern: Optional pattern to match (e.g., 'user:*')

        Returns:
            True if successful
        """
        try:
            if pattern:
                full_pattern = self._make_key(pattern)
                keys = self.redis.keys(full_pattern)
                if keys:
                    self.redis.delete(*keys)
            else:
                # Clear all keys with prefix
                pattern = self._make_key("*")
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
            return True
        except RedisError as e:
            logger.error(f"Redis flush error: {e}")
            return False

    def has(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        try:
            full_key = self._make_key(key)
            return bool(self.redis.exists(full_key))
        except RedisError as e:
            logger.error(f"Redis has error for key {key}: {e}")
            return False

    def increment(self, key: str, amount: int = 1) -> int | None:
        """
        Increment numeric value in cache.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value or None if error
        """
        try:
            full_key = self._make_key(key)
            return self.redis.incrby(full_key, amount)
        except RedisError as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return None

    def decrement(self, key: str, amount: int = 1) -> int | None:
        """
        Decrement numeric value in cache.

        Args:
            key: Cache key
            amount: Amount to decrement by

        Returns:
            New value or None if error
        """
        try:
            full_key = self._make_key(key)
            return self.redis.decrby(full_key, amount)
        except RedisError as e:
            logger.error(f"Redis decrement error for key {key}: {e}")
            return None

    def pull(self, key: str, default: Any = None) -> Any:
        """
        Get and delete value from cache.
        Similar to Laravel's Cache::pull().

        Args:
            key: Cache key
            default: Default value if key doesn't exist

        Returns:
            Cached value or default
        """
        value = self.get(key, default)
        if value is not None:
            self.forget(key)
        return value

    def add(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Add value to cache only if key doesn't exist.
        Similar to Laravel's Cache::add().

        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds

        Returns:
            True if key was added, False if it already exists
        """
        try:
            full_key = self._make_key(key)
            if self.redis.exists(full_key):
                return False

            return self.put(key, value, ttl)
        except RedisError as e:
            logger.error(f"Redis add error for key {key}: {e}")
            return False

    def forever(self, key: str, value: Any) -> bool:
        """
        Store value in cache forever (no expiration).

        Args:
            key: Cache key
            value: Value to store

        Returns:
            True if successful
        """
        return self.put(key, value, ttl=0)

    def tags(self, *tags: str):
        """
        Begin tagging a cache operation.
        Note: This is a simplified implementation.
        For full tag support, you'd need to maintain tag-key relationships.

        Args:
            *tags: Tag names

        Returns:
            TaggedCache instance (simplified)
        """
        # Simplified tag implementation
        # In production, you'd want to maintain tag-key relationships
        return TaggedCache(self, tags)


# Global cache instance
_cache_instance: RedisCache | None = None


def get_cache() -> RedisCache:
    """Get global cache instance (singleton)."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


# Convenience functions (Laravel-like API)
def cache() -> RedisCache:
    """Get cache instance - Laravel-like API."""
    return get_cache()


class TaggedCache:
    """Simplified tagged cache implementation."""

    def __init__(self, cache: RedisCache, tags: tuple):
        self.cache = cache
        self.tags = tags
        self._tag_prefix = "tag:"

    def _make_key(self, key: str) -> str:
        """Make tagged key."""
        tag_str = ":".join(self.tags)
        return f"{tag_str}:{key}"

    def get(self, key: str, default: Any = None) -> Any:
        return self.cache.get(self._make_key(key), default)

    def put(self, key: str, value: Any, ttl: int | None = None) -> bool:
        return self.cache.put(self._make_key(key), value, ttl)

    def forget(self, key: str) -> bool:
        return self.cache.forget(self._make_key(key))

    def flush(self) -> bool:
        """Flush all keys with these tags."""
        pattern = ":".join(self.tags) + ":*"
        return self.cache.flush(pattern)
