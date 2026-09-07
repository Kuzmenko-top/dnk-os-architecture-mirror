# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_redis_pubsub_manager"
# purpose: "Distributed Redis Pub/Sub Event Bus supporting Redis Cluster hashtags, Multi-Node WebSockets, and In-Memory Fallback"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import os
import json
import inspect
import asyncio
import logging
from typing import Optional, Callable, Dict, List, Any
import redis.asyncio as aioredis

logger = logging.getLogger("dnk.platform.redis_pubsub")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_CLUSTER_MODE = os.getenv("REDIS_CLUSTER_MODE", "false").lower() == "true"


class RedisPubSubManager:
    """
    Distributed Pub/Sub manager for horizontal WebSocket scaling.
    - Uses Redis Cluster hashtags `{workspace_id}` to guarantee single-slot co-location.
    - Seamlessly falls back to internal asyncio queues when Redis is offline or in local test mode.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or REDIS_URL
        self.client: Optional[aioredis.Redis] = None
        self._is_connected: bool = False
        self._subscriptions: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {}
        self._listener_tasks: Dict[str, asyncio.Task] = {}
        self._in_memory_channels: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {}

    def _get_workspace_channel(self, workspace_id: str) -> str:
        """Returns Redis cluster hashtag channel for workspace."""
        return f"dnk:events:{{{workspace_id}}}:workspace"

    def _get_tenant_channel(self, tenant_id: str) -> str:
        """Returns Redis cluster hashtag channel for tenant."""
        return f"dnk:events:{{{tenant_id}}}:tenant"

    async def connect(self) -> bool:
        """Connects to Redis server or cluster."""
        if self.client is None:
            try:
                self.client = aioredis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0
                )
                # Ping check
                await self.client.ping()
                self._is_connected = True
                logger.info("Successfully connected to Redis Event Bus at %s", self.redis_url)
            except Exception as e:
                logger.warning("Redis Event Bus unavailable (%s), operating in high-speed in-memory fallback mode", e)
                self.client = None
                self._is_connected = False
        return self._is_connected

    async def disconnect(self) -> None:
        """Closes Redis connections and cancels active subscription listeners."""
        for task in self._listener_tasks.values():
            task.cancel()
        self._listener_tasks.clear()

        if self.client:
            await self.client.aclose()
            self.client = None
            self._is_connected = False
        logger.info("Redis Event Bus disconnected.")

    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.client is not None

    async def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """Publishes an event payload to a channel (distributed Redis or in-memory)."""
        payload_str = json.dumps(message)

        if self.is_connected and self.client is not None:
            try:
                subscribers_count = await self.client.publish(channel, payload_str)
                return subscribers_count
            except Exception as e:
                logger.warning("Redis publish failed on channel %s (%s), dispatching via memory fallback", channel, e)

        # In-memory dispatch
        listeners = self._in_memory_channels.get(channel, [])
        for listener in listeners:
            try:
                if inspect.iscoroutinefunction(listener):
                    asyncio.create_task(listener(message))
                else:
                    listener(message)
            except Exception as ex:
                logger.error("Error in memory pubsub listener: %s", ex)
        return len(listeners)

    async def publish_workspace_event(
        self,
        workspace_id: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> int:
        """Dispatches an event to all nodes subscribed to a given workspace."""
        channel = self._get_workspace_channel(workspace_id)
        msg = {
            "channel": channel,
            "workspace_id": workspace_id,
            "event_type": event_type,
            "data": payload
        }
        return await self.publish(channel, msg)

    async def publish_tenant_event(
        self,
        tenant_id: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> int:
        """Dispatches an event to all nodes subscribed to a given tenant."""
        channel = self._get_tenant_channel(tenant_id)
        msg = {
            "channel": channel,
            "tenant_id": tenant_id,
            "event_type": event_type,
            "data": payload
        }
        return await self.publish(channel, msg)

    async def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """Subscribes a local listener callback to a Redis or in-memory channel."""
        # 1. Register in memory channel
        if channel not in self._in_memory_channels:
            self._in_memory_channels[channel] = []
        self._in_memory_channels[channel].append(callback)

        # 2. If Redis is connected, spawn listener task if not already listening
        if self.is_connected and self.client is not None and channel not in self._listener_tasks:
            pubsub = self.client.pubsub()
            await pubsub.subscribe(channel)

            async def _listen_loop():
                try:
                    async for raw_msg in pubsub.listen():
                        if raw_msg.get("type") == "message":
                            data_str = raw_msg.get("data", "{}")
                            try:
                                parsed = json.loads(data_str)
                            except Exception:
                                parsed = {"raw": data_str}
                            listeners = self._in_memory_channels.get(channel, [])
                            for cb in listeners:
                                try:
                                    if inspect.iscoroutinefunction(cb):
                                        await cb(parsed)
                                    else:
                                        cb(parsed)

                                except Exception as err:
                                    logger.error("Callback error in pubsub listener: %s", err)
                except asyncio.CancelledError:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                except Exception as e:
                    logger.warning("Pubsub listener for %s encountered error: %s", channel, e)

            self._listener_tasks[channel] = asyncio.create_task(_listen_loop())

    async def subscribe_workspace(
        self,
        workspace_id: str,
        callback: Callable[[Dict[str, Any]], Any]
    ) -> None:
        channel = self._get_workspace_channel(workspace_id)
        await self.subscribe(channel, callback)

    async def unsubscribe_workspace(self, workspace_id: str) -> None:
        channel = self._get_workspace_channel(workspace_id)
        self._in_memory_channels.pop(channel, None)
        task = self._listener_tasks.pop(channel, None)
        if task:
            task.cancel()


redis_pubsub_manager = RedisPubSubManager()
