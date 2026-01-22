"""
Base Event Classes for Broadcasting
Similar to Laravel's ShouldBroadcast interface.
"""

from abc import ABC, abstractmethod
from typing import Any


class ShouldBroadcast(ABC):
    """
    Interface for events that should be broadcast.
    Similar to Laravel's ShouldBroadcast.
    """

    @abstractmethod
    def broadcast_on(self) -> str | list[str]:
        """
        Get the channels the event should broadcast on.

        Returns:
            Channel name or list of channel names
        """
        pass

    @abstractmethod
    def broadcast_as(self) -> str:
        """
        Get the event name.

        Returns:
            Event name
        """
        pass

    def broadcast_with(self) -> dict[str, Any]:
        """
        Get the data to broadcast.

        Returns:
            Dictionary of data to broadcast
        """
        return {}

    def broadcast_queue(self) -> str | None:
        """
        Get the queue name for broadcasting.

        Returns:
            Queue name or None for default
        """
        return None

    def broadcast_connection(self) -> str | None:
        """
        Get the broadcasting connection to use.

        Returns:
            Connection name or None for default
        """
        return None


class ShouldBroadcastNow(ShouldBroadcast):
    """
    Interface for events that should be broadcast immediately.
    Similar to Laravel's ShouldBroadcastNow.
    """

    pass


class ShouldBroadcastToOthers(ShouldBroadcast):
    """
    Interface for events that should broadcast to others only.
    Similar to Laravel's ShouldBroadcastToOthers.
    """

    pass
