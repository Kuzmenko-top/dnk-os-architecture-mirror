# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_repositories_workspace_member_repository"
# purpose: "Async PostgreSQL repository for Workspace Members CRUD and role governance"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncpg

logger = logging.getLogger("dnk.workspace.member_repository")


class WorkspaceMemberRepository:
    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self.pool = pool
        # In-memory storage fallback for offline/test mode
        self._members: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def set_pool(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def add_member(
        self,
        workspace_id: str,
        user_id: str,
        role: str,
        invited_by: str,
        status: str = "active"
    ) -> Dict[str, Any]:
        role = role.lower()
        status = status.lower()
        now = datetime.now(timezone.utc)

        member_data = {
            "workspace_id": workspace_id,
            "user_id": user_id,
            "role": role,
            "invited_by": invited_by,
            "invited_at": now.isoformat(),
            "status": status
        }

        if self.pool:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO workspace_members (workspace_id, user_id, role, invited_by, invited_at, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (workspace_id, user_id) DO UPDATE SET
                        role = EXCLUDED.role,
                        invited_by = EXCLUDED.invited_by,
                        status = EXCLUDED.status
                    """,
                    workspace_id, user_id, role, invited_by, now, status
                )
        else:
            if workspace_id not in self._members:
                self._members[workspace_id] = {}
            self._members[workspace_id][user_id] = member_data

        return member_data

    async def get_members(self, workspace_id: str) -> List[Dict[str, Any]]:
        if self.pool:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT workspace_id, user_id, role, invited_by, invited_at, status "
                    "FROM workspace_members WHERE workspace_id = $1 ORDER BY invited_at ASC",
                    workspace_id
                )
                res = []
                for r in rows:
                    item = dict(r)
                    if isinstance(item.get("invited_at"), datetime):
                        item["invited_at"] = item["invited_at"].isoformat()
                    res.append(item)
                return res
        else:
            ws_m = self._members.get(workspace_id, {})
            return list(ws_m.values())

    async def get_member(self, workspace_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if self.pool:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT workspace_id, user_id, role, invited_by, invited_at, status "
                    "FROM workspace_members WHERE workspace_id = $1 AND user_id = $2",
                    workspace_id, user_id
                )
                if not row:
                    return None
                item = dict(row)
                if isinstance(item.get("invited_at"), datetime):
                    item["invited_at"] = item["invited_at"].isoformat()
                return item
        else:
            return self._members.get(workspace_id, {}).get(user_id)

    async def update_member_role(self, workspace_id: str, user_id: str, role: str) -> Optional[Dict[str, Any]]:
        role = role.lower()
        if self.pool:
            async with self.pool.acquire() as conn:
                res = await conn.execute(
                    "UPDATE workspace_members SET role = $1 WHERE workspace_id = $2 AND user_id = $3",
                    role, workspace_id, user_id
                )
                if "UPDATE 0" in res:
                    return None
                return await self.get_member(workspace_id, user_id)
        else:
            member = self._members.get(workspace_id, {}).get(user_id)
            if not member:
                return None
            member["role"] = role
            return member

    async def remove_member(self, workspace_id: str, user_id: str) -> bool:
        if self.pool:
            async with self.pool.acquire() as conn:
                res = await conn.execute(
                    "DELETE FROM workspace_members WHERE workspace_id = $1 AND user_id = $2",
                    workspace_id, user_id
                )
                return "DELETE 1" in res or "DELETE 0" not in res
        else:
            if workspace_id in self._members and user_id in self._members[workspace_id]:
                del self._members[workspace_id][user_id]
                return True
            return False

    async def list_user_memberships(self, user_id: str) -> List[Dict[str, Any]]:
        if self.pool:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT m.workspace_id, m.user_id, m.role, m.status, w.name as workspace_name, w.tenant_id "
                    "FROM workspace_members m "
                    "JOIN workspaces w ON m.workspace_id = w.id "
                    "WHERE m.user_id = $1 AND m.status = 'active'",
                    user_id
                )
                return [dict(r) for r in rows]
        else:
            res = []
            for ws_id, members in self._members.items():
                if user_id in members and members[user_id]["status"] == "active":
                    res.append({
                        "workspace_id": ws_id,
                        "user_id": user_id,
                        "role": members[user_id]["role"],
                        "status": members[user_id]["status"],
                        "workspace_name": f"Workspace {ws_id}",
                        "tenant_id": "tenant_default"
                    })
            return res
