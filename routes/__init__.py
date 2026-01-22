"""
Routes Package
Laravel-like routes structure for FastAPI Boilerplate
"""

from routes.api import register_api_routes
from routes.channels import register_channels
from routes.web import register_web_routes

__all__ = ["register_channels", "register_api_routes", "register_web_routes"]
