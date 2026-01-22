"""
Mail Configuration
Similar to Laravel's config/mail.php
"""

import os

mail_config = {
    "host": os.getenv("MAIL_HOST", "smtp.mailtrap.io"),
    "port": int(os.getenv("MAIL_PORT", "2525")),
    "username": os.getenv("MAIL_USERNAME"),
    "password": os.getenv("MAIL_PASSWORD"),
    "encryption": os.getenv("MAIL_ENCRYPTION", "tls"),
    "from_address": os.getenv("MAIL_FROM_ADDRESS", "hello@example.com"),
    "from_name": os.getenv("MAIL_FROM_NAME", "FastAPI Boilerplate"),
}
