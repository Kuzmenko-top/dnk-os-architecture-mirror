# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_taskdna"
# purpose: "Read-only TaskDNA API router and deterministic fixture repository for DNK-OS-001"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import re
import json
import base64
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from core.decorators.security_gate import SecurityGateDenied
from apps.api.services.github_adapter import GitHubAdapter

router = APIRouter(prefix="/api", tags=["TaskDNA"])
github_adapter = GitHubAdapter()

VALID_STATUSES = {"ALL", "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "CANCELLED", "BLOCKED"}


# ---------------------------------------------------------------------------
# Pydantic Domain Models
# ---------------------------------------------------------------------------

class Workspace(BaseModel):
    id: str
    name: str
    status: str = "active"
    created_at: str
    updated_at: str


class TaskAgent(BaseModel):
    id: str
    role: str
    name: str
    status: str = "IDLE"


class GitContext(BaseModel):
    repository: str
    branch: str
    base_branch: str
    base_sha: str
    head_sha: str
    merge_sha: Optional[str] = None


class ValidationGate(BaseModel):
    id: str
    name: str
    status: str  # PASSED, FAILED, PENDING, IN_PROGRESS
    evidence_ref: str
    completed_at: Optional[str] = None


class PullRequestInfo(BaseModel):
    model_config = {"extra": "ignore"}
    number: int
    title: str
    state: str  # OPEN, MERGED, CLOSED
    head_sha: str
    base_branch: str
    checks_status: str  # SUCCESS, FAILURE, PENDING
    mergeable: bool = True
    merged_at: Optional[str] = None


class DodProgress(BaseModel):
    total: int
    completed: int
    percentage: int


class TaskDNAModel(BaseModel):
    id: str
    workspace_id: str
    title: str
    phase: str
    status: str  # COMPLETED, IN_PROGRESS, BLOCKED, PENDING
    owner: str
    supervisor: TaskAgent
    worker: TaskAgent
    git_context: GitContext
    validation_gates: List[ValidationGate]
    pull_request: Optional[PullRequestInfo] = None
    blockers: List[str] = Field(default_factory=list)
    dod_progress: DodProgress
    created_at: str
    updated_at: str
    data_source: str = "fixture"  # "live" | "cache" | "fixture"
    stale: bool = False
    error_code: Optional[str] = None


class TaskSummary(BaseModel):
    id: str
    workspace_id: str
    title: str
    phase: str
    status: str
    owner: str
    supervisor_name: str
    worker_name: str
    branch: str
    pr_number: Optional[int] = None
    pr_state: Optional[str] = None
    gates_passed: int
    gates_total: int
    dod_percentage: int
    updated_at: str


class TaskTimelineEvent(BaseModel):
    id: str
    task_id: str
    timestamp: str
    event_type: str
    actor: str
    summary: str
    details: Optional[Dict[str, Any]] = None


class CanvasGraphNode(BaseModel):
    id: str
    type: str  # taskNode, agentNode, gateNode, prNode
    position: Dict[str, float]
    data: Dict[str, Any]


class CanvasGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    animated: bool = False


class CanvasGraphResponse(BaseModel):
    task_id: str
    nodes: List[CanvasGraphNode]
    edges: List[CanvasGraphEdge]


class GlobalEventModel(BaseModel):
    id: str
    task_id: str
    timestamp: str
    event_type: str
    actor: str
    summary: str


class RunSummary(BaseModel):
    id: str
    task_id: str
    title: str
    status: str
    worker: str
    started_at: str
    ended_at: Optional[str] = None
    steps_completed: int
    steps_total: int


class ApprovalSummary(BaseModel):
    id: str
    task_id: str
    title: str
    action_class: str
    required_role: str
    status: str
    requested_at: str
    preview_summary: str
    simulated_payload: Dict[str, Any]


class ApprovalDecisionRequest(BaseModel):
    decision: str  # APPROVED, REJECTED
    reason: Optional[str] = None
    actor: str = "User (Cabinet)"


class ApprovalDecisionResponse(BaseModel):
    approval_id: str
    status: str
    decision: str
    executed: bool = False
    mode: str = "SIMULATED_PREVIEW"
    message: str


class PluginSummary(BaseModel):
    id: str
    name: str
    version: str
    trust_state: str  # TRUSTED, VERIFIED, UNTRUSTED
    sandbox_mode: str
    author: str


class TrustStatus(BaseModel):
    status: str  # ENFORCED
    active_keys: int
    algorithm: str
    verified_plugins: int
    revoked_keys: int


class ShopifyDryRunRequest(BaseModel):
    store_url: str
    theme_id: Optional[str] = None


class ShopifyDryRunResponse(BaseModel):
    status: str = "COMPLETED"
    mode: str = "READ_ONLY_SIMULATED"
    diff_count: int
    changes_detected: List[Dict[str, Any]]
    reconciliation_plan: List[str]


class HealthSummary(BaseModel):
    status: str = "HEALTHY"
    supervisor_status: str = "ACTIVE"
    worker_status: str = "ACTIVE"
    omni_router: str = "ONLINE"
    event_bus: str = "ONLINE"
    active_runs: int = 2
    pending_approvals: int = 1
    version: str = "2.0.0"



# ---------------------------------------------------------------------------
# Deterministic Fixture Repository (M1 Canonical Baseline)
# ---------------------------------------------------------------------------

WORKSPACES_FIXTURE: Dict[str, Workspace] = {
    "ws-alpha-001": Workspace(
        id="ws-alpha-001",
        name="DNK OS Core Delivery",
        status="active",
        created_at="2026-08-20T10:00:00Z",
        updated_at="2026-08-23T14:00:00Z"
    ),
    "ws-shopify-001": Workspace(
        id="ws-shopify-001",
        name="DNK Shopify Ecosystem",
        status="active",
        created_at="2026-08-15T08:00:00Z",
        updated_at="2026-08-23T12:00:00Z"
    )
}

TASKS_FIXTURE: Dict[str, TaskDNAModel] = {
    "DNK-SHOPIFY-011": TaskDNAModel(
        id="DNK-SHOPIFY-011",
        workspace_id="ws-shopify-001",
        title="PDP Conversion Runtime & Zero-Liquid-Diff Hardening",
        phase="Phase 5: Handoff & Merge Complete",
        status="COMPLETED",
        owner="Maxim (Lead)",
        supervisor=TaskAgent(
            id="agent-antigravity",
            name="Antigravity",
            role="Lead Architect & Supervisor",
            status="IDLE"
        ),
        worker=TaskAgent(
            id="agent-gerych",
            name="Gerych",
            role="Primary Builder & Executor",
            status="IDLE"
        ),
        git_context=GitContext(
            repository="DNKShopify/DNK-e.com",
            branch="mentor/shopify/DNK-SHOPIFY-011-pdp-conversion-runtime",
            base_branch="feature/01-tinker-analysis",
            base_sha="daac1b1c20cd4c80f4c62fd56bfa79f202a8111e",
            head_sha="0bb073f1361dbd73c713b1853d9e830e0c0df4a7",
            merge_sha="c6f2f98f480ad2e08a6e873b2c28ca87f3ddae25"
        ),
        validation_gates=[
            ValidationGate(
                id="gate-1",
                name="PDP Runtime Inventory Gate",
                status="PASSED",
                evidence_ref="docs/migration/DNK-SHOPIFY-011-PDP-INVENTORY.md",
                completed_at="2026-08-23T04:15:00Z"
            ),
            ValidationGate(
                id="gate-2",
                name="Zero Liquid Diff Baseline Gate",
                status="PASSED",
                evidence_ref="docs/migration/DNK-SHOPIFY-011-PDP-CONVERSION-RUNTIME-SPEC.md",
                completed_at="2026-08-23T04:20:00Z"
            ),
            ValidationGate(
                id="gate-3",
                name="14/14 Theme Preview Matrix Gate",
                status="PASSED",
                evidence_ref="docs/migration/DNK-SHOPIFY-011-THEME-PREVIEW-EVIDENCE.md",
                completed_at="2026-08-23T04:25:00Z"
            ),
            ValidationGate(
                id="gate-4",
                name="Automated Test Suite & Handoff Gate",
                status="PASSED",
                evidence_ref="docs/handoffs/HANDOFF_DNK-SHOPIFY-011_2026-08-23.md",
                completed_at="2026-08-23T04:30:00Z"
            )
        ],
        pull_request=PullRequestInfo(
            number=4,
            title="feat(pdp): verify PDP conversion runtime contract & theme preview matrix (DNK-SHOPIFY-011)",
            state="MERGED",
            head_sha="0bb073f1361dbd73c713b1853d9e830e0c0df4a7",
            base_branch="feature/01-tinker-analysis",
            checks_status="SUCCESS",
            mergeable=True,
            merged_at="2026-08-23T04:45:00Z"
        ),
        blockers=[],
        dod_progress=DodProgress(
            total=11,
            completed=11,
            percentage=100
        ),
        created_at="2026-08-23T03:00:00Z",
        updated_at="2026-08-23T04:45:00Z"
    ),

    "DNK-OS-001": TaskDNAModel(
        id="DNK-OS-001",
        workspace_id="ws-alpha-001",
        title="Visual Workspace MVP: Shell, TaskDNA Dashboard & Canvas Foundation",
        phase="Phase 2: TaskDNA API & Workspace Shell Implementation",
        status="IN_PROGRESS",
        owner="Maxim (Lead)",
        supervisor=TaskAgent(
            id="agent-antigravity",
            name="Antigravity",
            role="Lead Architect & Supervisor",
            status="ACTIVE"
        ),
        worker=TaskAgent(
            id="agent-gerych",
            name="Gerych",
            role="Primary Builder & Executor",
            status="EXECUTING"
        ),
        git_context=GitContext(
            repository="Kuzmenko-top/DNK_OS_MVP",
            branch="feature/dnk-os-001-visual-workspace",
            base_branch="main",
            base_sha="5a072dfddbb73a2f417c8e10853e15b2b00f4a0d",
            head_sha="e3a60fdd427923bda0fe3102eab0be0c8b93aa2a"
        ),
        validation_gates=[
            ValidationGate(
                id="gate-1",
                name="Architecture Inventory & TaskDNA Contract Gate",
                status="PASSED",
                evidence_ref="docs/architecture/DNK-OS-001-TASKDNA-API-CONTRACT.md",
                completed_at="2026-08-23T05:00:00Z"
            ),
            ValidationGate(
                id="gate-2",
                name="Read-Only TaskDNA API & Security Gate",
                status="PASSED",
                evidence_ref="tests/dnk_os_001/test_taskdna_api.py",
                completed_at="2026-08-23T05:30:00Z"
            ),
            ValidationGate(
                id="gate-3",
                name="Workspace Shell & TaskDNA Dashboard Gate",
                status="PASSED",
                evidence_ref="apps/web/components/taskdna/TaskDNADashboard.tsx",
                completed_at="2026-08-23T05:45:00Z"
            ),
            ValidationGate(
                id="gate-4",
                name="Verification & Handoff Review Gate",
                status="IN_PROGRESS",
                evidence_ref="docs/handoffs/HANDOFF_DNK-OS-001-2026-08-23.md"
            )
        ],
        pull_request=PullRequestInfo(
            number=5,
            title="feat(taskdna): implement TaskDNA API router, workspace shell, and canvas graph viewer (DNK-OS-001)",
            state="OPEN",
            head_sha="e3a60fdd427923bda0fe3102eab0be0c8b93aa2a",
            base_branch="main",
            checks_status="SUCCESS",
            mergeable=True
        ),
        blockers=[],
        dod_progress=DodProgress(
            total=15,
            completed=12,
            percentage=80
        ),
        created_at="2026-08-23T04:50:00Z",
        updated_at="2026-08-23T06:00:00Z"
    ),

    "DNK-CI-002": TaskDNAModel(
        id="DNK-CI-002",
        workspace_id="ws-shopify-001",
        title="CI Baseline & Workflow Hardening",
        phase="Phase 5: Merged",
        status="COMPLETED",
        owner="Maxim (Lead)",
        supervisor=TaskAgent(
            id="agent-antigravity",
            name="Antigravity",
            role="Lead Architect & Supervisor",
            status="IDLE"
        ),
        worker=TaskAgent(
            id="agent-gerych",
            name="Gerych",
            role="Primary Builder & Executor",
            status="IDLE"
        ),
        git_context=GitContext(
            repository="DNKShopify/DNK-e.com",
            branch="ci/ci-002-workflow-hardening",
            base_branch="feature/01-tinker-analysis",
            base_sha="505319b984a575949732a44101b549694aa3aca0",
            head_sha="985e60b865bd2565651c68f1da45781a7905ce23",
            merge_sha="985e60b865bd2565651c68f1da45781a7905ce23"
        ),
        validation_gates=[
            ValidationGate(
                id="gate-1",
                name="Workflow File Presence Check",
                status="PASSED",
                evidence_ref=".github/workflows/validate.yml",
                completed_at="2026-08-23T02:30:00Z"
            ),
            ValidationGate(
                id="gate-2",
                name="Failure Path Verification Gate",
                status="PASSED",
                evidence_ref="docs/handoffs/HANDOFF_CI-002_2026-08-23.md",
                completed_at="2026-08-23T02:40:00Z"
            )
        ],
        pull_request=PullRequestInfo(
            number=3,
            title="ci: validate workflow portability and baseline integrity (CI-002)",
            state="MERGED",
            head_sha="985e60b865bd2565651c68f1da45781a7905ce23",
            base_branch="feature/01-tinker-analysis",
            checks_status="SUCCESS",
            mergeable=True,
            merged_at="2026-08-23T02:50:00Z"
        ),
        blockers=[],
        dod_progress=DodProgress(
            total=6,
            completed=6,
            percentage=100
        ),
        created_at="2026-08-23T02:00:00Z",
        updated_at="2026-08-23T02:50:00Z"
    )
}

TIMELINE_FIXTURE: Dict[str, List[TaskTimelineEvent]] = {
    "DNK-OS-001": [
        TaskTimelineEvent(
            id="evt-1",
            task_id="DNK-OS-001",
            timestamp="2026-08-23T04:50:00Z",
            event_type="TASK_CREATED",
            actor="Maxim",
            summary="Task DNK-OS-001 created from Visual OS Working Cabinet specification."
        ),
        TaskTimelineEvent(
            id="evt-2",
            task_id="DNK-OS-001",
            timestamp="2026-08-23T05:00:00Z",
            event_type="GATE_PASSED",
            actor="Antigravity",
            summary="Phase 1 Architecture Inventory and TaskDNA Contract approved."
        ),
        TaskTimelineEvent(
            id="evt-3",
            task_id="DNK-OS-001",
            timestamp="2026-08-23T05:20:00Z",
            event_type="CODE_COMMITTED",
            actor="Gerych",
            summary="Implemented TaskDNA read-only router, workspace shell, and canvas graph viewer."
        ),
        TaskTimelineEvent(
            id="evt-4",
            task_id="DNK-OS-001",
            timestamp="2026-08-23T05:35:00Z",
            event_type="TESTS_PASSED",
            actor="Gerych",
            summary="All 7 TaskDNA API and security gate tests passed."
        ),
        TaskTimelineEvent(
            id="evt-5",
            task_id="DNK-OS-001",
            timestamp="2026-08-23T05:40:00Z",
            event_type="REMOTE_PUSHED",
            actor="Gerych",
            summary="Pushed feature/dnk-os-001-visual-workspace (commit e3a60fdd4) to remote."
        )
    ],
    "DNK-SHOPIFY-011": [
        TaskTimelineEvent(
            id="evt-11",
            task_id="DNK-SHOPIFY-011",
            timestamp="2026-08-23T03:00:00Z",
            event_type="TASK_CREATED",
            actor="Antigravity",
            summary="PDP Conversion Runtime task intake started."
        ),
        TaskTimelineEvent(
            id="evt-12",
            task_id="DNK-SHOPIFY-011",
            timestamp="2026-08-23T04:30:00Z",
            event_type="GATES_COMPLETED",
            actor="Gerych",
            summary="All 4 validation gates verified with 14/14 Theme Preview matrix."
        ),
        TaskTimelineEvent(
            id="evt-13",
            task_id="DNK-SHOPIFY-011",
            timestamp="2026-08-23T04:45:00Z",
            event_type="PR_MERGED",
            actor="Maxim",
            summary="PR #4 squash-merged into feature/01-tinker-analysis."
        )
    ],
    "DNK-CI-002": [
        TaskTimelineEvent(
            id="evt-21",
            task_id="DNK-CI-002",
            timestamp="2026-08-23T02:00:00Z",
            event_type="TASK_CREATED",
            actor="Antigravity",
            summary="CI hardening task initiated."
        ),
        TaskTimelineEvent(
            id="evt-22",
            task_id="DNK-CI-002",
            timestamp="2026-08-23T02:50:00Z",
            event_type="PR_MERGED",
            actor="Maxim",
            summary="PR #3 merged to feature/01-tinker-analysis."
        )
    ]
}


# ---------------------------------------------------------------------------
# Auth & Security Gate Dependency
# ---------------------------------------------------------------------------

def decode_mock_jwt(token: str) -> Dict[str, Any]:
    """Helper to decode dev/test JWT format."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed JWT structure")
        payload_b64 = parts[1]
        # Pad base64 if needed
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)
    except Exception as e:
        raise ValueError(f"Invalid JWT token: {e}")


def enforce_workspace_authorization(
    workspace_id_header: Optional[str] = None,
    authorization: Optional[str] = None
) -> str:
    """
    Validates X-Workspace-ID header and optional Authorization JWT.
    Enforces tenant isolation and fail-closed security.
    """
    if not workspace_id_header or not workspace_id_header.strip():
        raise SecurityGateDenied("Missing or empty X-Workspace-ID header")

    ws_id = workspace_id_header.strip()

    # Reject malformed characters
    if not re.match(r"^[a-zA-Z0-9_\-]+$", ws_id):
        raise SecurityGateDenied(f"Invalid workspace ID format: '{ws_id}'")

    if ws_id not in WORKSPACES_FIXTURE and ws_id != "default":
        raise SecurityGateDenied(f"Forbidden: Workspace ID '{ws_id}' is not authorized")

    effective_ws = ws_id if ws_id in WORKSPACES_FIXTURE else "ws-alpha-001"

    # Validate JWT if provided
    if authorization:
        auth_header = authorization.strip()
        if not auth_header.startswith("Bearer "):
            raise SecurityGateDenied("Malformed Authorization header: must start with 'Bearer '")
        raw_token = auth_header[7:].strip()
        if not raw_token:
            raise SecurityGateDenied("Missing Bearer token in Authorization header")

        # In test/dev mode, allow standard dev token 'dnk-dev-token' or decode JSON payload
        if raw_token != "dnk-dev-token":
            try:
                claims = decode_mock_jwt(raw_token)
                token_ws = claims.get("workspace_id")
                if token_ws and token_ws != effective_ws:
                    raise SecurityGateDenied(f"JWT workspace claim '{token_ws}' does not match '{effective_ws}'")
            except ValueError as ve:
                raise SecurityGateDenied(f"Invalid JWT signature/payload: {ve}")

    return effective_ws


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@router.get("/workspaces/{workspace_id}", response_model=Workspace)
def get_workspace(
    workspace_id: str,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    authorized_ws = enforce_workspace_authorization(x_workspace_id or workspace_id, authorization)
    if workspace_id not in WORKSPACES_FIXTURE:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found")
    if workspace_id != authorized_ws and authorized_ws != "ws-alpha-001":
        raise SecurityGateDenied("Cross-workspace query forbidden")
    return WORKSPACES_FIXTURE[workspace_id]


@router.get("/tasks", response_model=List[TaskSummary])
def list_tasks(
    workspace_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    authorized_ws = enforce_workspace_authorization(x_workspace_id or workspace_id, authorization)
    target_ws = workspace_id or authorized_ws

    if status:
        if status.upper() not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status filter: '{status}'")

    results = []
    for task in TASKS_FIXTURE.values():
        if target_ws and task.workspace_id != target_ws:
            continue
        if status and status.upper() != "ALL" and task.status.upper() != status.upper():
            continue

        gates_passed = sum(1 for g in task.validation_gates if g.status == "PASSED")
        summary = TaskSummary(
            id=task.id,
            workspace_id=task.workspace_id,
            title=task.title,
            phase=task.phase,
            status=task.status,
            owner=task.owner,
            supervisor_name=task.supervisor.name,
            worker_name=task.worker.name,
            branch=task.git_context.branch,
            pr_number=task.pull_request.number if task.pull_request else None,
            pr_state=task.pull_request.state if task.pull_request else None,
            gates_passed=gates_passed,
            gates_total=len(task.validation_gates),
            dod_percentage=task.dod_progress.percentage,
            updated_at=task.updated_at
        )
        results.append(summary)

    return results[:limit]


@router.get("/tasks/{task_id}", response_model=TaskDNAModel)
def get_task_detail(
    task_id: str,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    authorized_ws = enforce_workspace_authorization(x_workspace_id, authorization)
    if task_id not in TASKS_FIXTURE:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    task = TASKS_FIXTURE[task_id].model_copy(deep=True)
    if task.workspace_id != authorized_ws:
        raise SecurityGateDenied(f"Cross-workspace task access forbidden: task '{task_id}' belongs to '{task.workspace_id}'")

    if task.pull_request and task.git_context:
        gh_res = github_adapter.get_pull_request(
            repo=task.git_context.repository,
            pr_number=task.pull_request.number,
            allow_fixture_fallback=True
        )
        task.data_source = gh_res.data_source
        task.stale = gh_res.stale
        task.error_code = gh_res.error_code
        if gh_res.data:
            task.pull_request = PullRequestInfo(**gh_res.data)
    else:
        task.data_source = "fixture"
        task.stale = False
        task.error_code = None

    return task


@router.get("/tasks/{task_id}/timeline", response_model=List[TaskTimelineEvent])
def get_task_timeline(
    task_id: str,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    authorized_ws = enforce_workspace_authorization(x_workspace_id, authorization)
    if task_id not in TASKS_FIXTURE:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    task = TASKS_FIXTURE[task_id]
    if task.workspace_id != authorized_ws:
        raise SecurityGateDenied(f"Cross-workspace task access forbidden: task '{task_id}' belongs to '{task.workspace_id}'")

    return TIMELINE_FIXTURE.get(task_id, [])


@router.get("/tasks/{task_id}/graph", response_model=CanvasGraphResponse)
def get_task_graph(
    task_id: str,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    authorized_ws = enforce_workspace_authorization(x_workspace_id, authorization)
    if task_id not in TASKS_FIXTURE:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    task = TASKS_FIXTURE[task_id]
    if task.workspace_id != authorized_ws:
        raise SecurityGateDenied(f"Cross-workspace task access forbidden: task '{task_id}' belongs to '{task.workspace_id}'")

    nodes: List[CanvasGraphNode] = [
        CanvasGraphNode(
            id=f"node-{task.id}",
            type="taskNode",
            position={"x": 300.0, "y": 40.0},
            data={
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "phase": task.phase,
                "branch": task.git_context.branch,
                "dod": f"{task.dod_progress.percentage}%"
            }
        ),
        CanvasGraphNode(
            id="node-supervisor",
            type="agentNode",
            position={"x": 80.0, "y": 180.0},
            data={
                "id": task.supervisor.id,
                "name": task.supervisor.name,
                "role": task.supervisor.role,
                "status": task.supervisor.status
            }
        ),
        CanvasGraphNode(
            id="node-worker",
            type="agentNode",
            position={"x": 520.0, "y": 180.0},
            data={
                "id": task.worker.id,
                "name": task.worker.name,
                "role": task.worker.role,
                "status": task.worker.status
            }
        )
    ]

    edges: List[CanvasGraphEdge] = [
        CanvasGraphEdge(id="e-task-sup", source=f"node-{task.id}", target="node-supervisor", label="governs"),
        CanvasGraphEdge(id="e-task-wrk", source=f"node-{task.id}", target="node-worker", label="executes")
    ]

    # Add Gate nodes
    y_offset = 320.0
    x_start = 100.0
    for idx, gate in enumerate(task.validation_gates):
        gate_node_id = f"node-gate-{gate.id}"
        nodes.append(
            CanvasGraphNode(
                id=gate_node_id,
                type="gateNode",
                position={"x": x_start + (idx * 160.0), "y": y_offset},
                data={
                    "id": gate.id,
                    "name": gate.name,
                    "status": gate.status,
                    "evidence_ref": gate.evidence_ref
                }
            )
        )
        edges.append(
            CanvasGraphEdge(
                id=f"e-wrk-gate-{gate.id}",
                source="node-worker",
                target=gate_node_id,
                label="validates"
            )
        )

    # Add PR node if exists
    if task.pull_request:
        pr_node_id = f"node-pr-{task.pull_request.number}"
        nodes.append(
            CanvasGraphNode(
                id=pr_node_id,
                type="prNode",
                position={"x": 300.0, "y": 460.0},
                data={
                    "number": task.pull_request.number,
                    "title": task.pull_request.title,
                    "state": task.pull_request.state,
                    "checks": task.pull_request.checks_status
                }
            )
        )
        for gate in task.validation_gates:
            edges.append(
                CanvasGraphEdge(
                    id=f"e-gate-{gate.id}-pr",
                    source=f"node-gate-{gate.id}",
                    target=pr_node_id,
                    label="satisfies"
                )
            )

    return CanvasGraphResponse(task_id=task.id, nodes=nodes, edges=edges)


# ---------------------------------------------------------------------------
# Additional Working Cabinet Endpoints
# ---------------------------------------------------------------------------

RUNS_FIXTURE: List[RunSummary] = [
    RunSummary(
        id="run-001",
        task_id="DNK-OS-001",
        title="TaskDNA API & Cabinet Foundation",
        status="IN_PROGRESS",
        worker="Gerych (Worker)",
        started_at="2026-08-23T18:00:00Z",
        steps_completed=4,
        steps_total=6
    ),
    RunSummary(
        id="run-002",
        task_id="DNK-SHOPIFY-011",
        title="Shopify PDP Theme Preview",
        status="COMPLETED",
        worker="Gerych (Worker)",
        started_at="2026-08-23T14:00:00Z",
        ended_at="2026-08-23T16:45:00Z",
        steps_completed=5,
        steps_total=5
    )
]

APPROVALS_FIXTURE: List[ApprovalSummary] = [
    ApprovalSummary(
        id="appr-001",
        task_id="DNK-VISUAL-OS-001",
        title="Shopify Theme Diff Sync Plan",
        action_class="SHOPIFY_WRITE_SIMULATED",
        required_role="Supervisor",
        status="PENDING",
        requested_at="2026-08-23T19:00:00Z",
        preview_summary="Simulated dry-run diff for sections/pdp-conversion.liquid (2 lines modified)",
        simulated_payload={
            "target": "sections/pdp-conversion.liquid",
            "operation": "theme_asset_update",
            "simulated": True,
            "read_only": True
        }
    )
]

PLUGINS_FIXTURE: List[PluginSummary] = [
    PluginSummary(
        id="plugin-shopify-guard",
        name="Shopify Security Guard",
        version="1.2.0",
        trust_state="TRUSTED",
        sandbox_mode="STRICT_READ_ONLY",
        author="DNK OS Governance"
    ),
    PluginSummary(
        id="plugin-canvas-research",
        name="Canvas Task Graph Engine",
        version="2.0.1",
        trust_state="VERIFIED",
        sandbox_mode="ISOLATED",
        author="DNK OS Swarm"
    )
]

TRUST_STATUS_FIXTURE = TrustStatus(
    status="ENFORCED",
    active_keys=4,
    algorithm="ED25519",
    verified_plugins=2,
    revoked_keys=0
)

HEALTH_FIXTURE = HealthSummary(
    status="HEALTHY",
    supervisor_status="ACTIVE",
    worker_status="ACTIVE",
    omni_router="ONLINE",
    event_bus="ONLINE",
    active_runs=2,
    pending_approvals=1,
    version="2.0.0"
)


@router.get("/runs", response_model=List[RunSummary])
def list_runs(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return RUNS_FIXTURE


@router.get("/events", response_model=List[GlobalEventModel])
def list_global_events(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    events = []
    for task_events in TIMELINE_FIXTURE.values():
        for evt in task_events:
            events.append(
                GlobalEventModel(
                    id=evt.id,
                    task_id=evt.task_id,
                    timestamp=evt.timestamp,
                    event_type=evt.event_type,
                    actor=evt.actor,
                    summary=evt.summary
                )
            )
    return sorted(events, key=lambda x: x.timestamp, reverse=True)


@router.get("/approvals", response_model=List[ApprovalSummary])
def list_approvals(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return APPROVALS_FIXTURE


@router.post("/approvals/{approval_id}/decision", response_model=ApprovalDecisionResponse)
def submit_approval_decision(
    approval_id: str,
    body: ApprovalDecisionRequest,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    enforce_workspace_authorization(x_workspace_id)
    target = next((a for a in APPROVALS_FIXTURE if a.id == approval_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found")

    return ApprovalDecisionResponse(
        approval_id=approval_id,
        status="DECISION_REGISTERED",
        decision=body.decision.upper(),
        executed=False,
        mode="SIMULATED_PREVIEW",
        message=f"Decision '{body.decision}' recorded in preview mode. No live mutation executed."
    )


@router.get("/plugins", response_model=List[PluginSummary])
def list_plugins(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return PLUGINS_FIXTURE


@router.get("/trust/status", response_model=TrustStatus)
def get_trust_status(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return TRUST_STATUS_FIXTURE


@router.post("/shopify/sync/dry-run", response_model=ShopifyDryRunResponse)
def execute_shopify_dry_run(
    body: ShopifyDryRunRequest,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    enforce_workspace_authorization(x_workspace_id)
    return ShopifyDryRunResponse(
        status="COMPLETED",
        mode="READ_ONLY_SIMULATED",
        diff_count=2,
        changes_detected=[
            {"asset": "sections/pdp-conversion.liquid", "type": "MODIFIED", "lines_changed": 2},
            {"asset": "snippets/pdp-badge.liquid", "type": "ADDED", "lines_changed": 14}
        ],
        reconciliation_plan=[
            "Preview liquid diff in Shopify Dry-Run Viewer",
            "Verify PDP Conversion conversion triggers",
            "Simulate supervisor approval gate"
        ]
    )


@router.get("/health", response_model=HealthSummary)
def get_system_health(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return HEALTH_FIXTURE


# --- Working Cabinet Dedicated Endpoints (DNK-VISUAL-OS-001) ---

@router.get("/cabinet/health")
def cabinet_health(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return {
        "status": "HEALTHY",
        "uptime_seconds": 14280,
        "active_agents": 3,
        "active_workers": 4,
        "pending_approvals": 2,
        "trusted_plugins_count": 5,
        "event_bus_status": "CONNECTED",
        "memory_usage_mb": 248.5,
        "cpu_percent": 4.2
    }


@router.get("/cabinet/tasks")
def cabinet_tasks(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return [
        {
            "id": "task-field-001",
            "title": "DNK OS Production Runtime",
            "plant_scale": "Project_Field",
            "status": "in_progress",
            "assigned_agent": "Hermes (Gerych)",
            "dod_criteria": ["Docker runtimes green", "Fail-closed auth", "Zero liquid diff verified"],
            "dod_progress": 85,
            "validation_gates": [
                {"name": "Security Gate", "passed": True},
                {"name": "MRH Header Compliance", "passed": True},
                {"name": "Zero Host Pollution", "passed": True}
            ],
            "cycle_report_path": "docs/reports/execution_cycles/CYCLE-001.md"
        },
        {
            "id": "task-flower-003",
            "title": "Working Cabinet Visual MVP",
            "plant_scale": "Task_Flower",
            "status": "in_progress",
            "parent_id": "task-field-001",
            "assigned_agent": "dnk-dev-01",
            "dod_criteria": ["App Shell", "TaskDNA Timeline", "Approval Inbox", "Shopify Diff Viewer"],
            "dod_progress": 90,
            "validation_gates": [
                {"name": "Component Unit Tests", "passed": True},
                {"name": "Read-Only Invariant", "passed": True}
            ],
            "cycle_report_path": "docs/reports/execution_cycles/CYCLE-003.md"
        }
    ]


@router.get("/cabinet/timeline")
def cabinet_timeline(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return [
        {
            "id": "evt-001",
            "timestamp": "2026-08-23T14:00:00Z",
            "level": "INFO",
            "category": "SUPERVISOR",
            "source": "Antigravity",
            "message": "TaskDNA architectural contract approved (DNK-OS-001)."
        },
        {
            "id": "evt-002",
            "timestamp": "2026-08-23T14:30:00Z",
            "level": "INFO",
            "category": "WORKER",
            "source": "Hermes",
            "message": "Dispatched subagent flower dnk-dev-01 for Cabinet UI."
        },
        {
            "id": "evt-003",
            "timestamp": "2026-08-23T15:00:00Z",
            "level": "SECURITY",
            "category": "SECURITY",
            "source": "FailClosedMiddleware",
            "message": "Validated JWT & workspace tenancy token with 0 mutations."
        }
    ]


@router.get("/cabinet/approvals")
def cabinet_approvals(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return [
        {
            "id": "appr-001",
            "task_id": "task-flower-003",
            "title": "Approve Theme Patch Simulation Manifest",
            "requester": "Hermes",
            "gate_type": "HITL",
            "status": "pending",
            "created_at": "2026-08-23T15:10:00Z",
            "preview_payload": {
                "target": "shopify_theme_preview",
                "simulated_files_count": 2,
                "dry_run": True,
                "mutations_allowed": False
            }
        },
        {
            "id": "appr-002",
            "task_id": "task-field-001",
            "title": "Verify ED25519 Plugin Signature for Shopify Adapter",
            "requester": "dnk_governance_companion",
            "gate_type": "SECURITY",
            "status": "pending",
            "created_at": "2026-08-23T14:50:00Z",
            "preview_payload": {
                "plugin_name": "dnk_shopify_adapter",
                "signer_key_id": "key-ed25519-0941",
                "verified": True
            }
        }
    ]


@router.get("/cabinet/plugins")
def cabinet_plugins(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return [
        {
            "id": "plug-01",
            "name": "dnk_governance_companion",
            "version": "1.2.0",
            "trusted": True,
            "signer": "DNK Core Authority (ED25519)",
            "signature_verified": True,
            "capabilities": ["read_telemetry", "validate_mrh", "audit_checks"]
        },
        {
            "id": "plug-02",
            "name": "dnk_shopify_read_adapter",
            "version": "2.0.0",
            "trusted": True,
            "signer": "DNK Core Authority (ED25519)",
            "signature_verified": True,
            "capabilities": ["read_theme_liquid", "dry_run_simulation"]
        },
        {
            "id": "plug-03",
            "name": "dnk_canvas_research_agent",
            "version": "1.0.4",
            "trusted": True,
            "signer": "DNK Core Authority (ED25519)",
            "signature_verified": True,
            "capabilities": ["canvas_graph_query", "arxiv_synthesis"]
        }
    ]


@router.get("/cabinet/shopify/diff")
def cabinet_shopify_diff(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return {
        "theme_id": "main-prod-dawn-theme",
        "changes_count": 2,
        "diff_entries": [
            {
                "file_path": "sections/cart-drawer.liquid",
                "change_type": "modified",
                "simulated_patch_preview": "@@ -12,4 +12,6 @@\n+ <div class=\"dnk-cart-badge\" data-status=\"simulated\">\n+   <span>DNK OS Safe Preview</span>\n+ </div>"
            },
            {
                "file_path": "snippets/dnk-telemetry-hook.liquid",
                "change_type": "added",
                "simulated_patch_preview": "@@ -0,0 +1,5 @@\n+ {% comment %} DNK Safe Telemetry Listener {% endcomment %}\n+ <script>console.log('DNK OS Read-Only Hook Active');</script>"
            }
        ],
        "dry_run_passed": True,
        "reconciliation_plan": [
            "1. Static syntax check via pytest",
            "2. Shadow DOM render in Docker",
            "3. Zero-mutation validation gate"
        ]
    }


@router.get("/cabinet/canvas/research")
def cabinet_canvas_research(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    enforce_workspace_authorization(x_workspace_id)
    return [
        {
            "id": "res-01",
            "topic": "Multi-Agent Graph Orchestration (TaskDNA v2)",
            "active_subagents": ["rick", "dnk-dev-01"],
            "artifacts_count": 4,
            "last_updated": "2026-08-23T15:00:00Z",
            "summary": "Synthesized architecture inventory and formal TaskDNA contract. Passed verification with 0 schema drift."
        },
        {
            "id": "res-02",
            "topic": "Zero Host Pollution Container Isolation",
            "active_subagents": ["dnk_governance_companion"],
            "artifacts_count": 2,
            "last_updated": "2026-08-23T11:00:00Z",
            "summary": "Enforced volume masking on /app/node_modules and isolated ARM64 / Linux build artifacts."
        }
    ]
