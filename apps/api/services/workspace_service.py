# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_workspace_service"
# purpose: "Workspace service handling state, prompts, staged diffs, approvals, snapshots, OCC commits, rollbacks, kill-switch, and audit trail with PostgreSQL persistence support"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import time
import json
import hashlib
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
import asyncpg

from apps.api.db.database import DatabaseManager, db_manager
from apps.api.repositories.workspace_repository import (
    WorkspaceRepository,
    WorkspacePromptRepository,
    WorkspaceDiffRepository,
    WorkspaceApprovalRepository,
    WorkspaceSnapshotRepository,
    WorkspaceCommitRepository,
    WorkspaceAuditRepository
)

logger = logging.getLogger("dnk.workspace.service")

# Default Seed Workspaces
INITIAL_WORKSPACES: Dict[str, Dict[str, Any]] = {
    "ws_alpha": {
        "workspace_id": "ws_alpha",
        "tenant_id": "tenant_corp_a",
        "name": "Production Storefront Workspace",
        "metadata": {
            "version": 1,
            "state": "ACTIVE",
            "last_active": "2026-08-23T12:00:00Z"
        },
        "nodes": [
            {"id": "node_hero_01", "type": "section", "label": "Hero Banner", "file_path": "sections/hero-banner.liquid"},
            {"id": "node_product_grid_01", "type": "section", "label": "Featured Products", "file_path": "sections/product-grid.liquid"},
            {"id": "node_header_01", "type": "section", "label": "Main Header", "file_path": "sections/header.liquid"}
        ],
        "edges": [
            {"source": "node_header_01", "target": "node_hero_01", "type": "layout_flow"},
            {"source": "node_hero_01", "target": "node_product_grid_01", "type": "layout_flow"}
        ]
    },
    "ws_beta": {
        "workspace_id": "ws_beta",
        "tenant_id": "tenant_corp_a",
        "name": "Staging Storefront Workspace",
        "metadata": {
            "version": 1,
            "state": "ACTIVE",
            "last_active": "2026-08-23T12:00:00Z"
        },
        "nodes": [],
        "edges": []
    }
}


class WorkspaceService:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or db_manager
        self.workspace_repo = WorkspaceRepository(self.db.get_pool())
        self.prompt_repo = WorkspacePromptRepository(self.db.get_pool())
        self.diff_repo = WorkspaceDiffRepository(self.db.get_pool())
        self.approval_repo = WorkspaceApprovalRepository(self.db.get_pool())
        self.snapshot_repo = WorkspaceSnapshotRepository(self.db.get_pool())
        self.commit_repo = WorkspaceCommitRepository(self.db.get_pool())
        self.audit_repo = WorkspaceAuditRepository(self.db.get_pool())

        # In-memory fast cache & test storage fallback
        self.WORKSPACES_DB: Dict[str, Dict[str, Any]] = {k: dict(v) for k, v in INITIAL_WORKSPACES.items()}
        self.PROMPTS_DB: Dict[str, Dict[str, Any]] = {}
        self.DIFFS_DB: Dict[str, Dict[str, Any]] = {}
        self.APPROVALS_DB: Dict[str, Dict[str, Any]] = {}
        self.SNAPSHOTS_DB: Dict[str, Dict[str, Any]] = {}
        self.COMMITS_DB: Dict[str, Dict[str, Any]] = {}
        self.IDEMPOTENCY_CACHE: Dict[str, Dict[str, Any]] = {}
        self.AUDIT_TRAIL: List[Dict[str, Any]] = []

    def set_pool(self, pool: asyncpg.Pool) -> None:
        """Dynamically attach or reconfigure asyncpg connection pool."""
        self.workspace_repo.set_pool(pool)
        self.prompt_repo.set_pool(pool)
        self.diff_repo.set_pool(pool)
        self.approval_repo.set_pool(pool)
        self.snapshot_repo.set_pool(pool)
        self.commit_repo.set_pool(pool)
        self.audit_repo.set_pool(pool)

    def _execute_async(self, coro):
        """Helper to run async repository methods within sync service methods if needed."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In running loop (e.g. FastAPI / pytest-asyncio)
                task = asyncio.ensure_future(coro)
                return task
            else:
                return loop.run_until_complete(coro)
        except Exception:
            return asyncio.run(coro)

    def get_workspace_state(self, workspace_id: str, tenant_id: str) -> Dict[str, Any]:
        ws = self.WORKSPACES_DB.get(workspace_id)
        if not ws or ws["tenant_id"] != tenant_id:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "WORKSPACE_NOT_FOUND", "message": "Workspace not found"}
            )
        return ws

    async def get_workspace_state_async(self, workspace_id: str, tenant_id: str) -> Dict[str, Any]:
        if self.workspace_repo.pool:
            db_ws = await self.workspace_repo.get_workspace(workspace_id, tenant_id)
            if db_ws:
                return db_ws
        return self.get_workspace_state(workspace_id, tenant_id)

    def submit_prompt(
        self,
        workspace_id: str,
        tenant_id: str,
        user_id: str,
        prompt: str,
        target_node_id: Optional[str] = None,
        context_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        ws = self.get_workspace_state(workspace_id, tenant_id)
        if ws["metadata"].get("state") == "LOCKED_READ_ONLY":
            raise HTTPException(
                status_code=403,
                detail={"error_code": "WORKSPACE_LOCKED_READ_ONLY", "message": "Workspace is locked in read-only mode"}
            )

        if not prompt or not prompt.strip():
            raise HTTPException(
                status_code=400,
                detail={"error_code": "PROMPT_REQUIRED", "message": "Prompt cannot be empty"}
            )

        prompt_id = f"prm_{int(time.time()*1000)}"
        task_id = f"task_{int(time.time()*1000)}"
        entry = {
            "prompt_id": prompt_id,
            "task_id": task_id,
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "prompt": prompt.strip(),
            "target_node_id": target_node_id,
            "context_parameters": context_parameters or {},
            "status": "SUBMITTED",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.PROMPTS_DB[prompt_id] = entry
        if self.prompt_repo.pool:
            self._execute_async(self.prompt_repo.save_prompt(entry))
        return entry

    def stage_diff_preview(
        self,
        workspace_id: str,
        tenant_id: str,
        task_id: str,
        files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        ws = self.get_workspace_state(workspace_id, tenant_id)
        if ws["metadata"].get("state") == "LOCKED_READ_ONLY":
            raise HTTPException(
                status_code=403,
                detail={"error_code": "WORKSPACE_LOCKED_READ_ONLY", "message": "Workspace is locked in read-only mode"}
            )

        diff_id = f"diff_{int(time.time()*1000)}"

        # Canonical JCS-like SHA-256 computation over sorted file paths and contents
        canonical_content = json.dumps(
            [{"file_path": f.get("file_path"), "staged_snippet": f.get("staged_snippet")} for f in sorted(files, key=lambda x: x.get("file_path", ""))],
            sort_keys=True
        )
        staged_hash = hashlib.sha256(canonical_content.encode('utf-8')).hexdigest()
        preview_hash = hashlib.sha256(f"preview_{staged_hash}".encode('utf-8')).hexdigest()

        diff_entry = {
            "diff_id": diff_id,
            "task_id": task_id,
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "status": "STAGED",
            "staged_diff_hash": staged_hash,
            "preview_hash": preview_hash,
            "files": files,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.DIFFS_DB[diff_id] = diff_entry
        if self.diff_repo.pool:
            self._execute_async(self.diff_repo.save_diff(diff_entry))
        return diff_entry

    def create_approval_card(
        self,
        workspace_id: str,
        tenant_id: str,
        user_id: str,
        role: Optional[str],
        staged_diff_hash: str,
        summary: str,
        expires_in_minutes: int = 15
    ) -> Dict[str, Any]:
        ws = self.get_workspace_state(workspace_id, tenant_id)
        if ws["metadata"].get("state") == "LOCKED_READ_ONLY":
            raise HTTPException(
                status_code=403,
                detail={"error_code": "WORKSPACE_LOCKED_READ_ONLY", "message": "Workspace is locked in read-only mode"}
            )

        if role == "viewer":
            raise HTTPException(
                status_code=403,
                detail={"error_code": "ROLE_NOT_AUTHORIZED", "message": "Viewers cannot create or approve mutation cards"}
            )

        approval_id = f"appr_{int(time.time()*1000)}"
        sig_data = f"{workspace_id}:{tenant_id}:{staged_diff_hash}:{user_id}:{time.time()}"
        approval_signature = hashlib.sha256(sig_data.encode('utf-8')).hexdigest()
        expires_at = int(time.time()) + (expires_in_minutes * 60)

        card = {
            "approval_id": approval_id,
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "staged_diff_hash": staged_diff_hash,
            "summary": summary,
            "status": "PENDING",
            "approval_signature": approval_signature,
            "created_by": user_id,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.APPROVALS_DB[approval_id] = card
        if self.approval_repo.pool:
            self._execute_async(self.approval_repo.save_approval(card))
        return card

    def process_approval_action(
        self,
        workspace_id: str,
        tenant_id: str,
        approval_id: str,
        action: str,
        user_id: str,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        card = self.APPROVALS_DB.get(approval_id)
        if not card or card["workspace_id"] != workspace_id or card["tenant_id"] != tenant_id:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "APPROVAL_NOT_FOUND", "message": "Approval card not found"}
            )

        if role == "viewer":
            raise HTTPException(
                status_code=403,
                detail={"error_code": "ROLE_NOT_AUTHORIZED", "message": "Viewers cannot approve mutation cards"}
            )

        if int(time.time()) > card["expires_at"]:
            card["status"] = "EXPIRED"
            raise HTTPException(
                status_code=400,
                detail={"error_code": "APPROVAL_EXPIRED", "message": "Approval card has expired"}
            )

        if action.upper() == "APPROVE":
            card["status"] = "APPROVED"
            card["approved_by"] = user_id
            card["approved_at"] = datetime.now(timezone.utc).isoformat()
        elif action.upper() == "REJECT":
            card["status"] = "REJECTED"
            card["rejected_by"] = user_id
            card["rejected_at"] = datetime.now(timezone.utc).isoformat()
        else:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "INVALID_ACTION", "message": f"Unknown approval action: {action}"}
            )

        if self.approval_repo.pool:
            self._execute_async(self.approval_repo.save_approval(card))

        return card

    def create_snapshot(
        self,
        workspace_id: str,
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        ws = self.get_workspace_state(workspace_id, tenant_id)
        snapshot_id = f"snap_{int(time.time()*1000)}"
        canonical_state = json.dumps({"nodes": ws.get("nodes", []), "edges": ws.get("edges", []), "version": ws["metadata"]["version"]}, sort_keys=True)
        pre_hash = hashlib.sha256(canonical_state.encode('utf-8')).hexdigest()

        snapshot = {
            "snapshot_id": snapshot_id,
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "pre_hash": pre_hash,
            "nodes_state": list(ws.get("nodes", [])),
            "edges_state": list(ws.get("edges", [])),
            "version": ws["metadata"]["version"],
            "created_by": user_id or "system",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.SNAPSHOTS_DB[snapshot_id] = snapshot
        if self.snapshot_repo.pool:
            self._execute_async(self.snapshot_repo.save_snapshot(snapshot))
        return snapshot

    def commit_workspace_changes(
        self,
        workspace_id: str,
        tenant_id: str,
        user_id: str,
        expected_version: int,
        idempotency_key: str,
        diff_id: Optional[str] = None,
        modified_files: Optional[List[Dict[str, Any]]] = None,
        approval_id: Optional[str] = None,
        approval_signature: Optional[str] = None
    ) -> Dict[str, Any]:
        ws = self.get_workspace_state(workspace_id, tenant_id)
        if ws["metadata"].get("state") == "LOCKED_READ_ONLY":
            raise HTTPException(
                status_code=403,
                detail={"error_code": "WORKSPACE_LOCKED_READ_ONLY", "message": "Workspace is locked in read-only mode"}
            )

        # Idempotency check
        if idempotency_key in self.IDEMPOTENCY_CACHE:
            return self.IDEMPOTENCY_CACHE[idempotency_key]

        # Multi-section mutation boundary rule: only 1 section file allowed per mutation batch
        if modified_files and len(modified_files) > 1:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "MULTI_SECTION_MUTATION_DENIED", "message": "Mutations are restricted to a single section per transaction"}
            )

        # OCC Version check
        current_version = ws["metadata"]["version"]
        if expected_version != current_version:
            raise HTTPException(
                status_code=409,
                detail={
                    "error_code": "VERSION_MISMATCH",
                    "current_version": current_version,
                    "expected_version": expected_version,
                    "message": f"Conflict: Expected version {expected_version} but workspace is at version {current_version}"
                }
            )

        # Mutate version
        new_version = current_version + 1
        ws["metadata"]["version"] = new_version
        commit_id = f"commit_{int(time.time()*1000)}"

        response = {
            "commit_id": commit_id,
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "status": "COMMITTED",
            "new_version": new_version,
            "diff_id": diff_id,
            "idempotency_key": idempotency_key,
            "committed_at": datetime.now(timezone.utc).isoformat()
        }
        self.IDEMPOTENCY_CACHE[idempotency_key] = response
        self.COMMITS_DB[commit_id] = response

        if self.commit_repo.pool:
            self._execute_async(self.commit_repo.save_commit(response))
            self._execute_async(self.commit_repo.save_idempotency(idempotency_key, workspace_id, tenant_id, response))
            self._execute_async(self.workspace_repo.update_workspace_version(workspace_id, new_version))

        return response

    def rollback_workspace(
        self,
        workspace_id: str,
        tenant_id: str,
        user_id: str,
        snapshot_id: str,
        reason: Optional[str] = "User initiated 1-click rollback"
    ) -> Dict[str, Any]:
        ws = self.get_workspace_state(workspace_id, tenant_id)
        snap = self.SNAPSHOTS_DB.get(snapshot_id)
        if not snap or snap["workspace_id"] != workspace_id or snap["tenant_id"] != tenant_id:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "SNAPSHOT_NOT_FOUND", "message": "Snapshot not found"}
            )

        # Restore state
        ws["nodes"] = list(snap["nodes_state"])
        ws["edges"] = list(snap["edges_state"])
        ws["metadata"]["version"] = snap["version"]

        # Re-verify restored hash
        canonical_state = json.dumps({"nodes": ws["nodes"], "edges": ws["edges"], "version": ws["metadata"]["version"]}, sort_keys=True)
        restored_hash = hashlib.sha256(canonical_state.encode('utf-8')).hexdigest()

        if restored_hash != snap["pre_hash"]:
            raise HTTPException(
                status_code=500,
                detail={"error_code": "ROLLBACK_FAILED", "message": "Post-rollback hash mismatch"}
            )

        rollback_id = f"rb_{int(time.time()*1000)}"
        now = datetime.now(timezone.utc).isoformat()

        audit_entry = {
            "event_id": f"evt_{int(time.time()*1000)}",
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "actor": user_id,
            "action": "ROLLBACK_EXECUTED",
            "details": {"snapshot_id": snapshot_id, "restored_hash": restored_hash, "reason": reason},
            "timestamp": now
        }
        self.AUDIT_TRAIL.append(audit_entry)

        if self.workspace_repo.pool:
            self._execute_async(self.workspace_repo.restore_workspace_state(
                workspace_id, ws["nodes"], ws["edges"], ws["metadata"]["version"]
            ))
            self._execute_async(self.audit_repo.save_event(audit_entry))

        return {
            "rollback_id": rollback_id,
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "status": "RESTORED",
            "restored_version": ws["metadata"]["version"],
            "restored_hash": restored_hash,
            "snapshot_id": snapshot_id,
            "timestamp": now
        }

    def trigger_kill_switch(
        self,
        workspace_id: str,
        tenant_id: str,
        actor: Optional[str] = None
    ) -> Dict[str, Any]:
        ws = self.get_workspace_state(workspace_id, tenant_id)
        ws["metadata"]["state"] = "LOCKED_READ_ONLY"
        cancelled = len(self.APPROVALS_DB)
        self.APPROVALS_DB.clear()
        now = datetime.now(timezone.utc).isoformat()

        audit_entry = {
            "event_id": f"evt_{int(time.time()*1000)}",
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "actor": actor or "user",
            "action": "KILL_SWITCH_TRIGGERED",
            "details": {"reason": "Emergency kill-switch triggered"},
            "timestamp": now
        }
        self.AUDIT_TRAIL.append(audit_entry)

        if self.workspace_repo.pool:
            self._execute_async(self.workspace_repo.set_workspace_state(workspace_id, "LOCKED_READ_ONLY"))
            self._execute_async(self.approval_repo.clear_pending_approvals(workspace_id, tenant_id))
            self._execute_async(self.audit_repo.save_event(audit_entry))

        return {
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "status": "LOCKED_READ_ONLY",
            "cancelled_approvals_count": cancelled,
            "timestamp": now
        }

    def get_audit_trail(self, workspace_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        self.get_workspace_state(workspace_id, tenant_id)
        return [e for e in self.AUDIT_TRAIL if e["workspace_id"] == workspace_id and e["tenant_id"] == tenant_id]


workspace_service = WorkspaceService()
