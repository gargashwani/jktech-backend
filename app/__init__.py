import os
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from app.core.error_handler import global_exception_handler
from app.core.logging import get_logger
from app.http.middleware import LoggingMiddleware, RateLimitMiddleware
from config import settings
from routes.api import register_api_routes

# Import all models to ensure SQLAlchemy can resolve relationships
# This must happen before routes are registered
from app.models.user import User  # noqa: F401
from app.models.book import Book, Review  # noqa: F401
from app.models.document import Document, Ingestion  # noqa: F401

# Initialize logger
logger = get_logger("app")

app = FastAPI(
    title=settings.APP_NAME, openapi_url="/openapi.json", debug=settings.APP_DEBUG
)

# Log application startup
try:
    logger.info(
        f"Starting {settings.APP_NAME}",
        context={
            "env": settings.APP_ENV,
            "debug": settings.APP_DEBUG,
            "version": "1.0.0",
        },
    )
except Exception as e:
    print(f"Error logging startup: {e}")


# Add validation error handler to log 422 errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors (422) with detailed logging."""
    try:
        body = await request.body()
        body_str = body.decode('utf-8') if body else None
    except Exception:
        body_str = None
    
    # Get validation errors and ensure they're serializable
    errors = exc.errors()
    
    logger.error(
        f"Validation error on {request.method} {request.url.path}",
        context={
            "errors": errors,
            "body": body_str,
            "method": request.method,
            "url": str(request.url),
        },
    )
    
    # Build response content - ensure all values are JSON serializable
    response_content = {"detail": errors}
    
    # Only include body if it's serializable
    if hasattr(exc, 'body') and exc.body is not None:
        try:
            # Try to serialize the body to check if it's valid
            import json
            json.dumps(exc.body)
            response_content["body"] = exc.body
        except (TypeError, ValueError):
            # If body is not serializable, convert to string or skip
            try:
                response_content["body"] = str(exc.body)
            except Exception:
                pass  # Skip body if we can't convert it
    
    return JSONResponse(
        status_code=422,
        content=response_content,
    )

# Add global exception handler
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    return await global_exception_handler(request, exc)


# Set up CORS - never allow all origins in production
cors_origins = settings.BACKEND_CORS_ORIGINS
if settings.APP_ENV == "production" and "*" in cors_origins:
    # In production, don't allow wildcard
    cors_origins = [origin for origin in cors_origins if origin != "*"]
    if not cors_origins:
        raise ValueError(
            "CORS origins must be specified in production. Cannot use '*' wildcard."
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)


# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # HSTS - only in production with HTTPS
    if settings.APP_ENV == "production" and settings.APP_URL.startswith("https://"):
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

    # Content Security Policy
    # Allow Swagger UI CDN resources for /docs and /redoc endpoints
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        # More permissive CSP for API docs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self';"
        )
    else:
        # Strict CSP for other endpoints
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        )

    # Permissions Policy
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response


# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracking."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Add custom middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


@app.get("/")
async def root():
    return {
        "message": "Welcome to the FastAPI Boilerplate API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_docs": "/redoc",
    }


# Mount static files (public directory)
# Similar to Laravel's public directory
public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if os.path.exists(public_dir):
    app.mount("/public", StaticFiles(directory=public_dir), name="public")

# Mount storage files for public access
# Files in public/storage will be accessible via /storage/ URL
storage_public_dir = os.path.join(public_dir, "storage")
if os.path.exists(storage_public_dir):
    app.mount("/storage", StaticFiles(directory=storage_public_dir), name="storage")

# Include API routes (Laravel-like routes/api.php)
api_router = register_api_routes()
app.include_router(api_router, prefix="/api/v1")


# Initialize Prometheus instrumentation if enabled
if settings.ENABLE_METRICS:
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator().instrument(app).expose(app)
    except ImportError:
        import logging
        logging.getLogger(__name__).warning(
            "prometheus-fastapi-instrumentator not installed, metrics disabled."
        )
