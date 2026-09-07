# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_repositories_workspace_repository"
# purpose: "PostgreSQL asyncpg repository implementations for Workspace, Prompts, Diffs, Approvals, Snapshots, Commits, and Audit Trail"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import json
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
import asyncpg

from apps.api.db.database import db_manager, PoolRole

logger = logging.getLogger("dnk.workspace.repository")


class WorkspaceRepository:
    """PostgreSQL repository handling workspaces, nodes, edges, and state transitions with Master/Replica routing."""

    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self.pool = pool

    def set_pool(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    def _get_pool(self, role: PoolRole = PoolRole.MASTER) -> Optional[asyncpg.Pool]:
        if self.pool is not None:
            return self.pool
        return db_manager.get_pool(role)

    async def get_workspace(self, workspace_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        pool = self._get_pool(PoolRole.REPLICA)
        if not pool:
            return None
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, tenant_id, name, version, state, last_active, created_at, updated_at "
                "FROM workspaces WHERE id = $1 AND tenant_id = $2",
                workspace_id, tenant_id
            )
            if not row:
                return None

            nodes = await conn.fetch(
                "SELECT node_id, type, label, file_path, data FROM workspace_nodes "
                "WHERE workspace_id = $1 ORDER BY created_at ASC",
                workspace_id
            )
            edges = await conn.fetch(
                "SELECT source, target, type FROM workspace_edges "
                "WHERE workspace_id = $1 ORDER BY created_at ASC",
                workspace_id
            )

            last_active_val = row["last_active"]
            if isinstance(last_active_val, datetime):
                last_active_str = last_active_val.isoformat()
            else:
                last_active_str = str(last_active_val) if last_active_val else None

            return {
                "workspace_id": row["id"],
                "tenant_id": row["tenant_id"],
                "name": row["name"],
                "metadata": {
                    "version": row["version"],
                    "state": row["state"],
                    "last_active": last_active_str
                },
                "nodes": [
                    {
                        "id": n["node_id"],
                        "type": n["type"],
                        "label": n["label"],
                        "file_path": n["file_path"],
                        **({"data": n["data"]} if n["data"] else {})
                    }
                    for n in nodes
                ],
                "edges": [
                    {
                        "source": e["source"],
                        "target": e["target"],
                        "type": e["type"]
                    }
                    for e in edges
                ]
            }

    async def save_workspace(self, ws: Dict[str, Any]) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                ws_id = ws["workspace_id"]
                tenant_id = ws["tenant_id"]
                name = ws.get("name", "Workspace")
                version = ws.get("metadata", {}).get("version", 1)
                state = ws.get("metadata", {}).get("state", "ACTIVE")
                now = datetime.now(timezone.utc)

                await conn.execute(
                    """
                    INSERT INTO workspaces (id, tenant_id, name, version, state, last_active, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO UPDATE SET
                        tenant_id = EXCLUDED.tenant_id,
                        name = EXCLUDED.name,
                        version = EXCLUDED.version,
                        state = EXCLUDED.state,
                        last_active = EXCLUDED.last_active,
                        updated_at = EXCLUDED.updated_at
                    """,
                    ws_id, tenant_id, name, version, state, now, now, now
                )

                # Replace nodes
                await conn.execute("DELETE FROM workspace_nodes WHERE workspace_id = $1", ws_id)
                for node in ws.get("nodes", []):
                    node_id = node.get("id") or node.get("node_id")
                    node_type = node.get("type", "node")
                    label = node.get("label", "")
                    file_path = node.get("file_path")
                    data = node.get("data")
                    pk = f"{ws_id}_{node_id}"
                    await conn.execute(
                        """
                        INSERT INTO workspace_nodes (id, workspace_id, node_id, type, label, file_path, data, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        pk, ws_id, node_id, node_type, label, file_path, data, now
                    )

                # Replace edges
                await conn.execute("DELETE FROM workspace_edges WHERE workspace_id = $1", ws_id)
                for edge in ws.get("edges", []):
                    source = edge.get("source")
                    target = edge.get("target")
                    edge_type = edge.get("type")
                    pk = f"{ws_id}_{source}_{target}"
                    await conn.execute(
                        """
                        INSERT INTO workspace_edges (id, workspace_id, source, target, type, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        pk, ws_id, source, target, edge_type, now
                    )

    async def update_workspace_version(self, workspace_id: str, new_version: int) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE workspaces SET version = $1, updated_at = $2 WHERE id = $3",
                new_version, datetime.now(timezone.utc), workspace_id
            )

    async def set_workspace_state(self, workspace_id: str, state: str) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE workspaces SET state = $1, updated_at = $2 WHERE id = $3",
                state, datetime.now(timezone.utc), workspace_id
            )

    async def restore_workspace_state(
        self,
        workspace_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        version: int
    ) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                now = datetime.now(timezone.utc)
                await conn.execute(
                    "UPDATE workspaces SET version = $1, updated_at = $2 WHERE id = $3",
                    version, now, workspace_id
                )

                # Restore nodes
                await conn.execute("DELETE FROM workspace_nodes WHERE workspace_id = $1", workspace_id)
                for node in nodes:
                    node_id = node.get("id") or node.get("node_id")
                    node_type = node.get("type", "node")
                    label = node.get("label", "")
                    file_path = node.get("file_path")
                    data = node.get("data")
                    pk = f"{workspace_id}_{node_id}"
                    await conn.execute(
                        """
                        INSERT INTO workspace_nodes (id, workspace_id, node_id, type, label, file_path, data, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        pk, workspace_id, node_id, node_type, label, file_path, data, now
                    )

                # Restore edges
                await conn.execute("DELETE FROM workspace_edges WHERE workspace_id = $1", workspace_id)
                for edge in edges:
                    source = edge.get("source")
                    target = edge.get("target")
                    edge_type = edge.get("type")
                    pk = f"{workspace_id}_{source}_{target}"
                    await conn.execute(
                        """
                        INSERT INTO workspace_edges (id, workspace_id, source, target, type, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        pk, workspace_id, source, target, edge_type, now
                    )


class WorkspacePromptRepository:
    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self.pool = pool

    def set_pool(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def save_prompt(self, entry: Dict[str, Any]) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO workspace_prompts (
                    prompt_id, task_id, workspace_id, tenant_id, user_id, prompt,
                    target_node_id, context_parameters, status, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (prompt_id) DO UPDATE SET
                    status = EXCLUDED.status
                """,
                entry["prompt_id"],
                entry["task_id"],
                entry["workspace_id"],
                entry["tenant_id"],
                entry["user_id"],
                entry["prompt"],
                entry.get("target_node_id"),
                entry.get("context_parameters"),
                entry.get("status", "SUBMITTED"),
                datetime.now(timezone.utc)
            )

    async def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM workspace_prompts WHERE prompt_id = $1", prompt_id
            )
            return dict(row) if row else None


class WorkspaceDiffRepository:
    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self.pool = pool

    def set_pool(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def save_diff(self, entry: Dict[str, Any]) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO workspace_diffs (
                    diff_id, task_id, workspace_id, tenant_id, status,
                    staged_diff_hash, preview_hash, files, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (diff_id) DO UPDATE SET
                    status = EXCLUDED.status
                """,
                entry["diff_id"],
                entry["task_id"],
                entry["workspace_id"],
                entry["tenant_id"],
                entry.get("status", "STAGED"),
                entry["staged_diff_hash"],
                entry["preview_hash"],
                entry.get("files", []),
                datetime.now(timezone.utc)
            )

    async def get_diff(self, diff_id: str) -> Optional[Dict[str, Any]]:
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM workspace_diffs WHERE diff_id = $1", diff_id
            )
            return dict(row) if row else None


class WorkspaceApprovalRepository:
    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self.pool = pool

    def set_pool(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def save_approval(self, card: Dict[str, Any]) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO workspace_approvals (
                    approval_id, workspace_id, tenant_id, staged_diff_hash, summary,
                    status, approval_signature, created_by, approved_by, approved_at,
                    rejected_by, rejected_at, expires_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (approval_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    approved_by = EXCLUDED.approved_by,
                    approved_at = EXCLUDED.approved_at,
                    rejected_by = EXCLUDED.rejected_by,
                    rejected_at = EXCLUDED.rejected_at
                """,
                card["approval_id"],
                card["workspace_id"],
                card["tenant_id"],
                card["staged_diff_hash"],
                card["summary"],
                card["status"],
                card["approval_signature"],
                card["created_by"],
                card.get("approved_by"),
                datetime.fromisoformat(card["approved_at"]) if card.get("approved_at") else None,
                card.get("rejected_by"),
                datetime.fromisoformat(card["rejected_at"]) if card.get("rejected_at") else None,
                int(card["expires_at"]),
                datetime.now(timezone.utc)
            )

    async def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM workspace_approvals WHERE approval_id = $1", approval_id
            )
            if not row:
                return None
            res = dict(row)
            if isinstance(res.get("created_at"), datetime):
                res["created_at"] = res["created_at"].isoformat()
            if isinstance(res.get("approved_at"), datetime):
                res["approved_at"] = res["approved_at"].isoformat()
            if isinstance(res.get("rejected_at"), datetime):
                res["rejected_at"] = res["rejected_at"].isoformat()
            return res

    async def clear_pending_approvals(self, workspace_id: str, tenant_id: str) -> int:
        if not self.pool:
            return 0
        async with self.pool.acquire() as conn:
            res = await conn.execute(
                "DELETE FROM workspace_approvals WHERE workspace_id = $1 AND tenant_id = $2 AND status = 'PENDING'",
                workspace_id, tenant_id
            )
            # res is e.g. "DELETE 3"
            parts = res.split()
            return int(parts[1]) if len(parts) > 1 else 0


class WorkspaceSnapshotRepository:
    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self.pool = pool

    def set_pool(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def save_snapshot(self, snapshot: Dict[str, Any]) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO workspace_snapshots (
                    snapshot_id, workspace_id, tenant_id, pre_hash, nodes_state,
                    edges_state, version, created_by, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (snapshot_id) DO NOTHING
                """,
                snapshot["snapshot_id"],
                snapshot["workspace_id"],
                snapshot["tenant_id"],
                snapshot["pre_hash"],
                snapshot["nodes_state"],
                snapshot["edges_state"],
                snapshot["version"],
                snapshot["created_by"],
                datetime.now(timezone.utc)
            )

    async def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM workspace_snapshots WHERE snapshot_id = $1", snapshot_id
            )
            if not row:
                return None
            res = dict(row)
            if isinstance(res.get("created_at"), datetime):
                res["created_at"] = res["created_at"].isoformat()
            return res


class WorkspaceCommitRepository:
    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self.pool = pool

    def set_pool(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def save_commit(self, commit: Dict[str, Any]) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO workspace_commits (
                    commit_id, workspace_id, tenant_id, status, new_version,
                    diff_id, idempotency_key, committed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (commit_id) DO NOTHING
                """,
                commit["commit_id"],
                commit["workspace_id"],
                commit["tenant_id"],
                commit.get("status", "COMMITTED"),
                commit["new_version"],
                commit.get("diff_id"),
                commit["idempotency_key"],
                datetime.now(timezone.utc)
            )

    async def get_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT response_data FROM workspace_idempotency_cache WHERE idempotency_key = $1",
                idempotency_key
            )
            return row["response_data"] if row else None

    async def save_idempotency(self, idempotency_key: str, workspace_id: str, tenant_id: str, response_data: Dict[str, Any]) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO workspace_idempotency_cache (
                    idempotency_key, workspace_id, tenant_id, response_data, created_at
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (idempotency_key) DO UPDATE SET
                    response_data = EXCLUDED.response_data
                """,
                idempotency_key,
                workspace_id,
                tenant_id,
                response_data,
                datetime.now(timezone.utc)
            )


class WorkspaceAuditRepository:
    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self.pool = pool

    def set_pool(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def save_event(self, event: Dict[str, Any]) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO workspace_audit_trail (
                    event_id, workspace_id, tenant_id, actor, action, details, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (event_id) DO NOTHING
                """,
                event["event_id"],
                event["workspace_id"],
                event["tenant_id"],
                event["actor"],
                event["action"],
                event.get("details", {}),
                datetime.now(timezone.utc)
            )

    async def get_audit_trail(self, workspace_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        if not self.pool:
            return []
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT event_id, workspace_id, tenant_id, actor, action, details, timestamp "
                "FROM workspace_audit_trail WHERE workspace_id = $1 AND tenant_id = $2 "
                "ORDER BY timestamp ASC",
                workspace_id, tenant_id
            )
            events = []
            for r in rows:
                ts = r["timestamp"]
                ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
                events.append({
                    "event_id": r["event_id"],
                    "workspace_id": r["workspace_id"],
                    "tenant_id": r["tenant_id"],
                    "actor": r["actor"],
                    "action": r["action"],
                    "details": r["details"],
                    "timestamp": ts_str
                })
            return events
