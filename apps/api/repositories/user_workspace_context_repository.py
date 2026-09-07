# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_repositories_user_workspace_context_repository"
# purpose: "Async PostgreSQL repository for User Workspace Context state and OCC switching"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import asyncpg

logger = logging.getLogger("dnk.workspace.user_context_repository")


class UserWorkspaceContextRepository:
    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self.pool = pool
        self._contexts: Dict[str, Dict[str, Any]] = {}

    def set_pool(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def get_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self.pool:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT user_id, active_workspace_id, last_switched_at, version "
                    "FROM user_workspace_context WHERE user_id = $1",
                    user_id
                )
                if not row:
                    return None
                item = dict(row)
                if isinstance(item.get("last_switched_at"), datetime):
                    item["last_switched_at"] = item["last_switched_at"].isoformat()
                return item
        else:
            return self._contexts.get(user_id)

    async def set_active_workspace(
        self,
        user_id: str,
        active_workspace_id: str,
        expected_version: Optional[int] = None
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        current = await self.get_context(user_id)

        if current:
            current_ver = current["version"]
            if expected_version is not None and expected_version != current_ver:
                raise ValueError(f"OCC_CONFLICT: expected version {expected_version}, current version is {current_ver}")
            next_version = current_ver + 1
        else:
            if expected_version is not None and expected_version != 1:
                raise ValueError(f"OCC_CONFLICT: expected version {expected_version}, current version is 1")
            next_version = 1

        if self.pool:
            async with self.pool.acquire() as conn:
                if current:
                    res = await conn.execute(
                        """
                        UPDATE user_workspace_context
                        SET active_workspace_id = $1, last_switched_at = $2, version = $3
                        WHERE user_id = $4 AND version = $5
                        """,
                        active_workspace_id, now, next_version, user_id, current["version"]
                    )
                    if "UPDATE 0" in res:
                        raise ValueError("OCC_CONFLICT: Concurrent update detected during active workspace switch")
                else:
                    await conn.execute(
                        """
                        INSERT INTO user_workspace_context (user_id, active_workspace_id, last_switched_at, version)
                        VALUES ($1, $2, $3, $4)
                        """,
                        user_id, active_workspace_id, now, next_version
                    )
        
        ctx_data = {
            "user_id": user_id,
            "active_workspace_id": active_workspace_id,
            "last_switched_at": now.isoformat(),
            "version": next_version
        }
        self._contexts[user_id] = ctx_data
        return ctx_data
