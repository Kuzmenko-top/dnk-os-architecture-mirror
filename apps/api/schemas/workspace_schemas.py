# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_schemas_workspace_schemas"
# purpose: "Pydantic data schemas for DNK OS User Workspace representation, state, prompts, diffs, approvals, snapshots, commit, rollback, and kill-switch"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class WorkspaceMetadata(BaseModel):
    version: int = 1
    state: str = "ACTIVE"
    last_active: Optional[str] = None


class WorkspaceNode(BaseModel):
    id: str
    type: str
    label: str
    file_path: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class WorkspaceEdge(BaseModel):
    source: str
    target: str
    type: Optional[str] = "layout_flow"


class WorkspaceStateResponse(BaseModel):
    workspace_id: str
    tenant_id: str
    name: str
    metadata: WorkspaceMetadata
    nodes: List[WorkspaceNode] = []
    edges: List[WorkspaceEdge] = []


class PromptDockRequest(BaseModel):
    prompt: str
    target_node_id: Optional[str] = None
    context_parameters: Optional[Dict[str, Any]] = None


class PromptDockResponse(BaseModel):
    prompt_id: str
    task_id: str
    workspace_id: str
    tenant_id: str
    status: str
    created_at: str


class StagedDiffPreviewResponse(BaseModel):
    diff_id: str
    task_id: str
    workspace_id: str
    tenant_id: str
    status: str
    staged_diff_hash: str
    preview_hash: str
    files: List[Dict[str, Any]] = []
    created_at: str


class ApprovalCardRequest(BaseModel):
    staged_diff_hash: str
    summary: str
    expires_in_minutes: int = 15


class ApprovalCardResponse(BaseModel):
    approval_id: str
    workspace_id: str
    tenant_id: str
    staged_diff_hash: str
    summary: str
    status: str
    approval_signature: str
    created_by: str
    expires_at: int
    created_at: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[str] = None


class ApprovalActionRequest(BaseModel):
    action: str  # APPROVE | REJECT


class SnapshotResponse(BaseModel):
    snapshot_id: str
    workspace_id: str
    tenant_id: str
    pre_hash: str
    version: int
    nodes_state: List[Dict[str, Any]] = []
    edges_state: List[Dict[str, Any]] = []
    created_by: str
    created_at: str


class CommitRequest(BaseModel):
    expected_version: int
    idempotency_key: str
    diff_id: Optional[str] = None
    modified_files: Optional[List[Dict[str, Any]]] = None
    approval_id: Optional[str] = None
    approval_signature: Optional[str] = None


class CommitResponse(BaseModel):
    commit_id: str
    workspace_id: str
    tenant_id: str
    status: str
    new_version: int
    diff_id: Optional[str] = None
    idempotency_key: str
    committed_at: str


class RollbackRequest(BaseModel):
    snapshot_id: str
    reason: Optional[str] = "User initiated 1-click rollback"


class RollbackResponse(BaseModel):
    rollback_id: str
    workspace_id: str
    tenant_id: str
    status: str
    restored_version: int
    restored_hash: str
    snapshot_id: str
    timestamp: str


class KillSwitchResponse(BaseModel):
    workspace_id: str
    tenant_id: str
    status: str
    cancelled_approvals_count: int
    timestamp: str


class AuditEventEntry(BaseModel):
    event_id: str
    workspace_id: str
    tenant_id: str
    actor: str
    action: str
    details: Dict[str, Any]
    timestamp: str


class ErrorDetail(BaseModel):
    error_code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail
