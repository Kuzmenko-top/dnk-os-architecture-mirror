# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STUDIO-ARCH-001-api-migration"
# purpose: "Technical migration and deprecation rules for Canonical API routers and State Separation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym & Antigravity Orchestrator"
# --- END DNK-MRH-HEADER ---

# 🔄 DNK-STUDIO-ARCH-001: API Migration & State Boundaries

## 1. The 4-State Architectural Boundary

To prevent state desynchronization and "split-brain" bugs, data is strictly partitioned into 4 distinct layers:

| Layer | Storage Engine | Scope & Lifecycle | Examples |
| :--- | :--- | :--- | :--- |
| **1. Domain State (SSOT)** | **PostgreSQL** | Persistent business entities. Survives reloads and worker crashes. | `Workspace`, `CanvasElement`, `CanvasEdge`, `TaskDNAGraph`, `Artifact`, `ApprovalRecord`, `AuditTrail`. |
| **2. Runtime State** | **Redis + A2A Mesh** | Ephemeral execution events and agent concurrency locks. | Agent heartbeat, Task `queued`/`running` lock, WebSocket presence, distributed mutex. |
| **3. UI State** | **Zustand** | Local browser session state only. Zero business logic. | `selectedNodeId`, `isLeftDockOpen`, `activeInspectorTab`, `viewportZoom`, `stageMode` (canvas/preview/split). |
| **4. Query Cache** | **TanStack Query** | Client-side API caching with automatic cache invalidation. | `useCanvasQuery(canvasId)`, `useArtifactQuery(id)`, optimistic node updates, background refetch. |

> [!CAUTION]
> **Anti-Pattern Prohibition**: Never store domain workflow logic solely in local React state or Zustand. The server (PostgreSQL) is the sole authority for task states, node connections, and execution outputs.

---

## 2. API Router Consolidation Roadmap

### Canvas Subsystem Migration

```
[Legacy Routes]
- /api/v1/canvas (canvas.py)           ──┐
- /api/v1/canvas_router (canvas_router.py) ──┼──► CANONICAL SSOT: /api/v1/canvas/v3/*
- /api/v1/canvas/ws (canvas_ws.py)      ──┘     (canvas_v3_router.py & canvas_v3_ws.py)
```

**Deprecation Rules**:
1. All client requests in `apps/web/` must target `/api/v1/canvas/v3/*`.
2. Legacy files `canvas.py`, `canvas_router.py`, and `canvas_ws.py` are aliased with HTTP `308 Permanent Redirect` and logged with deprecation warnings.

### Agent-to-Agent (A2A) Subsystem Migration

```
[Legacy Routes]
- /api/v1/a2a/mesh (a2a_mesh_router.py) ──┐
- /api/v1/a2a/sse (a2a_mesh_sse.py)     ──┼──► CANONICAL SSOT: /api/v1/a2a/federation/*
- /api/v1/a2a/ws (a2a_mesh_ws.py)       ──┘     (a2a_federation_router.py & a2a_monitor.py)
```

---

## 3. Optimistic Concurrency Control (OCC) Specification

When a client mutates a node or edge:

1. **Client Request**:
   - `PUT /api/v1/canvas/v3/{canvas_id}/nodes/{node_id}`
   - Header: `If-Match: "v4"` (or payload `server_version: 4`)
   - Payload includes `idempotency_key: "mut_01J..."`
2. **Server Evaluation**:
   - If `current_version == 4`: Mutate DB, increment `version = 5`, return `200 OK` and broadcast `workflow.node.mutated` with `DNKEventEnvelope`.
   - If `current_version != 4`: Reject with `409 Conflict`, returning current server snapshot for client auto-rebase.
