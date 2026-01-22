"""
User-related Broadcast Events
Example events for user actions.
"""

from typing import Any

from app.events.base import ShouldBroadcast
from app.models.user import User


class UserCreated(ShouldBroadcast):
    """Event broadcast when a user is created."""

    def __init__(self, user: User):
        self.user = user

    def broadcast_on(self) -> str:
        """Broadcast on public channel."""
        return "users"

    def broadcast_as(self) -> str:
        """Event name."""
        return "UserCreated"

    def broadcast_with(self) -> dict[str, Any]:
        """Event data."""
        return {
            "id": self.user.id,
            "email": self.user.email,
            "name": self.user.full_name,
            "created_at": str(self.user.created_at),
        }


class UserUpdated(ShouldBroadcast):
    """Event broadcast when a user is updated."""

    def __init__(self, user: User):
        self.user = user

    def broadcast_on(self) -> str:
        """Broadcast on private channel for the user."""
        return f"private-user.{self.user.id}"

    def broadcast_as(self) -> str:
        """Event name."""
        return "UserUpdated"

    def broadcast_with(self) -> dict[str, Any]:
        """Event data."""
        return {
            "id": self.user.id,
            "email": self.user.email,
            "name": self.user.full_name,
            "updated_at": str(self.user.updated_at),
        }


class UserDeleted(ShouldBroadcast):
    """Event broadcast when a user is deleted."""

    def __init__(self, user_id: int):
        self.user_id = user_id

    def broadcast_on(self) -> str:
        """Broadcast on presence channel."""
        return "presence-users"

    def broadcast_as(self) -> str:
        """Event name."""
        return "UserDeleted"

    def broadcast_with(self) -> dict[str, Any]:
        """Event data."""
        return {
            "user_id": self.user_id,
        }
