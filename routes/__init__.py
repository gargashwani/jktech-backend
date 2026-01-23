from routes.api import register_api_routes
from routes.web import register_web_routes
from routes.channels import register_channels

__all__ = ["register_api_routes", "register_web_routes", "register_channels"]
