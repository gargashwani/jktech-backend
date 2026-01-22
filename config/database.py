"""
Database Configuration
Similar to Laravel's config/database.php
"""

import os

database_config = {
    "connection": os.getenv("DB_CONNECTION", "postgresql"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_DATABASE", "fastapi_boilerplate"),
    "username": os.getenv("DB_USERNAME", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "unix_socket": os.getenv("DB_UNIX_SOCKET"),
    "ssl_mode": os.getenv("DB_SSL_MODE"),
}
