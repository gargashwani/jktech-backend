"""
Channel Authorization
Similar to Laravel's routes/channels.php
"""

from collections.abc import Callable

from app.models.user import User


class Channel:
    """
    Channel authorization manager.
    Similar to Laravel's Broadcast::channel().
    """

    def __init__(self):
        self.channels: Dict[str, Callable] = {}

    def channel(self, name: str, callback: Callable[[User, str], bool]):
        """
        Register channel authorization callback.

        Args:
            name: Channel name pattern (e.g., 'private-user.{id}')
            callback: Authorization callback (user, channel_params) -> bool
        """
        self.channels[name] = callback

    def authorize(self, user: User, channel_name: str) -> bool:
        """
        Authorize user access to channel.

        Args:
            user: User instance
            channel_name: Channel name

        Returns:
            True if authorized
        """
        # Check if channel matches any registered pattern
        for pattern, callback in self.channels.items():
            if self._matches_pattern(pattern, channel_name):
                # Extract parameters from channel name
                params = self._extract_params(pattern, channel_name)
                return callback(user, **params)

        # Default: deny access to private/presence channels
        if channel_name.startswith("private-") or channel_name.startswith("presence-"):
            return False

        # Public channels are accessible to all
        return True

    def _matches_pattern(self, pattern: str, channel_name: str) -> bool:
        """Check if channel name matches pattern."""
        # Simple pattern matching (e.g., 'private-user.{id}' matches 'private-user.123')
        import re

        regex_pattern = pattern.replace("{id}", r"(\d+)").replace(".", r"\.")
        return bool(re.match(regex_pattern, channel_name))

    def _extract_params(self, pattern: str, channel_name: str) -> dict:
        """Extract parameters from channel name based on pattern."""
        import re

        regex_pattern = pattern.replace("{id}", r"(\d+)").replace(".", r"\.")
        match = re.match(regex_pattern, channel_name)
        if match:
            return {"id": int(match.group(1))}
        return {}


# Global channel manager
_channel_manager: Channel | None = None


def get_channel_manager() -> Channel:
    """Get global channel manager."""
    global _channel_manager
    if _channel_manager is None:
        _channel_manager = Channel()
    return _channel_manager


def channel() -> Channel:
    """Get channel manager - Laravel-like API."""
    return get_channel_manager()
