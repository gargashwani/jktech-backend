"""Rate Limit Middleware"""

import json
import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    NOTE: This uses in-memory storage and won't work across multiple servers.
    For production, use Redis-based rate limiting.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit = settings.RATE_LIMIT
        self.rate_limit_window = settings.RATE_LIMIT_WINDOW
        self.requests = {}

        # Try to use Redis for distributed rate limiting if available
        try:
            from redis import Redis

            self.redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            # Test connection
            self.redis.ping()
            self.use_redis = True
        except Exception:
            self.redis = None
            self.use_redis = False
            if settings.APP_ENV == "production":
                logger.warning(
                    "Rate limiting using in-memory storage. For production, configure Redis."
                )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Use Redis if available for distributed rate limiting
        if self.use_redis and self.redis:
            try:
                key = f"rate_limit:{client_ip}"
                count = self.redis.incr(key)
                if count == 1:
                    self.redis.expire(key, self.rate_limit_window)

                if count > self.rate_limit:
                    return Response(
                        content=json.dumps({"detail": "Too many requests"}),
                        status_code=429,
                        media_type="application/json",
                    )
            except Exception:
                # Fallback to in-memory if Redis fails
                pass

        # In-memory rate limiting (fallback or if Redis not available)
        self.requests = {
            ip: [t for t in times if current_time - t < self.rate_limit_window]
            for ip, times in self.requests.items()
        }

        # Check rate limit
        if client_ip in self.requests:
            if len(self.requests[client_ip]) >= self.rate_limit:
                return Response(
                    content=json.dumps({"detail": "Too many requests"}),
                    status_code=429,
                    media_type="application/json",
                )
            self.requests[client_ip].append(current_time)
        else:
            self.requests[client_ip] = [current_time]

        return await call_next(request)
