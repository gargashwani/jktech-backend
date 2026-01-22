"""
Web Routes
Define web routes here, similar to Laravel's routes/web.php
These are typically for web pages, not API endpoints.
"""

from fastapi import APIRouter


def register_web_routes() -> APIRouter:
    """
    Register all web routes.
    Similar to Laravel's routes/web.php
    Returns the web router with all routes included.
    """
    web_router = APIRouter()

    # Add web routes here
    # Example:
    # @web_router.get("/")
    # async def home():
    #     return {"message": "Welcome"}

    return web_router
