# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_redis_pubsub"
# purpose: "Distributed Redis Pub/Sub event bus for cross-node WebSocket collaboration broadcasting"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List, Set, Coroutine
from apps.api.services.redis_client import redis_client

logger = logging.getLogger("dnk.workspace.pubsub")


class RedisPubSubManager:
    """
    Manages Redis Pub/Sub subscriptions for cross-node WebSocket broadcasting.
    Includes in-memory local fallback bus.
    """

    def __init__(self):
        self.pubsub: Optional[Any] = None
        self._handlers: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {}
        self._subscribed_channels: Set[str] = set()
        self._listen_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._local_bus: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {}

    async def init(self) -> None:
        """Initializes Redis Pub/Sub listener."""
        if not redis_client.is_connected:
            await redis_client.init()

        client = redis_client.get_client()
        # Only attach remote pubsub if a live remote server (standalone or cluster) is active
        if (redis_client.is_cluster or (redis_client.standalone and redis_client._connected)) and hasattr(client, "pubsub"):
            try:
                self.pubsub = client.pubsub()
                self._running = True
                logger.info("Redis PubSub manager initialized with remote Redis backend")
                return
            except Exception as e:
                logger.warning("Failed to initialize remote Redis PubSub (%s), using local fallback", e)

        self.pubsub = None
        self._running = True
        logger.info("Redis PubSub manager running in local fallback mode")

    async def subscribe(
        self,
        channel: str,
        handler: Callable[[Dict[str, Any]], Any]
    ) -> None:
        """Subscribes a coroutine or callback handler to a specific pub/sub channel."""
        if channel not in self._handlers:
            self._handlers[channel] = []
        if handler not in self._handlers[channel]:
            self._handlers[channel].append(handler)

        if channel not in self._local_bus:
            self._local_bus[channel] = []
        if handler not in self._local_bus[channel]:
            self._local_bus[channel].append(handler)

        if self.pubsub and channel not in self._subscribed_channels:
            try:
                await self.pubsub.subscribe(channel)
                self._subscribed_channels.add(channel)
                logger.debug("Subscribed to Redis PubSub channel: %s", channel)
                if not self._listen_task or self._listen_task.done():
                    self._listen_task = asyncio.create_task(self._listen_loop())
            except Exception as e:
                logger.warning("Redis subscribe error on %s: %s", channel, e)

    async def unsubscribe(
        self,
        channel: str,
        handler: Optional[Callable[[Dict[str, Any]], Any]] = None
    ) -> None:
        """Unsubscribes handler or entire channel."""
        if handler and channel in self._handlers:
            self._handlers[channel] = [h for h in self._handlers[channel] if h != handler]
            if channel in self._local_bus:
                self._local_bus[channel] = [h for h in self._local_bus[channel] if h != handler]

        if not handler or (channel in self._handlers and not self._handlers[channel]):
            self._handlers.pop(channel, None)
            self._local_bus.pop(channel, None)
            if self.pubsub and channel in self._subscribed_channels:
                try:
                    await self.pubsub.unsubscribe(channel)
                    self._subscribed_channels.discard(channel)
                except Exception as e:
                    logger.warning("Redis unsubscribe error on %s: %s", channel, e)

    async def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """Publishes a message to a channel across all cluster nodes and local handlers."""
        payload_str = json.dumps(message)

        # 1. Dispatch to remote Redis PubSub if connected
        client = redis_client.get_client()
        published_remote = False
        if self.pubsub and hasattr(client, "publish"):
            try:
                await client.publish(channel, payload_str)
                published_remote = True
            except Exception as e:
                logger.debug("Remote publish failed (%s), falling back to local bus", e)

        # 2. Local fallback dispatch if remote not available or local mode
        if not published_remote or not self.pubsub:
            handlers = list(self._local_bus.get(channel, []))
            for handler in handlers:
                try:
                    res = handler(message)
                    if asyncio.iscoroutine(res):
                        asyncio.create_task(res)
                except Exception as e:
                    logger.error("Error executing local handler for %s: %s", channel, e)

    async def _listen_loop(self) -> None:
        """Continuous background listener for incoming PubSub events."""
        try:
            if not self.pubsub:
                return
            async for msg in self.pubsub.listen():
                if not self._running:
                    break
                if msg and msg.get("type") == "message":
                    channel = msg.get("channel")
                    if isinstance(channel, (bytes, bytearray)):
                        channel = channel.decode("utf-8")

                    raw_data = msg.get("data")
                    if isinstance(raw_data, (bytes, bytearray)):
                        raw_data = raw_data.decode("utf-8")
                    if isinstance(raw_data, str):
                        try:
                            parsed_data = json.loads(raw_data)
                        except json.JSONDecodeError:
                            parsed_data = {"raw": raw_data}
                    else:
                        parsed_data = raw_data

                    handlers = list(self._handlers.get(channel, []))
                    for handler in handlers:
                        try:
                            res = handler(parsed_data)
                            if asyncio.iscoroutine(res):
                                asyncio.create_task(res)
                        except Exception as h_err:
                            logger.error("Error in subscriber handler for channel %s: %s", channel, h_err)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("PubSub listening loop exception: %s", e)

    async def close(self) -> None:
        """Stops listener and cleans up resources."""
        self._running = False
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None

        if self.pubsub:
            try:
                await self.pubsub.aclose()
            except AttributeError:
                try:
                    await self.pubsub.close()
                except Exception:
                    pass
            except Exception:
                pass
            self.pubsub = None

        self._handlers.clear()
        self._local_bus.clear()
        self._subscribed_channels.clear()
        logger.info("Redis PubSub manager closed")


pubsub_manager = RedisPubSubManager()
