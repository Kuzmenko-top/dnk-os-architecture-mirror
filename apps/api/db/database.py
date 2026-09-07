# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_database"
# purpose: "Enterprise Multi-Pool DatabaseManager supporting Master + Read Replicas, Round-Robin Load Balancing, and Automatic Failover"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import os
import json
import logging
from enum import Enum
from typing import Optional, Any, Dict, List, Union
from contextlib import asynccontextmanager
import asyncpg

logger = logging.getLogger("dnk.workspace.db")

class PoolRole(str, Enum):
    MASTER = "master"
    REPLICA = "replica"

DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("DATABASE_MASTER_URL", "postgresql://dnk:dnk_password@localhost:5432/dnk_os"))
DATABASE_READ_REPLICAS = os.getenv("DATABASE_READ_REPLICAS", "")

DB_POOL_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "5"))
DB_POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
DB_POOL_TIMEOUT = float(os.getenv("DB_POOL_TIMEOUT", "30.0"))


class DatabaseManager:
    """
    Enterprise-grade Multi-Pool PostgreSQL Manager.
    - Write queries route strictly to the Master database pool.
    - Read queries round-robin across healthy Read Replicas with zero-latency fallback to Master.
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        replica_dsns: Optional[List[str]] = None
    ):
        self.master_dsn = dsn or DATABASE_URL
        if replica_dsns is not None:
            self.replica_dsns = replica_dsns
        elif DATABASE_READ_REPLICAS.strip():
            self.replica_dsns = [r.strip() for r in DATABASE_READ_REPLICAS.split(",") if r.strip()]
        else:
            self.replica_dsns = []

        self.pool: Optional[asyncpg.Pool] = None  # Master pool (backward compatibility)
        self.replica_pools: List[asyncpg.Pool] = []
        self._replica_index: int = 0
        self._is_connected: bool = False

    async def _init_connection(self, conn: asyncpg.Connection):
        """Codec setup for JSON and JSONB columns."""
        try:
            await conn.set_type_codec(
                'jsonb',
                encoder=json.dumps,
                decoder=json.loads,
                schema='pg_catalog'
            )
            await conn.set_type_codec(
                'json',
                encoder=json.dumps,
                decoder=json.loads,
                schema='pg_catalog'
            )
        except Exception as e:
            logger.debug(f"JSON codec initialization note: {e}")

    async def connect(
        self,
        min_size: int = DB_POOL_MIN_SIZE,
        max_size: int = DB_POOL_MAX_SIZE,
        timeout: float = DB_POOL_TIMEOUT
    ) -> asyncpg.Pool:
        """Connects Master pool and all configured Read Replica pools."""
        # 1. Connect Master Pool
        if self.pool is None or self.pool._closed:
            try:
                self.pool = await asyncpg.create_pool(
                    dsn=self.master_dsn,
                    min_size=min_size,
                    max_size=max_size,
                    timeout=timeout,
                    init=self._init_connection
                )
                self._is_connected = True
                logger.info("Established Master PostgreSQL connection pool (%s-%s conns)", min_size, max_size)
            except Exception as e:
                logger.warning("Master PostgreSQL connection failed (%s), pool in offline/test mode", e)
                self._is_connected = False

        # 2. Connect Read Replica Pools
        self.replica_pools.clear()
        for i, rep_dsn in enumerate(self.replica_dsns):
            try:
                rep_pool = await asyncpg.create_pool(
                    dsn=rep_dsn,
                    min_size=min_size,
                    max_size=max_size,
                    timeout=timeout,
                    init=self._init_connection
                )
                self.replica_pools.append(rep_pool)
                logger.info("Established Read Replica #%s pool (%s)", i + 1, rep_dsn)
            except Exception as e:
                logger.warning("Read Replica #%s connection failed (%s), will fallback to Master", i + 1, e)

        return self.pool

    async def disconnect(self) -> None:
        """Gracefully drains and closes all Master and Replica pools."""
        if self.pool and not self.pool._closed:
            await self.pool.close()
            self.pool = None
            self._is_connected = False

        for rep_pool in self.replica_pools:
            if rep_pool and not rep_pool._closed:
                await rep_pool.close()
        self.replica_pools.clear()
        logger.info("All PostgreSQL connection pools closed.")

    @property
    def master_pool(self) -> Optional[asyncpg.Pool]:
        return self.pool

    @master_pool.setter
    def master_pool(self, value: Optional[asyncpg.Pool]) -> None:
        self.pool = value

    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.pool is not None and not self.pool._closed

    def get_pool(self, role: Union[PoolRole, str, bool] = PoolRole.MASTER, read_only: bool = False) -> Optional[asyncpg.Pool]:
        """
        Returns the appropriate pool:
        - If role is MASTER (or read_only is False): always Master pool.
        - If role is REPLICA (or read_only is True): round-robin across healthy replicas, falling back to Master.
        """
        is_read = read_only or (role in (PoolRole.REPLICA, "replica", True))
        if not is_read or not self.replica_pools:
            return self.master_pool

        # Filter active, non-closed replica pools
        healthy_replicas = [p for p in self.replica_pools if p and not p._closed]
        if not healthy_replicas:
            return self.master_pool

        # Round-robin selection
        selected = healthy_replicas[self._replica_index % len(healthy_replicas)]
        self._replica_index = (self._replica_index + 1) % len(healthy_replicas)
        return selected

    def get_replica_count(self) -> int:
        """Returns the number of active healthy read replica pools."""
        return len([p for p in self.replica_pools if p and not p._closed])

    @asynccontextmanager
    async def acquire(self, role: Union[PoolRole, str, bool] = PoolRole.MASTER, read_only: bool = False):
        """Context manager acquiring a connection from the routed pool."""
        pool = self.get_pool(role=role, read_only=read_only)
        if pool is None:
            raise ConnectionError("Database pool is not initialized or connected.")
        async with pool.acquire() as conn:
            yield conn

    async def execute(self, query: str, *args, read_only: bool = False) -> str:
        async with self.acquire(read_only=read_only) as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args, read_only: bool = True) -> List[asyncpg.Record]:
        async with self.acquire(read_only=read_only) as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args, read_only: bool = True) -> Optional[asyncpg.Record]:
        async with self.acquire(read_only=read_only) as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args, read_only: bool = True) -> Any:
        async with self.acquire(read_only=read_only) as conn:
            return await conn.fetchval(query, *args)

    async def check_health(self) -> Dict[str, Any]:
        """Returns comprehensive health metadata for Master and Replicas."""
        master_ok = self.is_connected
        replicas_status = []
        for i, rep_pool in enumerate(self.replica_pools):
            is_ok = rep_pool is not None and not rep_pool._closed
            replicas_status.append({
                "replica_id": i + 1,
                "healthy": is_ok,
                "free_conns": rep_pool.get_idle_size() if is_ok else 0,
                "size": rep_pool.get_size() if is_ok else 0
            })

        return {
            "master_connected": master_ok,
            "master_pool_size": self.pool.get_size() if master_ok else 0,
            "master_idle_size": self.pool.get_idle_size() if master_ok else 0,
            "total_replicas": len(self.replica_dsns),
            "active_replicas": len([r for r in replicas_status if r["healthy"]]),
            "replicas": replicas_status
        }


db_manager = DatabaseManager()


async def get_db_pool(read_only: bool = False) -> Optional[asyncpg.Pool]:
    if not db_manager.is_connected:
        await db_manager.connect()
    return db_manager.get_pool(read_only=read_only)
