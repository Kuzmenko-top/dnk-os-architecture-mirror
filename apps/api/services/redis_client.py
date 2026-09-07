# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_redis_client"
# purpose: "Unified Redis Client supporting Redis Cluster, Standalone, and In-Memory fallback for horizontal scaling"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import os
import sys
import asyncio
import time
import logging
import fnmatch
from typing import Optional, Any, Dict, List, Union

logger = logging.getLogger("dnk.workspace.redis")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_CLUSTER_URLS = os.getenv("REDIS_CLUSTER_URLS", "")


class InMemoryRedisFallback:
    """Mock in-memory Redis client for tests and environments without active Redis."""
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._ttls: Dict[str, float] = {}

    async def get(self, key: str) -> Optional[str]:
        if key in self._ttls and time.time() > self._ttls[key]:
            self._store.pop(key, None)
            self._ttls.pop(key, None)
            return None
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None, nx: bool = False) -> bool:
        now = time.time()
        if key in self._ttls and now > self._ttls[key]:
            self._store.pop(key, None)
            self._ttls.pop(key, None)

        if nx and key in self._store:
            return False
        self._store[key] = value
        if ex is not None:
            self._ttls[key] = now + ex
        else:
            self._ttls.pop(key, None)
        return True

    async def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                self._ttls.pop(k, None)
                count += 1
        return count

    async def keys(self, pattern: str = "*") -> List[str]:
        now = time.time()
        expired = [k for k, exp in self._ttls.items() if now > exp]
        for k in expired:
            self._store.pop(k, None)
            self._ttls.pop(k, None)
        return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        self._store.clear()
        self._ttls.clear()

    async def close(self) -> None:
        await self.aclose()


class RedisClient:
    """
    Manages Redis connection with support for:
    1. Redis Cluster (distributed multi-node shard setup)
    2. Standalone Redis (single-node production / staging)
    3. In-Memory Mock Fallback (local dev / tests)
    """

    def __init__(self):
        self.cluster: Optional[Any] = None
        self.standalone: Optional[Any] = None
        self.fallback: InMemoryRedisFallback = InMemoryRedisFallback()
        self.is_cluster: bool = False
        self._connected: bool = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _is_test_mode(self) -> bool:
        return (
            os.getenv("FIXTURE_MODE", "false").lower() == "true"
            or os.getenv("TESTING", "false").lower() == "true"
            or "PYTEST_CURRENT_TEST" in os.environ
            or "pytest" in sys.modules
        )

    async def init(self) -> None:
        """Initializes cluster or standalone connection based on environment."""
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

        if self._is_test_mode():
            self.standalone = None
            self.cluster = None
            self.is_cluster = False
            self._connected = True
            return

        cluster_raw = os.getenv("REDIS_CLUSTER_URLS", REDIS_CLUSTER_URLS)
        cluster_nodes = [u.strip() for u in cluster_raw.split(",") if u.strip()]

        if cluster_nodes:
            # Cluster Mode
            try:
                import redis.asyncio as aioredis
                from redis.asyncio.cluster import RedisCluster, ClusterNode

                nodes = []
                for node_str in cluster_nodes:
                    clean = node_str.replace("redis://", "")
                    if "@" in clean:
                        clean = clean.split("@")[-1]
                    parts = clean.split(":")
                    host = parts[0]
                    port = int(parts[1]) if len(parts) > 1 else 6379
                    nodes.append(ClusterNode(host=host, port=port))

                cluster_instance = RedisCluster(
                    startup_nodes=nodes,
                    decode_responses=True,
                    socket_timeout=float(os.getenv("REDIS_TIMEOUT", "2.0"))
                )
                await cluster_instance.ping()
                self.cluster = cluster_instance
                self.is_cluster = True
                self._connected = True
                logger.info("Redis Cluster client connected (%s startup nodes)", len(nodes))
                return
            except Exception as e:
                logger.warning("Redis Cluster connection failed (%s), attempting fallback", e)
                if self.cluster:
                    try:
                        await self.cluster.aclose()
                    except Exception:
                        pass
                self.cluster = None
                self.is_cluster = False

        # Standalone Mode
        try:
            import redis.asyncio as aioredis
            redis_url = os.getenv("REDIS_URL", REDIS_URL)
            standalone_client = aioredis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=float(os.getenv("REDIS_TIMEOUT", "1.0"))
            )
            await standalone_client.ping()
            self.standalone = standalone_client
            self._connected = True
            logger.info("Redis Standalone client connected (%s)", redis_url.split("@")[-1] if "@" in redis_url else redis_url)
        except Exception as e:
            logger.info("Redis Standalone server unreachable (%s), using In-Memory Fallback", e)
            self.standalone = None
            self._connected = True  # Fallback is active and connected in-memory

    def get_client(self) -> Any:
        """Returns the active Redis client (Cluster, Standalone, or Fallback)."""
        try:
            current_loop = asyncio.get_running_loop()
            if self._loop and self._loop != current_loop:
                self.cluster = None
                self.standalone = None
                self._connected = False
                self._loop = None
        except RuntimeError:
            pass

        if self.is_cluster and self.cluster:
            return self.cluster
        if self.standalone:
            return self.standalone
        return self.fallback

    @property
    def is_connected(self) -> bool:
        try:
            current_loop = asyncio.get_running_loop()
            if self._loop and self._loop != current_loop:
                return False
        except RuntimeError:
            pass
        return self._connected

    async def ping(self) -> bool:
        client = self.get_client()
        try:
            return await client.ping()
        except Exception:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Returns health diagnostics for Redis deployment."""
        mode = "cluster" if self.is_cluster else ("standalone" if self.standalone else "in_memory_fallback")
        alive = await self.ping()
        status = "healthy" if alive and (self.is_cluster or self.standalone) else ("healthy_fallback" if alive else "unhealthy")
        return {
            "status": status,
            "healthy": alive,
            "mode": mode,
            "connected": self._connected,
            "cluster_nodes_count": len(self.cluster.nodes_manager.nodes) if self.is_cluster and self.cluster else 1
        }

    async def close(self) -> None:
        """Closes all connections."""
        if self.cluster:
            try:
                await self.cluster.aclose()
            except AttributeError:
                await self.cluster.close()
            self.cluster = None

        if self.standalone:
            try:
                await self.standalone.aclose()
            except AttributeError:
                await self.standalone.close()
            self.standalone = None

        await self.fallback.aclose()
        self._connected = False
        self.is_cluster = False
        logger.info("Redis client closed")


redis_client = RedisClient()
