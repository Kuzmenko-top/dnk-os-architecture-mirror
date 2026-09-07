# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_sharding"
# purpose: "Tenant Shard Router and Sharded Connection Pool Manager for multi-tenant PostgreSQL horizontal scaling"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import os
import hashlib
import logging
from typing import Dict, Optional, Any, List
import asyncpg

from apps.api.db.database import db_manager, PoolRole

logger = logging.getLogger("dnk.workspace.sharding")

DEFAULT_NUM_SHARDS = int(os.getenv("TENANT_NUM_SHARDS", "4"))


class TenantShardRouter:
    """
    Routes tenant queries to specific database shards based on deterministic tenant_id hashing.
    Manages shard connection pools with graceful fallback to default master pool.
    """

    def __init__(self, num_shards: int = DEFAULT_NUM_SHARDS):
        self.num_shards = max(1, num_shards)
        self.shard_dsns: Dict[int, str] = {}
        self.shard_pools: Dict[int, asyncpg.Pool] = {}
        self._load_env_shards()

    def _load_env_shards(self) -> None:
        """Loads shard DSNs from environment variables (DATABASE_SHARD_0_URL, etc.)."""
        for i in range(self.num_shards):
            dsn = os.getenv(f"DATABASE_SHARD_{i}_URL")
            if dsn and dsn.strip():
                self.shard_dsns[i] = dsn.strip()

    def get_shard_for_tenant(self, tenant_id: str) -> int:
        """
        Deterministically maps tenant_id to a shard index [0..num_shards-1]
        using stable MD5 hashing across process restarts.
        """
        if not tenant_id:
            return 0
        digest = hashlib.md5(tenant_id.encode("utf-8")).hexdigest()
        return int(digest, 16) % self.num_shards

    def get_shard_dsn(self, tenant_id: str) -> Optional[str]:
        """Returns the DSN for a tenant's assigned shard."""
        shard_id = self.get_shard_for_tenant(tenant_id)
        return self.shard_dsns.get(shard_id) or os.getenv(f"DATABASE_SHARD_{shard_id}_URL")

    def register_shard(self, shard_id: int, dsn: str) -> None:
        """Registers or overrides a shard DSN dynamically."""
        self.shard_dsns[shard_id] = dsn
        if shard_id >= self.num_shards:
            self.num_shards = shard_id + 1

    async def init_shard_pool(self, shard_id: int) -> Optional[asyncpg.Pool]:
        """Initializes a connection pool for a specific shard."""
        dsn = self.shard_dsns.get(shard_id)
        if not dsn:
            return None
        if shard_id in self.shard_pools and not self.shard_pools[shard_id]._closed:
            return self.shard_pools[shard_id]

        try:
            pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=int(os.getenv("DB_SHARD_POOL_MIN_SIZE", "2")),
                max_size=int(os.getenv("DB_SHARD_POOL_MAX_SIZE", "8")),
                timeout=float(os.getenv("DB_SHARD_POOL_TIMEOUT", "20.0"))
            )
            self.shard_pools[shard_id] = pool
            logger.info("Initialized connection pool for PostgreSQL Shard #%s", shard_id)
            return pool
        except Exception as e:
            logger.warning("Failed to initialize pool for shard #%s (%s): %s", shard_id, dsn, e)
            return None

    async def get_pool_for_tenant(self, tenant_id: str) -> Optional[asyncpg.Pool]:
        """
        Returns connection pool for tenant. If shard pool is not active or configured,
        falls back to central DatabaseManager master pool.
        """
        shard_id = self.get_shard_for_tenant(tenant_id)
        if shard_id in self.shard_pools and not self.shard_pools[shard_id]._closed:
            return self.shard_pools[shard_id]

        if shard_id in self.shard_dsns:
            pool = await self.init_shard_pool(shard_id)
            if pool:
                return pool

        # Fallback to standard master pool
        return db_manager.get_pool(PoolRole.MASTER)

    def get_shard_distribution_stats(self) -> Dict[str, Any]:
        """Returns metadata regarding active shards and connection pools."""
        return {
            "num_shards": self.num_shards,
            "registered_shards": list(self.shard_dsns.keys()),
            "active_pools": [sid for sid, p in self.shard_pools.items() if p and not p._closed]
        }

    async def close(self) -> None:
        """Closes all active shard connection pools."""
        for shard_id, pool in self.shard_pools.items():
            if pool and not pool._closed:
                await pool.close()
                logger.info("Closed pool for PostgreSQL Shard #%s", shard_id)
        self.shard_pools.clear()


shard_router = TenantShardRouter()
