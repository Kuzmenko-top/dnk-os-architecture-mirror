# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STUDIO-ARCH-001-current-state"
# purpose: "Current State Inventory & Real vs Mock Assessment across all Frontend Routes and Backend Routers."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym & Antigravity Orchestrator"
# --- END DNK-MRH-HEADER ---

# 🔍 DNK-STUDIO-ARCH-001: Current State Inventory & Real vs Mock Audit

## 1. Frontend Routes Inventory & Real/Mock Assessment

| Route | Primary Component | API Source | DB / Storage | Realtime Transport | Mock? | Status & Known Gaps |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/` | `MainHubView.tsx` | `/api/v1/workspace`, `/api/v1/projects` | PostgreSQL + SCONES L3 | None (Polling) | **No** (Real UI) | CapCut Launchpad & Open Design Theme switcher. Fully functional. |
| `/os` & `/os/[id]` | `WorkspaceShell.tsx` | `/api/v1/canvas/v3`, `/api/v1/workflow/compose` | PostgreSQL (`dnk_canvases`) | WS (`/api/v1/canvas/v3/ws/{id}`) | **Partial** | Full ReactXYFlow DAG with live agent execution; fallback client DAG if API offline. |
| `/canvas/[id]` | `CanvasEditor.tsx` | `/api/v1/canvas/v3`, `/api/v1/taskdna` | PostgreSQL + Redis PubSub | WS (`/api/v1/canvas/v3/ws`) | **No** (Real) | OCC synchronization & dynamic 4-scenario switcher. |
| `/cabinet` | `CabinetShell.tsx` | `/api/v1/timeline`, `/api/v1/admin/security` | PostgreSQL | SSE (`/api/v1/a2a/mesh/stream`) | **No** (Real) | Governance, Timeline, Activity logs, Diff Viewer, PR Inspector. |
| `/taskdna` | `TaskForestPage.tsx` | `/api/v1/taskdna/forest`, `/api/v1/taskdna/tasks` | PostgreSQL (`dnk_tasks`) | WebSocket | **No** (Real) | Forest board displaying Task trees, dependencies, and state machine. |
| `/whiteboard` | `WhiteboardEditor.tsx` | `/api/v1/whiteboard` | LocalStorage + SCONES L3 | BroadcastChannel | **Partial** | Freeform concept sketches (Excalidraw integration). |
| `/memory-l3` | `MemoryL3View.tsx` | `/api/v1/memory-l3/query` | PostgreSQL + pgvector + Redis | None (REST) | **No** (Real) | SCONES L3 vector search and memory item inspection. |
| `/patent-shield` | `PatentShieldView.tsx` | `/api/v1/patent-shield/verify` | PostgreSQL audit log | None (REST) | **No** (Real) | IP boundary enforcement and clean-room provenance verification. |
| `/analytics` | `AnalyticsView.tsx` | `/api/v1/workspace-analytics` | PostgreSQL + Redis cache | Polling | **No** (Real) | System health, agent throughput, error rates, and resource utilization. |

---

## 2. Backend Routers Inventory & Canonicalization Decision

### A. Canvas Routers

| File Path | Version | Protocol | Status | Decision & Migration Plan |
| :--- | :--- | :--- | :--- | :--- |
| `apps/api/routers/canvas_v3_router.py` | v3.0.0 | REST | **Canonical** | **PRIMARY SSOT** for all spatial nodes, presence, time-travel, and Weaver. |
| `apps/api/routers/canvas_v3_ws.py` | v3.0.0 | WebSocket | **Canonical** | **PRIMARY SSOT** for bidirectional collaborative canvas mutations & presence. |
| `apps/api/routers/canvas.py` | v1.0.0 | REST | **Legacy** | Deprecate in PR-01. Route aliased to `/api/v1/canvas/v3`. |
| `apps/api/routers/canvas_router.py` | v2.0.0 | REST | **Legacy** | Merge remaining helper endpoints into `canvas_v3_router.py`. |
| `apps/api/routers/canvas_ws.py` | v1.0.0 | WebSocket | **Legacy** | Deprecate. Redirect connections to `canvas_v3_ws.py`. |

### B. Agent-to-Agent (A2A) Routers

| File Path | Version | Protocol | Status | Decision & Migration Plan |
| :--- | :--- | :--- | :--- | :--- |
| `apps/api/routers/a2a_federation_router.py` | v2.0.0 | REST + SSE | **Canonical** | **PRIMARY SSOT** for multi-agent mesh, consensus, DLQ, and SSE streams. |
| `apps/api/routers/a2a_monitor.py` | v1.5.0 | REST | **Canonical** | Telemetry, active topics, locks, and agent inspection. |
| `apps/api/routers/a2a_mesh_router.py` | v1.0.0 | REST | **Legacy** | Superseded by `a2a_federation_router.py`. Deprecate in PR-02. |
| `apps/api/routers/a2a_mesh_sse.py` | v1.0.0 | SSE | **Legacy** | Integrated into `a2a_federation_router.py` (`/api/v1/a2a/federation/stream`). |
| `apps/api/routers/a2a_mesh_ws.py` | v1.0.0 | WebSocket | **Legacy** | Deprecate in favor of unified A2A telemetry over Federation SSE. |

---

## 3. Analysis of Duplications & Gaps

1. **Parallel Router Versions**:
   - The existence of `canvas.py`, `canvas_router.py`, and `canvas_v3_router.py` causes client ambiguity. **Resolution**: `canvas_v3_router.py` is the official SSOT (`/api/v1/canvas/v3/*`).
2. **Page Fragmentations**:
   - Having separate full-page views for `/cabinet`, `/taskdna`, `/whiteboard`, and `/canvas` forces context switching. **Resolution**: All 4 views are unified as modular modes within the single **DNK Studio Shell**.
3. **Mock Fallback vs Real Backend**:
   - When the backend is running, `CanvasEditor` and `WorkspaceShell` execute against PostgreSQL and Redis. However, when disconnected, they gracefully fall back to local preview. **Resolution**: Explicit visual status badge (`🟢 Connected (PostgreSQL)` vs `🟡 Offline Preview Mode`) in the Studio Top Bar.
