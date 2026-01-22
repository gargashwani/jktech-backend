"""
Broadcasting System
Laravel-like broadcasting using WebSockets and Redis pub/sub.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.events.base import ShouldBroadcast
from config import settings

logger = logging.getLogger(__name__)


class BroadcastManager:
    """
    Broadcasting manager similar to Laravel's Broadcast facade.
    Supports multiple drivers: redis, pusher, ably, log, null
    """

    def __init__(self):
        self._driver = None
        self._connections: dict[str, Any] = {}

    def driver(self, driver: str | None = None) -> "BroadcastDriver":
        """
        Get broadcasting driver instance.

        Args:
            driver: Driver name (defaults to BROADCAST_DRIVER from config)

        Returns:
            BroadcastDriver instance
        """
        driver = driver or settings.BROADCAST_DRIVER

        if driver not in self._connections:
            self._connections[driver] = self._create_driver(driver)

        return self._connections[driver]

    def _create_driver(self, driver: str) -> "BroadcastDriver":
        """Create broadcasting driver instance."""
        if driver == "redis":
            return RedisBroadcastDriver()
        elif driver == "pusher":
            return PusherBroadcastDriver()
        elif driver == "ably":
            return AblyBroadcastDriver()
        elif driver == "log":
            return LogBroadcastDriver()
        elif driver == "null":
            return NullBroadcastDriver()
        else:
            raise ValueError(f"Unsupported broadcast driver: {driver}")

    def channel(self, channel: str) -> "BroadcastChannel":
        """
        Create a channel instance.

        Args:
            channel: Channel name

        Returns:
            BroadcastChannel instance
        """
        return BroadcastChannel(channel, self.driver())

    def private(self, channel: str) -> "BroadcastChannel":
        """
        Create a private channel instance.

        Args:
            channel: Private channel name (will be prefixed with 'private-')

        Returns:
            BroadcastChannel instance
        """
        return BroadcastChannel(f"private-{channel}", self.driver())

    def presence(self, channel: str) -> "BroadcastChannel":
        """
        Create a presence channel instance.

        Args:
            channel: Presence channel name (will be prefixed with 'presence-')

        Returns:
            BroadcastChannel instance
        """
        return BroadcastChannel(f"presence-{channel}", self.driver())

    def event(self, event: ShouldBroadcast) -> bool:
        """
        Broadcast an event.

        Args:
            event: Event instance implementing ShouldBroadcast

        Returns:
            True if successful
        """
        try:
            driver = self.driver(event.broadcast_connection())
            channels = event.broadcast_on()

            # Handle single channel or list of channels
            if isinstance(channels, str):
                channels = [channels]
            elif not isinstance(channels, list):
                channels = [str(channels)]

            event_name = event.broadcast_as()
            data = event.broadcast_with()

            # Broadcast to all channels
            for channel in channels:
                driver.broadcast(channel, event_name, data)

            return True
        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")
            return False

    def to_others(self) -> "BroadcastManager":
        """
        Broadcast to others only (exclude current user).
        Similar to Laravel's broadcast()->toOthers().
        """
        # This would be used in conjunction with events
        # Implementation would track socket_id to exclude
        return self

    def queue(self, queue: str | None = None):
        """
        Set the queue for broadcasting.

        Args:
            queue: Queue name
        """
        # Implementation would set queue for async broadcasting
        pass


class BroadcastDriver(ABC):
    """Base class for broadcast drivers."""

    @abstractmethod
    def broadcast(self, channel: str, event: str, data: dict[str, Any]) -> bool:
        """Broadcast event to channel."""
        pass


class RedisBroadcastDriver(BroadcastDriver):
    """Redis pub/sub broadcast driver."""

    def __init__(self):
        self.redis: Redis | None = None
        self.pubsub = None

    def _get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self.redis is None:
            self.redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,
            )
        return self.redis

    def broadcast(self, channel: str, event: str, data: dict[str, Any]) -> bool:
        """Broadcast event to Redis channel."""
        try:
            redis = self._get_redis()

            # Format message similar to Laravel's broadcasting format
            message = {
                "event": event,
                "data": data,
                "socket": None,  # For "to others" functionality
            }

            # Publish to Redis channel
            redis.publish(f"broadcast:{channel}", json.dumps(message))

            return True
        except RedisError as e:
            logger.error(f"Redis broadcast error: {e}")
            return False


class PusherBroadcastDriver(BroadcastDriver):
    """Pusher Channels broadcast driver."""

    def __init__(self):
        self.pusher = None

    def _get_pusher(self):
        """Get or create Pusher client."""
        if self.pusher is None:
            try:
                import pusher

                self.pusher = pusher.Pusher(
                    app_id=settings.PUSHER_APP_ID,
                    key=settings.PUSHER_APP_KEY,
                    secret=settings.PUSHER_APP_SECRET,
                    cluster=settings.PUSHER_APP_CLUSTER,
                    host=settings.PUSHER_HOST,
                    port=settings.PUSHER_PORT,
                    ssl=settings.PUSHER_ENCRYPTED,
                )
            except ImportError:
                raise ImportError(
                    "pusher library is required. Install with: pip install pusher"
                )
        return self.pusher

    def broadcast(self, channel: str, event: str, data: dict[str, Any]) -> bool:
        """Broadcast event via Pusher."""
        try:
            pusher = self._get_pusher()
            pusher.trigger(channel, event, data)
            return True
        except Exception as e:
            logger.error(f"Pusher broadcast error: {e}")
            return False


class AblyBroadcastDriver(BroadcastDriver):
    """Ably broadcast driver."""

    def __init__(self):
        self.ably = None

    def _get_ably(self):
        """Get or create Ably client."""
        if self.ably is None:
            try:
                from ably import AblyRest

                self.ably = AblyRest(settings.ABLY_KEY)
            except ImportError:
                raise ImportError(
                    "ably library is required. Install with: pip install ably"
                )
        return self.ably

    def broadcast(self, channel: str, event: str, data: dict[str, Any]) -> bool:
        """Broadcast event via Ably."""
        try:
            ably = self._get_ably()
            channel_obj = ably.channels.get(channel)
            channel_obj.publish(event, data)
            return True
        except Exception as e:
            logger.error(f"Ably broadcast error: {e}")
            return False


class LogBroadcastDriver(BroadcastDriver):
    """Log broadcast driver (for testing/development)."""

    def broadcast(self, channel: str, event: str, data: dict[str, Any]) -> bool:
        """Log broadcast event."""
        logger.info(f"Broadcasting to {channel}: {event} - {data}")
        return True


class NullBroadcastDriver(BroadcastDriver):
    """Null broadcast driver (no-op)."""

    def broadcast(self, channel: str, event: str, data: dict[str, Any]) -> bool:
        """Do nothing."""
        return True


class BroadcastChannel:
    """Channel instance for broadcasting."""

    def __init__(self, channel: str, driver: BroadcastDriver):
        self.channel = channel
        self.driver = driver

    def broadcast(self, event: str, data: dict[str, Any]) -> bool:
        """
        Broadcast event to this channel.

        Args:
            event: Event name
            data: Event data

        Returns:
            True if successful
        """
        return self.driver.broadcast(self.channel, event, data)

    def to_others(self) -> "BroadcastChannel":
        """
        Broadcast to others only.
        Similar to Laravel's toOthers().
        """
        # Implementation would exclude current socket
        return self


# Global broadcast manager instance
_broadcast_manager: BroadcastManager | None = None


def get_broadcast_manager() -> BroadcastManager:
    """Get global broadcast manager instance."""
    global _broadcast_manager
    if _broadcast_manager is None:
        _broadcast_manager = BroadcastManager()
    return _broadcast_manager


def broadcast() -> BroadcastManager:
    """
    Get broadcast manager - Laravel-like API.

    Usage:
        broadcast().channel('orders').broadcast('OrderShipped', data)
        broadcast().event(OrderShippedEvent(order))
    """
    return get_broadcast_manager()
