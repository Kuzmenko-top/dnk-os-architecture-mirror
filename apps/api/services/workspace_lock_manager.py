# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_workspace_lock_manager"
# purpose: "Pessimistic Workspace Section Lock Manager with Redis Cluster, Standalone, and in-memory fallback, TTL expiration, and conflict detection"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import asyncio
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from apps.api.services.redis_client import redis_client

logger = logging.getLogger("dnk.workspace.lock_manager")


class WorkspaceLockManager:
    """
    Manages pessimistic section locks for collaborative multi-user editing.
    Supports in-memory tracking with TTL expiration and distributed Redis Cluster/Standalone integration.
    Uses Redis hash tags '{workspace_id}' to ensure cluster slot affinity.
    """

    def __init__(self, default_ttl: int = 60):
        self.default_ttl = default_ttl
        # In-memory lock store: {f"{workspace_id}:{section_id}": lock_data}
        self._memory_locks: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def _make_key(self, workspace_id: str, section_id: str) -> str:
        # Hash tag ensures that locks for the same workspace hit the same cluster shard
        return f"dnk:lock:{{{workspace_id}}}:{section_id}"

    async def acquire_lock(
        self,
        workspace_id: str,
        section_id: str,
        user_id: str,
        ttl_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Attempts to acquire a pessimistic lock on a section for a user.
        Returns result dict with success=True and lock info, or success=False and conflict info.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()
        expires_at = now + ttl
        key = self._make_key(workspace_id, section_id)

        # 1. Redis path if available
        client = redis_client.get_client()
        if client and hasattr(client, "set"):
            try:
                lock_payload = json.dumps({
                    "workspace_id": workspace_id,
                    "section_id": section_id,
                    "user_id": user_id,
                    "locked_at": now,
                    "expires_at": expires_at,
                    "ttl_seconds": ttl
                })
                # NX = set only if not exists, EX = expire seconds
                acquired = await client.set(key, lock_payload, nx=True, ex=ttl)
                if acquired:
                    return {
                        "success": True,
                        "lock": {
                            "workspace_id": workspace_id,
                            "section_id": section_id,
                            "user_id": user_id,
                            "locked_at": now,
                            "expires_at": expires_at,
                            "ttl_seconds": ttl
                        }
                    }
                else:
                    # Retrieve existing lock holder
                    existing = await client.get(key)
                    if existing:
                        data = json.loads(existing) if isinstance(existing, str) else existing
                        if data.get("user_id") == user_id:
                            # Re-entrant: extend TTL
                            await client.set(key, lock_payload, ex=ttl)
                            return {
                                "success": True,
                                "lock": {
                                    "workspace_id": workspace_id,
                                    "section_id": section_id,
                                    "user_id": user_id,
                                    "locked_at": now,
                                    "expires_at": expires_at,
                                    "ttl_seconds": ttl,
                                    "renewed": True
                                }
                            }
                        return {
                            "success": False,
                            "conflict": {
                                "error": "SECTION_ALREADY_LOCKED",
                                "section_id": section_id,
                                "user_id": data.get("user_id"),
                                "locked_by": data.get("user_id"),
                                "expires_at": data.get("expires_at"),
                                "remaining_seconds": max(0, int(data.get("expires_at", 0) - now))
                            }
                        }
            except Exception as e:
                logger.warning("Redis lock acquisition error, falling back to memory: %s", e)

        # 2. In-memory fallback
        async with self._lock:
            existing = self._memory_locks.get(key)
            if existing:
                # Check expiration
                if existing.get("expires_at", 0) <= now:
                    # Expired, clean it up
                    del self._memory_locks[key]
                elif existing.get("user_id") == user_id:
                    # Re-entrant / renew
                    existing["expires_at"] = expires_at
                    existing["ttl_seconds"] = ttl
                    existing["renewed"] = True
                    return {"success": True, "lock": existing}
                else:
                    # Active conflict
                    return {
                        "success": False,
                        "conflict": {
                            "error": "SECTION_ALREADY_LOCKED",
                            "section_id": section_id,
                            "user_id": existing.get("user_id"),
                            "locked_by": existing.get("user_id"),
                            "expires_at": existing.get("expires_at"),
                            "remaining_seconds": max(0, int(existing.get("expires_at", 0) - now))
                        }
                    }

            lock_data = {
                "workspace_id": workspace_id,
                "section_id": section_id,
                "user_id": user_id,
                "locked_at": now,
                "expires_at": expires_at,
                "ttl_seconds": ttl
            }
            self._memory_locks[key] = lock_data
            return {"success": True, "lock": lock_data}

    async def release_lock(self, workspace_id: str, section_id: str, user_id: str) -> bool:
        """
        Releases a lock held by user_id on a section.
        Returns True if released, False if not held by user.
        """
        key = self._make_key(workspace_id, section_id)
        client = redis_client.get_client()

        if client and hasattr(client, "get"):
            try:
                existing = await client.get(key)
                if existing:
                    data = json.loads(existing) if isinstance(existing, str) else existing
                    if data.get("user_id") == user_id:
                        await client.delete(key)
                        return True
                    return False
            except Exception as e:
                logger.warning("Redis lock release error: %s", e)

        async with self._lock:
            existing = self._memory_locks.get(key)
            if existing:
                if existing.get("user_id") == user_id:
                    del self._memory_locks[key]
                    return True
                return False
            return False

    async def is_locked_by_other(self, workspace_id: str, section_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Checks if a section is locked by another user.
        Returns conflict dict if locked by another, None otherwise.
        """
        key = self._make_key(workspace_id, section_id)
        now = time.time()
        client = redis_client.get_client()

        if client and hasattr(client, "get"):
            try:
                existing = await client.get(key)
                if existing:
                    data = json.loads(existing) if isinstance(existing, str) else existing
                    if data.get("user_id") != user_id:
                        return {
                            "error": "SECTION_LOCKED_BY_ANOTHER_USER",
                            "section_id": section_id,
                            "locked_by": data.get("user_id"),
                            "expires_at": data.get("expires_at"),
                            "remaining_seconds": max(0, int(data.get("expires_at", 0) - now))
                        }
            except Exception as e:
                logger.warning("Redis is_locked_by_other check error: %s", e)

        async with self._lock:
            existing = self._memory_locks.get(key)
            if existing:
                if existing.get("expires_at", 0) <= now:
                    del self._memory_locks[key]
                    return None
                if existing.get("user_id") != user_id:
                    return {
                        "error": "SECTION_LOCKED_BY_ANOTHER_USER",
                        "section_id": section_id,
                        "locked_by": existing.get("user_id"),
                        "expires_at": existing.get("expires_at"),
                        "remaining_seconds": max(0, int(existing.get("expires_at", 0) - now))
                    }
        return None

    async def get_locks(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Returns all active locks for a workspace.
        """
        now = time.time()
        active_locks: List[Dict[str, Any]] = []

        client = redis_client.get_client()
        if client and hasattr(client, "keys"):
            try:
                pattern = f"dnk:lock:{{{workspace_id}}}:*"
                keys = await client.keys(pattern)
                for k in keys:
                    if isinstance(k, (bytes, bytearray)):
                        k = k.decode("utf-8")
                    val = await client.get(k)
                    if val:
                        data = json.loads(val) if isinstance(val, str) else val
                        if data.get("expires_at", 0) > now:
                            active_locks.append(data)
                if active_locks or keys:
                    return active_locks
            except Exception as e:
                logger.warning("Redis get_locks error: %s", e)

        async with self._lock:
            expired_keys = []
            prefix = f"dnk:lock:{{{workspace_id}}}:"
            for k, v in self._memory_locks.items():
                if k.startswith(prefix):
                    if v.get("expires_at", 0) <= now:
                        expired_keys.append(k)
                    else:
                        active_locks.append(v)
            for k in expired_keys:
                del self._memory_locks[k]

        return active_locks

    async def release_all_user_locks(self, workspace_id: str, user_id: str) -> List[str]:
        """
        Releases all locks held by a user in a workspace (e.g. on disconnect).
        Returns list of released section_ids.
        """
        released_sections: List[str] = []

        client = redis_client.get_client()
        if client and hasattr(client, "keys"):
            try:
                pattern = f"dnk:lock:{{{workspace_id}}}:*"
                keys = await client.keys(pattern)
                for k in keys:
                    k_str = k.decode("utf-8") if isinstance(k, (bytes, bytearray)) else k
                    val = await client.get(k)
                    if val:
                        data = json.loads(val) if isinstance(val, str) else val
                        if data.get("user_id") == user_id:
                            sec_id = data.get("section_id") or k_str.split(":")[-1]
                            released_sections.append(sec_id)
                            await client.delete(k)
            except Exception as e:
                logger.warning("Redis release_all_user_locks error: %s", e)

        prefix = f"dnk:lock:{{{workspace_id}}}:"
        async with self._lock:
            keys_to_delete = []
            for k, v in self._memory_locks.items():
                if k.startswith(prefix) and v.get("user_id") == user_id:
                    sec_id = v.get("section_id", "")
                    if sec_id not in released_sections:
                        released_sections.append(sec_id)
                    keys_to_delete.append(k)
            for k in keys_to_delete:
                del self._memory_locks[k]

        return released_sections

    async def clear(self):
        """Clears all in-memory locks (useful for test resets)."""
        async with self._lock:
            self._memory_locks.clear()


workspace_lock_manager = WorkspaceLockManager()
