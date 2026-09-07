# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_workspace"
# purpose: "FastAPI Router for DNK OS User Workspace (Phase 1 Read-Only, Phase 2 Staged Preview, Phase 3 Approval/Snapshot/Commit/Rollback/Kill-Switch)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, WebSocket, WebSocketDisconnect

from apps.api.middleware.tenant_authorization import require_tenant_and_workspace
from apps.api.schemas.workspace_schemas import (
    WorkspaceStateResponse,
    PromptDockRequest,
    PromptDockResponse,
    StagedDiffPreviewResponse,
    ApprovalCardRequest,
    ApprovalCardResponse,
    ApprovalActionRequest,
    SnapshotResponse,
    CommitRequest,
    CommitResponse,
    RollbackRequest,
    RollbackResponse,
    KillSwitchResponse,
    AuditEventEntry,
    ErrorResponse
)
from apps.api.services.workspace_service import workspace_service
from apps.api.services.auth_service import auth_service

router = APIRouter(prefix="/api/v1/workspaces", tags=["User Workspace"])


@router.get("/{workspace_id}", response_model=WorkspaceStateResponse)
@router.get("/{workspace_id}/state", response_model=WorkspaceStateResponse)
def get_workspace_state(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return workspace_service.get_workspace_state(workspace_id=workspace_id, tenant_id=auth_info["tenant_id"])


@router.post("/{workspace_id}/prompts", response_model=PromptDockResponse)
def submit_prompt(
    workspace_id: str,
    body: PromptDockRequest,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return workspace_service.submit_prompt(
        workspace_id=workspace_id,
        tenant_id=auth_info["tenant_id"],
        user_id=auth_info["user_id"],
        prompt=body.prompt,
        target_node_id=body.target_node_id,
        context_parameters=body.context_parameters
    )


@router.post("/{workspace_id}/diffs/stage", response_model=StagedDiffPreviewResponse)
def stage_diff_preview(
    workspace_id: str,
    task_id: str = Query(..., description="Task ID associated with diff"),
    files: List[Dict[str, Any]] = Body(..., description="List of file modifications"),
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return workspace_service.stage_diff_preview(
        workspace_id=workspace_id,
        tenant_id=auth_info["tenant_id"],
        task_id=task_id,
        files=files
    )


@router.post("/{workspace_id}/approvals/create", response_model=ApprovalCardResponse)
def create_approval_card(
    workspace_id: str,
    body: ApprovalCardRequest,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return workspace_service.create_approval_card(
        workspace_id=workspace_id,
        tenant_id=auth_info["tenant_id"],
        user_id=auth_info["user_id"],
        role=auth_info.get("role"),
        staged_diff_hash=body.staged_diff_hash,
        summary=body.summary,
        expires_in_minutes=body.expires_in_minutes
    )


@router.post("/{workspace_id}/approvals/{approval_id}/action", response_model=ApprovalCardResponse)
def process_approval_action(
    workspace_id: str,
    approval_id: str,
    body: ApprovalActionRequest,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return workspace_service.process_approval_action(
        workspace_id=workspace_id,
        tenant_id=auth_info["tenant_id"],
        approval_id=approval_id,
        action=body.action,
        user_id=auth_info["user_id"],
        role=auth_info.get("role")
    )


@router.post("/{workspace_id}/snapshots", response_model=SnapshotResponse)
def create_snapshot(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return workspace_service.create_snapshot(
        workspace_id=workspace_id,
        tenant_id=auth_info["tenant_id"],
        user_id=auth_info["user_id"]
    )


@router.post("/{workspace_id}/commit", response_model=CommitResponse)
def commit_workspace_changes(
    workspace_id: str,
    body: CommitRequest,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return workspace_service.commit_workspace_changes(
        workspace_id=workspace_id,
        tenant_id=auth_info["tenant_id"],
        user_id=auth_info["user_id"],
        diff_id=body.diff_id,
        expected_version=body.expected_version,
        idempotency_key=body.idempotency_key,
        modified_files=body.modified_files,
        approval_id=body.approval_id,
        approval_signature=body.approval_signature
    )


@router.post("/{workspace_id}/rollback", response_model=RollbackResponse)
def rollback_workspace(
    workspace_id: str,
    body: RollbackRequest,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return workspace_service.rollback_workspace(
        workspace_id=workspace_id,
        tenant_id=auth_info["tenant_id"],
        user_id=auth_info["user_id"],
        snapshot_id=body.snapshot_id,
        reason=body.reason
    )


@router.post("/{workspace_id}/kill-switch", response_model=KillSwitchResponse)
def trigger_kill_switch(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return workspace_service.trigger_kill_switch(
        workspace_id=workspace_id,
        tenant_id=auth_info["tenant_id"],
        actor=auth_info["user_id"]
    )


@router.get("/{workspace_id}/audit-trail", response_model=List[AuditEventEntry])
def get_audit_trail(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return workspace_service.get_audit_trail(
        workspace_id=workspace_id,
        tenant_id=auth_info["tenant_id"]
    )


@router.post("/{workspace_id}/mutate")
def mutate_workspace_legacy(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    raise HTTPException(
        status_code=403,
        detail={"error_code": "MUTATION_GATED_IN_PHASE_2", "message": "Direct unapproved mutations are blocked. Use Staged Preview + Approval + Commit flow"}
    )


@router.post("/{workspace_id}/shopify/sync", operation_id="shopify_sync_blocked_path")
@router.post("/{workspace_id}/shopify-sync", operation_id="shopify_sync_dash_blocked_path")
def shopify_sync_blocked(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    raise HTTPException(
        status_code=403,
        detail={"error_code": "SHOPIFY_WRITE_BLOCKED", "message": "Direct Shopify writes are gated and require explicit Phase 3 approval/commit"}
    )


from apps.api.services.workspace_collaboration_hub import workspace_collaboration_hub

async def handle_workspace_websocket(websocket: WebSocket, workspace_id: str):
    token_str = websocket.query_params.get("token")
    if not token_str:
        await websocket.close(code=4401)
        return

    try:
        payload = auth_service.verify_access_token(token_str)
        user_id = payload.get("sub")
        jwt_tenant_id = payload.get("tenant_id")
        roles = payload.get("roles", ["developer"])
        role = roles[0] if isinstance(roles, list) and roles else "developer"
        if not user_id or not jwt_tenant_id:
            await websocket.close(code=4401)
            return
    except Exception:
        await websocket.close(code=4401)
        return

    if not auth_service.check_user_workspace_membership(user_id, jwt_tenant_id, workspace_id):
        await websocket.close(code=4403)
        return

    await websocket.accept()
    await workspace_collaboration_hub.connect(
        workspace_id=workspace_id,
        user_id=user_id,
        websocket=websocket,
        role=role
    )
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            await workspace_collaboration_hub.handle_message(
                websocket=websocket,
                workspace_id=workspace_id,
                tenant_id=jwt_tenant_id,
                user_id=user_id,
                role=role,
                raw_message=msg
            )
    except WebSocketDisconnect:
        await workspace_collaboration_hub.disconnect(workspace_id=workspace_id, user_id=user_id, websocket=websocket)
    except Exception as e:
        await workspace_collaboration_hub.disconnect(workspace_id=workspace_id, user_id=user_id, websocket=websocket)
