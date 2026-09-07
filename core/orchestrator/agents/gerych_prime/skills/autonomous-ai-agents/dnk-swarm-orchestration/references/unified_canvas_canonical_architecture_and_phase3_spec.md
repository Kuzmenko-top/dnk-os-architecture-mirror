# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/unified_canvas_canonical_architecture_and_phase3_spec.md"
# purpose: "Canonical Reference for Unified Canvas 4/4 MVP Convergence and Phase 3 Swarm Co-Pilot Protocol"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎯 Unified Canvas Canonical Architecture & Phase 3 Swarm Co-Pilot Reference

## 1. Executive Summary & Convergence Milestone
The Unified Spatial Canvas consolidates all previous development into a single canonical architecture:
- **MVP Convergence**: 4/4 steps completed, 1488+ tests green, 0 absolute path violations.
- **Canonical Document**: `docs/architecture/UNIFIED_CANVAS_CANONICAL_SPEC_V1.md`.

## 2. Core Architectural Pillars

### A. Frontend SSOT & Dual-Layer Layout (`apps/web`)
- **React Flow v12**: `@xyflow/react` + JSON Canvas 1.0 (.canvas spec compatibility).
- **Zustand SSOT**: `useCanvasStore.ts` manages active nodes, edges, whiteboard elements, selection, and viewport coordinates.
- **Dual-Layer Whiteboard**: `WhiteboardOverlay.tsx` sits synchronously above `CanvasEngine.tsx` with synced camera matrix (`x`, `y`, `zoom`).
- **Dynamic Controls**: `StitchFloatingDock.tsx` (natural language prompt dock) and `MediaSidebar.tsx` (drag-to-canvas component templates).

### B. Backend Engine & Persistence (`services/dnk_canvas_api`)
- **FastAPI Core**: Port 8000 with asynchronous SQLAlchemy 2.0.
- **PostgreSQL 16 Schema**: `hub_memory` schema with tables:
  - `canvas_documents`: Workspace and metadata root.
  - `canvas_nodes`: Spatial node records.
  - `canvas_edges`: Relational connection topology.
  - `canvas_revisions`: Immutable history snapshots with SHA-256 scene checksums.
- **Dual Sync (Delta Sync + WebSocket)**:
  - REST Delta Sync (`POST /api/v1/canvases/{canvas_id}/delta`): Atomic patch updates with debounced client flush (750ms).
  - WebSocket (`WS /api/v1/ws/canvas/{canvas_id}`): Low-latency broadcast of collaborator cursors, presence, and real-time remote deltas.
  - Offline Fallback: `IndexedDB` transaction buffer in `canvasApi.ts` for zero data loss during network disruptions.

## 3. Phase 3: Swarm Co-Pilot Specification

### Components & Responsibilities:
1. **`CopilotToolbar.tsx` (`apps/web/components/copilot/`)**:
   - Floating contextual toolbar anchored to active/selected nodes.
   - Quick invocation via `Cmd+K` keyboard shortcut.
   - Context packager: Extracts active node data, type, and attached Brand DNA from `sconesStore`.
   - Action chips: "Deepen Strategy", "Reskin UI", "Transpile to Liquid", "Generate Storyboard".

2. **`intentResolver.ts` (`apps/web/lib/`)**:
   - Classifies user intent from natural language prompts.
   - Routes request to specialized swarm agents:
     - Strategy/Copy -> `dnk_marketing_cmo`
     - Visuals/Media -> `dnk_video_ai_creator`
     - Shopify Liquid -> `dnk_shopify`
     - Backend/API -> `dnk_dev_fullstack`
     - Code/UI -> `gerych_builder`
     - Audit/Testing -> `gerych_auditor`

3. **`budgetGuard.ts` (`apps/web/lib/`)**:
   - Real-time token and dollar cost estimation prior to dispatch.
   - Enforces configurable thresholds (`WARN` above $0.20, `BLOCK` above $1.00 unless explicitly approved).
   - In-UI safety badge indicating cost grade (Free, Minimal, Heavy).

4. **Streaming Tokens & Reactive Cascade (`propagateSwarm`)**:
   - Asynchronous SSE / WebSocket token streaming directly into node visual DOM.
   - Topological downstream propagation down connected edges (e.g. Strategy -> Design -> Code -> Kanban).
   - Atomic transaction history snapshot (`history.past`) for 1-click Undo/Redo.
