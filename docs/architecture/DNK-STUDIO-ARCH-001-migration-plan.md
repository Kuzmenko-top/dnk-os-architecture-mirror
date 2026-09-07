# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STUDIO-ARCH-001-migration-plan"
# purpose: "Step-by-step Migration & Implementation Plan for DNK Studio Canonicalization."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym & Antigravity Orchestrator"
# --- END DNK-MRH-HEADER ---

# 🚀 DNK-STUDIO-ARCH-001: Migration & Implementation Roadmap

## 📦 PR-Sized Execution Milestones

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ MILESTONE 1: Router & API Canonicalization                                            │
│  • PR-01: Consolidate canvas routers onto canvas_v3_router.py + canvas_v3_ws.py       │
│  • PR-02: Consolidate A2A routers onto a2a_federation_router.py (SSE + Mesh)          │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ MILESTONE 2: Studio Shell Consolidation                                               │
│  • PR-03: Create StudioShell.tsx consolidating TopNav, LeftDock, Stage, Inspector     │
│  • PR-04: Integrate Cabinet components (Timeline, DiffViewer, PRInspector, Governance)│
├───────────────────────────────────────────────────────────────────────────────────────┤
│ MILESTONE 3: Open Design Generative Bridge                                            │
│  • PR-05: Connect Open Design (:3005) token generator directly into Stitch Prompt Dock│
│  • PR-06: Implement polymorphic Artifact Preview Bus (Liquid, Video, React, Docs)     │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ MILESTONE 4: End-to-End Scenario Verification (ReBurn Launch)                          │
│  • PR-07: Full verification: Brief ──► Liquid Theme ──► 9:16 Video ──► Approval Gate │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Milestone 1: Router & API Canonicalization

### Task 1.1: Canonical Canvas API (PR-01)
- Set `apps/api/routers/canvas_v3_router.py` and `apps/api/routers/canvas_v3_ws.py` as the official endpoints.
- Alias legacy routes `/api/v1/canvas/*` to `/api/v1/canvas/v3/*`.
- Mark legacy `canvas.py`, `canvas_router.py`, and `canvas_ws.py` as deprecated.

### Task 1.2: Canonical A2A Federation (PR-02)
- Standardize all live agent streams on `apps/api/routers/a2a_federation_router.py` using `DNKEventEnvelope`.
- Deprecate separate legacy `a2a_mesh_router.py` and `a2a_mesh_sse.py`.

---

## 🎯 Milestone 2: Studio Shell Consolidation

### Task 2.1: Master Studio Shell (PR-03)
- Path: `apps/web/app/os/[workspaceId]/page.tsx` & `/os/w/[workspaceId]/p/[projectId]`.
- Assembles:
  1. `StudioTopBar` (Breadcrumbs, Presets, Run, Export).
  2. `CapabilityDock` (Node Palette, Media Vault, Open Design Components).
  3. `StudioStage` (Canvas, Preview, Split, Timeline, Kanban Board).
  4. `ContextInspector` (Node Properties, Diffs, PR Review, Memory L3, Governance).
  5. `ExecutionTimelineDrawer` (Media scrubber & live A2A telemetry).

### Task 2.2: Cabinet Feature Re-use (PR-04)
- Migrate `TimelineTab`, `CommandOverviewTab`, `PRInspectorTab`, and `GovernanceTab` from `CabinetShell` into `ContextInspector` and `ExecutionTimelineDrawer`.

---

## 🎯 Milestone 3: Open Design Generative Bridge

### Task 3.1: Token & Component Injection (PR-05)
- Allow user prompts in `StitchPromptDock` to request any of the 100+ Open Design systems (e.g. *Stripe*, *Linear*, *Luxury*, *Neon*).
- Backend worker generates component code and emits it as an interactive `ComponentSliceNode` on the Canvas.

### Task 3.2: Polymorphic Artifact Bus (PR-06)
- Enable 1-click preview of Shopify Liquid AST, 9:16 Video Ad timeline, Markdown PR docs, and SCONES L3 vector memories in the central Stage.

---

## 🎯 Milestone 4: End-to-End Canonical Scenario

### Task 4.1: ReBurn Smoker v2 Launch Verification (PR-07)
- User selects *ReBurn Smoker Launch* in Studio Shell.
- TaskDNA orchestrates:
  1. `gerych_researcher` generates persona & brief.
  2. `dnk_dev_fullstack` + Open Design generates Obsidian Aurora theme.
  3. `dnk_video_ai_creator` renders 9:16 vertical Reels ad with audio.
  4. `ApprovalNode` halts for human authorization.
  5. User clicks "Approve", `dnk_shopify` deploys assets.
  6. Quality Gate `./scripts/verify_all.sh` verifies 100% Green.
