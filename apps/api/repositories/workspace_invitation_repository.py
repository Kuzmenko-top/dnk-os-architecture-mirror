# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_repositories_workspace_invitation_repository"
# purpose: "Async PostgreSQL repository for Workspace Invitations lifecycle (create, accept, reject, expire)"
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

logger = logging.getLogger("dnk.workspace.invitation_repository")


class WorkspaceInvitationRepository:
    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self.pool = pool
        self._invitations: Dict[str, Dict[str, Any]] = {}

    def set_pool(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def create_invitation(
        self,
        invitation_id: str,
        workspace_id: str,
        email: str,
        role: str,
        invited_by: str,
        expires_at: datetime
    ) -> Dict[str, Any]:
        role = role.lower()
        now = datetime.now(timezone.utc)

        inv_data = {
            "invitation_id": invitation_id,
            "workspace_id": workspace_id,
            "email": email,
            "role": role,
            "invited_by": invited_by,
            "invited_at": now.isoformat(),
            "expires_at": expires_at.isoformat() if isinstance(expires_at, datetime) else expires_at,
            "status": "pending"
        }

        if self.pool:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO workspace_invitations (invitation_id, workspace_id, email, role, invited_by, invited_at, expires_at, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    invitation_id, workspace_id, email, role, invited_by, now, expires_at, "pending"
                )
        else:
            self._invitations[invitation_id] = inv_data

        return inv_data

    async def get_invitation(self, invitation_id: str) -> Optional[Dict[str, Any]]:
        if self.pool:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT invitation_id, workspace_id, email, role, invited_by, invited_at, expires_at, status "
                    "FROM workspace_invitations WHERE invitation_id = $1",
                    invitation_id
                )
                if not row:
                    return None
                item = dict(row)
                if isinstance(item.get("invited_at"), datetime):
                    item["invited_at"] = item["invited_at"].isoformat()
                if isinstance(item.get("expires_at"), datetime):
                    item["expires_at"] = item["expires_at"].isoformat()
                return item
        else:
            return self._invitations.get(invitation_id)

    async def list_invitations(self, workspace_id: str) -> List[Dict[str, Any]]:
        if self.pool:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT invitation_id, workspace_id, email, role, invited_by, invited_at, expires_at, status "
                    "FROM workspace_invitations WHERE workspace_id = $1 ORDER BY invited_at DESC",
                    workspace_id
                )
                res = []
                for r in rows:
                    item = dict(r)
                    if isinstance(item.get("invited_at"), datetime):
                        item["invited_at"] = item["invited_at"].isoformat()
                    if isinstance(item.get("expires_at"), datetime):
                        item["expires_at"] = item["expires_at"].isoformat()
                    res.append(item)
                return res
        else:
            return [inv for inv in self._invitations.values() if inv["workspace_id"] == workspace_id]

    async def update_invitation_status(self, invitation_id: str, status: str) -> Optional[Dict[str, Any]]:
        status = status.lower()
        if self.pool:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE workspace_invitations SET status = $1 WHERE invitation_id = $2",
                    status, invitation_id
                )
                return await self.get_invitation(invitation_id)
        else:
            inv = self._invitations.get(invitation_id)
            if not inv:
                return None
            inv["status"] = status
            return inv
