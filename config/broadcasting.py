"""
Broadcasting Configuration
Similar to Laravel's config/broadcasting.php
"""

import os

broadcasting_config = {
    "driver": os.getenv("BROADCAST_DRIVER", "redis"),
    "connection": os.getenv("BROADCAST_CONNECTION", "default"),
    "pusher_app_id": os.getenv("PUSHER_APP_ID"),
    "pusher_app_key": os.getenv("PUSHER_APP_KEY"),
    "pusher_app_secret": os.getenv("PUSHER_APP_SECRET"),
    "pusher_app_cluster": os.getenv("PUSHER_APP_CLUSTER", "mt1"),
    "pusher_host": os.getenv("PUSHER_HOST"),
    "pusher_port": int(os.getenv("PUSHER_PORT", "443")),
    "pusher_scheme": os.getenv("PUSHER_SCHEME", "https"),
    "pusher_encrypted": os.getenv("PUSHER_ENCRYPTED", "true").lower() == "true",
    "ably_key": os.getenv("ABLY_KEY"),
}
