"""
Broadcasting WebSocket Endpoints
Handles WebSocket connections for real-time broadcasting.
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from redis import Redis

from app.core.security import get_current_user
from app.models.user import User
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Store active WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, dict[str, WebSocket]] = {}
        # Format: {channel: {socket_id: websocket}}
        self.user_connections: dict[int, dict[str, WebSocket]] = {}
        # Format: {user_id: {socket_id: websocket}}
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
                decode_responses=True,
            )
        return self.redis

    async def connect(
        self, websocket: WebSocket, socket_id: str, user_id: int | None = None
    ):
        """Accept WebSocket connection."""
        await websocket.accept()

        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = {}
            self.user_connections[user_id][socket_id] = websocket

        logger.info(f"WebSocket connected: {socket_id}")

    def disconnect(self, socket_id: str, user_id: int | None = None):
        """Remove WebSocket connection."""
        # Remove from channels
        for channel, connections in self.active_connections.items():
            connections.pop(socket_id, None)

        # Remove from user connections
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].pop(socket_id, None)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        logger.info(f"WebSocket disconnected: {socket_id}")

    async def subscribe(self, socket_id: str, channel: str):
        """Subscribe socket to channel."""
        if channel not in self.active_connections:
            self.active_connections[channel] = {}
        # Note: WebSocket will be added when connection is established
        logger.info(f"Socket {socket_id} subscribed to {channel}")

    async def unsubscribe(self, socket_id: str, channel: str):
        """Unsubscribe socket from channel."""
        if channel in self.active_connections:
            self.active_connections[channel].pop(socket_id, None)
        logger.info(f"Socket {socket_id} unsubscribed from {channel}")

    async def broadcast_to_channel(
        self,
        channel: str,
        event: str,
        data: dict[str, Any],
        exclude_socket: str | None = None,
    ):
        """Broadcast event to all connections in channel."""
        if channel not in self.active_connections:
            return

        message = {
            "event": event,
            "data": data,
            "channel": channel,
        }

        disconnected = []
        for socket_id, websocket in self.active_connections[channel].items():
            if exclude_socket and socket_id == exclude_socket:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {socket_id}: {e}")
                disconnected.append(socket_id)

        # Clean up disconnected sockets
        for socket_id in disconnected:
            self.disconnect(socket_id)

    async def listen_redis(self):
        """Listen to Redis pub/sub for broadcasts."""
        try:
            # Use synchronous Redis with threading for pub/sub
            # In production, consider using aioredis
            redis = self._get_redis()
            pubsub = redis.pubsub(ignore_subscribe_messages=True)
            pubsub.psubscribe("broadcast:*")

            # Process messages in a loop
            while True:
                try:
                    message = pubsub.get_message(timeout=1.0)
                    if message and message["type"] == "pmessage":
                        channel = message["channel"].replace("broadcast:", "")
                        try:
                            data = json.loads(message["data"])
                            event = data.get("event")
                            event_data = data.get("data", {})
                            exclude_socket = data.get("socket")

                            await self.broadcast_to_channel(
                                channel, event, event_data, exclude_socket
                            )
                        except json.JSONDecodeError:
                            logger.error(
                                f"Invalid JSON in broadcast message: {message['data']}"
                            )
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error listening to Redis: {e}")
        finally:
            if "pubsub" in locals():
                pubsub.close()


# Global connection manager
manager = ConnectionManager()
_redis_listener_started = False


async def start_redis_listener():
    """Start Redis listener (should be called once)."""
    global _redis_listener_started
    if not _redis_listener_started:
        _redis_listener_started = True
        asyncio.create_task(manager.listen_redis())


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = Query(None)):
    """
    WebSocket endpoint for broadcasting.
    Similar to Laravel's broadcasting endpoint.
    Requires authentication token.
    """
    import uuid

    socket_id = str(uuid.uuid4())
    user_id = None

    # Require authentication token
    if not token:
        await websocket.close(code=1008, reason="Authentication token required")
        return

    # Authenticate user
    try:
        from jose import jwt
        from jose.exceptions import JWTError

        from app.models.user import User
        from config import settings

        # Decode and validate JWT token
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")

        if user_id is None:
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Verify user exists
        # Note: We need to get a DB session - for WebSocket, we'll create a temporary one
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            user = User.get(db, id=int(user_id))
            if not user or not user.is_active:
                await websocket.close(code=1008, reason="User not found or inactive")
                return
            user_id = user.id
        finally:
            db.close()

    except (JWTError, ValueError, Exception) as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return

    await manager.connect(websocket, socket_id, user_id)

    try:
        # Start Redis listener if not already started
        await start_redis_listener()

        # Send connection confirmation
        await websocket.send_json(
            {"event": "connected", "data": {"socket_id": socket_id}}
        )

        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            event_type = data.get("event")

            if event_type == "subscribe":
                channel = data.get("channel")
                if channel:
                    await manager.subscribe(socket_id, channel)
                    # Add to active connections
                    if channel not in manager.active_connections:
                        manager.active_connections[channel] = {}
                    manager.active_connections[channel][socket_id] = websocket

                    await websocket.send_json(
                        {"event": "subscribed", "channel": channel}
                    )

            elif event_type == "unsubscribe":
                channel = data.get("channel")
                if channel:
                    await manager.unsubscribe(socket_id, channel)
                    await websocket.send_json(
                        {"event": "unsubscribed", "channel": channel}
                    )

            elif event_type == "ping":
                await websocket.send_json({"event": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(socket_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(socket_id, user_id)


@router.post("/auth")
async def authorize_channel(
    channel_name: str = Query(...),
    socket_id: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    """
    Authorize private/presence channel access.
    Similar to Laravel's broadcasting/auth endpoint.
    """
    from app.core.channels import get_channel_manager
    from routes.channels import register_channels

    # Register channels (should be done once, but safe to call multiple times)
    register_channels()

    channel_manager = get_channel_manager()

    # Check if channel is private or presence
    if not channel_name.startswith("private-") and not channel_name.startswith(
        "presence-"
    ):
        raise HTTPException(
            status_code=403, detail="Channel authorization not required"
        )

    # Authorize using channel manager
    if not channel_manager.authorize(current_user, channel_name):
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Generate auth signature (simplified - in production, use proper signing)
    import hashlib
    import hmac

    message = f"{socket_id}:{channel_name}"
    signature = hmac.new(
        settings.APP_KEY.encode(), message.encode(), hashlib.sha256
    ).hexdigest()

    if channel_name.startswith("private-"):
        # Private channel
        return {"auth": f"{settings.APP_KEY}:{signature}", "channel_data": None}

    elif channel_name.startswith("presence-"):
        # Presence channel - include user information
        channel_data = {
            "user_id": current_user.id,
            "user_info": {
                "id": current_user.id,
                "email": current_user.email,
                "name": current_user.full_name or current_user.email,
            },
        }

        return {
            "auth": f"{settings.APP_KEY}:{signature}",
            "channel_data": json.dumps(channel_data),
        }

    raise HTTPException(status_code=403, detail="Unauthorized")
