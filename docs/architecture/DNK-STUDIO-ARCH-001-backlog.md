# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STUDIO-ARCH-001-backlog"
# purpose: "PR-Sized Backlog and Definition of Done for Phased Implementation (Phase 0 to Phase 5)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym & Antigravity Orchestrator"
# --- END DNK-MRH-HEADER ---

# 📋 DNK-STUDIO-ARCH-001: Phased Engineering Backlog

## 🏁 Phase 0: Canonicalization & API SSOT

| Task ID | Title & Scope | Files Affected | DoD / Verification |
| :--- | :--- | :--- | :--- |
| **PR-01** | **Canvas API Router Canonicalization**<br>Consolidate all canvas operations onto `canvas_v3_router.py` + `canvas_v3_ws.py`. Deprecate legacy `canvas.py`, `canvas_router.py`, `canvas_ws.py`. | `apps/api/routers/canvas*`, `apps/api/main.py` | `pytest tests/canvas/` 100% Green. No legacy router calls. |
| **PR-02** | **A2A Federation & Event Envelope SSOT**<br>Standardize agent events on `a2a_federation_router.py` with `DNKEventEnvelopeV1`. Deprecate `a2a_mesh_router.py` and `a2a_mesh_sse.py`. | `apps/api/routers/a2a*`, `apps/api/main.py` | SSE and WebSocket streams emit valid envelope schema. |

---

## 🏗️ Phase 1: Infinite Workspace Foundation

| Task ID | Title & Scope | Files Affected | DoD / Verification |
| :--- | :--- | :--- | :--- |
| **PR-03** | **PostgreSQL Canvas Persistence & OCC**<br>Implement server-side `CanvasElement` and `CanvasEdge` models with optimistic concurrency control (`version` checking & `409` conflict handling). | `apps/api/db/`, `apps/api/routers/canvas_v3_router.py` | Concurrency test with simulated duplicate writes returns 409. |
| **PR-04** | **Master StudioShell Component (CapCut + Stitch Layout)**<br>Assemble unified 4-zone shell at `/os/w/[workspaceId]/p/[projectId]` with TopBar, Left Capability Dock, Center Stage, Right Inspector, and Bottom Timeline. | `apps/web/components/studio/`, `apps/web/app/os/` | Page loads cleanly on port 3000 with 4 interactive zones. |

---

## 🧬 Phase 2: Workflow Projection & A2A Binding

| Task ID | Title & Scope | Files Affected | DoD / Verification |
| :--- | :--- | :--- | :--- |
| **PR-05** | **TaskDNA DAG <-> Canvas Node Projection**<br>Bind `GoalNode`, `TaskNode`, `AgentNode`, `ApprovalNode`, and `ArtifactNode` to backend `TaskDNA` entities. | `apps/web/components/canvas/nodes/`, `apps/api/routers/taskdna.py` | Modifying a TaskDNA entity updates canvas node state in realtime. |
| **PR-06** | **Approval Gate Fail-Closed Protocol**<br>Implement side-effect gating on `ApprovalNode` for high-risk actions (`shopify.theme.deploy`, `github.pr.merge`). | `apps/api/services/approval_gate.py`, `apps/web/components/canvas/nodes/ApprovalNode.tsx` | External mutations blocked until explicit cryptographic sign-off. |

---

## 🎭 Phase 3: Multi-Modal Studio Preview Stage

| Task ID | Title & Scope | Files Affected | DoD / Verification |
| :--- | :--- | :--- | :--- |
| **PR-07** | **Polymorphic Artifact Preview Bus**<br>Implement central Stage switcher (`Canvas` / `Preview` / `Split` / `Timeline` / `Board`) rendering Shopify themes, 9:16 videos, React UI, and Diff reports. | `apps/web/components/studio/StudioStage.tsx`, `apps/web/components/preview/` | 1-click preview of all 5 core artifact types without reload. |
| **PR-08** | **Cabinet Features Integration into Context Inspector**<br>Migrate `TimelineTab`, `PRInspectorTab`, `GovernanceTab`, and `MemoryL3Tab` into the Studio Right Inspector. | `apps/web/components/studio/ContextInspector.tsx` | All operational and review capabilities available inside Studio. |

---

## 🪄 Phase 4: Workflow Composer Agent

| Task ID | Title & Scope | Files Affected | DoD / Verification |
| :--- | :--- | :--- | :--- |
| **PR-09** | **Natural Language Goal -> TaskDNA DAG Weaver**<br>User prompt in `⌘K` queries SCONES L3 memory, selects valid Node Contracts from Capability Registry, constructs `WorkflowPlan`, and renders proposed draft on Canvas. | `apps/api/routers/workflow_composer.py`, `apps/web/components/studio/StudioPromptDock.tsx` | Prompt generates validated draft graph awaiting user approval. |

---

## 🛡️ Phase 5: Controlled Self-Extension & Plugin Registry

| Task ID | Title & Scope | Files Affected | DoD / Verification |
| :--- | :--- | :--- | :--- |
| **PR-10** | **Clean-Room Plugin Proposal & License Firewall**<br>Plugin gap detection -> Clean-room spec -> Auditor gate (Auditor ⚔️) -> Test suite verification -> User approval -> Service Registry publication. | `core/service_registry.py`, `plugins/` | Zero AGY/AGPL contamination. Full provenance verification. |
