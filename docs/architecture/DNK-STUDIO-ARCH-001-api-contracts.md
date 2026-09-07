# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STUDIO-ARCH-001-api-contracts"
# purpose: "SSOT API Contracts, Node Manifest v1, Edge Semantics, Backend Enums, and Structured Execution Event Envelope for DNK Studio."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym & Antigravity Orchestrator"
# --- END DNK-MRH-HEADER ---

# 📜 DNK-STUDIO-ARCH-001: API Contracts & Schema Specifications

## 1. Structured Execution Event Envelope (`DNKEventEnvelopeV1`)

Rather than streaming unstructured internal "thoughts", all real-time events over WebSocket (`/api/v1/canvas/v3/ws/{canvas_id}`) and SSE (`/api/v1/a2a/federation/stream`) MUST conform to this exact structured execution schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DNKEventEnvelopeV1",
  "description": "Standardized Realtime Event Envelope for Structured Execution Traces across DNK OS Studio",
  "type": "object",
  "required": [
    "event_id",
    "event_type",
    "workspace_id",
    "canvas_id",
    "trace_id",
    "occurred_at",
    "actor_type",
    "actor_id",
    "payload"
  ],
  "properties": {
    "event_id": {
      "type": "string",
      "pattern": "^evt_[0-9a-zA-Z]{16,36}$",
      "description": "Unique event identifier"
    },
    "event_type": {
      "type": "string",
      "enum": [
        "agent.task.assigned",
        "agent.tool.invoked",
        "agent.artifact.generated",
        "agent.test.started",
        "agent.test.result",
        "agent.retry.scheduled",
        "agent.task.completed",
        "agent.task.failed",
        "workflow.node.status_changed",
        "workflow.node.mutated",
        "workflow.edge.connected",
        "workflow.edge.disconnected",
        "approval.gate.requested",
        "approval.gate.resolved",
        "canvas.presence.updated",
        "canvas.cursor.moved",
        "system.dlq.alert",
        "system.occ.conflict"
      ],
      "description": "Structured execution lifecycle event"
    },
    "workspace_id": { "type": "string" },
    "canvas_id": { "type": "string" },
    "workflow_id": { "type": "string" },
    "node_id": { "type": "string" },
    "trace_id": { "type": "string" },
    "occurred_at": { "type": "string", "format": "date-time" },
    "actor_type": { "type": "string", "enum": ["user", "agent", "system", "worker"] },
    "actor_id": { "type": "string" },
    "payload": {
      "type": "object",
      "properties": {
        "previous_status": { "type": "string" },
        "status": { "type": "string" },
        "tool_name": { "type": "string" },
        "tool_duration_ms": { "type": "number" },
        "artifact_ids": { "type": "array", "items": { "type": "string" } },
        "evidence_links": { "type": "array", "items": { "type": "string" } },
        "server_version": { "type": "integer" },
        "error": {
          "type": "object",
          "properties": {
            "code": { "type": "string" },
            "message": { "type": "string" },
            "solution_id": { "type": "string" }
          }
        }
      }
    }
  }
}
```

---

## 2. Server-Side Edge Semantic Enum (`EdgeKind`)

Edge semantics are enforced on the backend as a first-class Python enum:

```python
from enum import Enum

class EdgeKind(str, Enum):
    DATA = "data"              # Passes typed output to input port (Executable)
    CONTROL = "control"        # Triggers state execution sequence (Executable)
    DEPENDENCY = "dependency"  # Target blocked until source is COMPLETED (Executable)
    APPROVAL = "approval"      # Human sign-off gate before side-effect (Executable)
    REFERENCE = "reference"    # Provenance link to memory/artifact (Declarative metadata)
    VISUAL = "visual"          # UI mental grouping with zero side-effects (Declarative metadata)
```

**Runtime Invariant**: The workflow execution engine executes ONLY `DATA`, `CONTROL`, `DEPENDENCY`, and `APPROVAL` edges. `REFERENCE` and `VISUAL` edges never trigger side effects.

---

## 3. Router Domain Ownership Matrix (No Arbitrary Deletion)

| Router File | Prefix | Primary Domain Responsibility | Consumers |
| :--- | :--- | :--- | :--- |
| `canvas_v3_router.py` | `/api/v1/canvas/v3` | Spatial indexing, lock management, presence, and history/branching. | `CanvasEditor.tsx`, `StitchCanvas.tsx`, Spatial Weaver |
| `canvas_v3_ws.py` | `/api/v1/canvas/v3/ws` | Realtime bidirectional collaboration & cursor presence. | `CanvasEditor.tsx`, Collaborative Studio Stage |
| `canvas_router.py` | `/api/v1/canvas` | Core Workflow execution, Node/Edge CRUD, UI generation, Sandbox envelope. | `WorkspaceShell.tsx`, `TaskDNA`, Studio Node Palette |
| `a2a_federation_router.py` | `/api/v1/a2a/federation` | Agent dispatch, capability routing, probe evaluation, and SSE telemetry stream. | `StudioSessionStore`, `ExecutionTimelineDrawer` |
| `a2a_monitor.py` | `/api/v1/a2a` | Observability, DLQ, active topics, distributed locking, and telemetry. | `ContextInspector.tsx`, `CabinetShell.tsx`, Metrics |
| `a2a_mesh_router.py` | `/api/v1/a2a/mesh` | Autonomous agent contract negotiation, auctions, and consensus rounds. | Swarm Coordinator, Agent Runtime |

---

## 4. Workflow Composer Agent Contract (`WorkflowPlan`)

```python
from pydantic import BaseModel

class WorkflowPlan(BaseModel):
    workflow_id: str
    workspace_id: str
    goal: str
    template_id: str | None = None
    nodes: list[dict]
    edges: list[dict]
    assumptions: list[str] = []
    risks: list[dict] = []
    approval_gates: list[dict] = []
    estimated_duration_seconds: int | None = None
    confidence: float
```
