# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_tenant_router"
# purpose: "Consistent Hashing Tenant Shard Router with RLS Boundary Enforcement and Shard Overrides"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import hashlib
import bisect
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("dnk.platform.tenant_router")


class TenantShardRouter:
    """
    High-performance consistent-hashing and modular shard router for multi-tenant isolation.
    """

    def __init__(
        self,
        shards: Optional[List[str]] = None,
        virtual_replicas: int = 100
    ):
        self.shards: List[str] = shards or ["shard-primary"]
        self.virtual_replicas = virtual_replicas
        self._ring: List[int] = []
        self._ring_nodes: Dict[int, str] = {}
        self._overrides: Dict[str, str] = {}
        self._rebuild_ring()

    def _hash(self, key: str) -> int:
        """MD5-based 32-bit consistent hash key."""
        return int(hashlib.md5(key.encode("utf-8")).hexdigest()[:8], 16)

    def _rebuild_ring(self) -> None:
        """Constructs virtual node distribution ring."""
        self._ring.clear()
        self._ring_nodes.clear()
        for shard in self.shards:
            for v in range(self.virtual_replicas):
                v_key = f"{shard}:vnode_{v}"
                h = self._hash(v_key)
                self._ring.append(h)
                self._ring_nodes[h] = shard
        self._ring.sort()

    def set_shards(self, shards: List[str]) -> None:
        """Dynamically updates active shard clusters and rebalances the ring."""
        if not shards:
            raise ValueError("Shards list cannot be empty.")
        self.shards = list(shards)
        self._rebuild_ring()

    def set_tenant_override(self, tenant_id: str, shard_id: str) -> None:
        """Explicitly pins a high-value or dedicated tenant to a specific shard cluster."""
        self._overrides[tenant_id] = shard_id

    def remove_tenant_override(self, tenant_id: str) -> None:
        self._overrides.pop(tenant_id, None)

    def get_shard_for_tenant(self, tenant_id: str) -> str:
        """
        Resolves the target shard cluster for a given tenant_id.
        Priority:
        1. Explicit pinned override
        2. Consistent hash ring lookup
        """
        if not tenant_id or not tenant_id.strip():
            return self.shards[0]

        clean_tenant = tenant_id.strip()

        # 1. Override
        if clean_tenant in self._overrides:
            return self._overrides[clean_tenant]

        if not self._ring:
            return self.shards[0]

        # 2. Consistent Hash Ring
        h = self._hash(clean_tenant)
        idx = bisect.bisect_right(self._ring, h)
        if idx == len(self._ring):
            idx = 0
        node_hash = self._ring[idx]
        return self._ring_nodes[node_hash]

    def get_modular_shard_index(self, tenant_id: str, num_shards: Optional[int] = None) -> int:
        """Alternative deterministic modular hashing index: hash(tenant_id) % N."""
        n = num_shards or len(self.shards)
        if n <= 1:
            return 0
        return self._hash(tenant_id) % n

    @staticmethod
    def verify_tenant_boundary(actor_tenant_id: str, target_tenant_id: str) -> bool:
        """
        Guarantees cross-tenant boundary isolation.
        Returns True if authorized, False if violation attempt detected.
        """
        if not actor_tenant_id or not target_tenant_id:
            return False
        return actor_tenant_id.strip() == target_tenant_id.strip()

    @staticmethod
    def format_rls_context_statement(tenant_id: str) -> str:
        """Formats safe session context parameter for PostgreSQL RLS."""
        # Sanitize single quotes to protect against SQL injection in session setting
        safe_tenant = tenant_id.replace("'", "''")
        return f"SET LOCAL dnk.current_tenant_id = '{safe_tenant}';"


tenant_shard_router = TenantShardRouter()
