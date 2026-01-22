"""Logging Middleware"""

import json
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger("http")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log request details (don't log sensitive information)
        # Remove query parameters that might contain sensitive data
        url = str(request.url)
        if "?" in url:
            base_url = url.split("?")[0]
            # Only log base URL, not query params
            url = base_url

        log_data = {
            "method": request.method,
            "url": url,  # Sanitized URL
            "status_code": response.status_code,
            "process_time": process_time,
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        # Use proper logging instead of print
        try:
            logger.info(
                f"{request.method} {url} - {response.status_code}",
                context=log_data,
            )
        except Exception as e:
            # Fallback if logging fails
            print(f"Logging middleware error: {e}")

        return response
