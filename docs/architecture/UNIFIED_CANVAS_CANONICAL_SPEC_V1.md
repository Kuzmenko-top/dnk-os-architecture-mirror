<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/architecture/UNIFIED_CANVAS_CANONICAL_SPEC_V1.md"
purpose: "Canonical System Architecture Specification & Production Roadmap for DNK OS Unified Canvas (MVP to Phase 6)."
canonical_source: true
alters_files: []
triggers_tasks: ["TaskDNA-PHASE-3-SWARM-COPILOT"]
status: "Active"
version: "1.0.0"
updated_at: "2026-09-03"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🌐 DNK OS Unified Canvas: Canonical Architecture Specification & Production Roadmap (v1.0.0)

## 📌 1. Executive Summary & Convergence Milestone

The **DNK OS Unified Spatial Canvas** has achieved **100% MVP completion** across all 4 foundational convergence steps. The fragmented legacy interfaces (`/canvas`, `/whiteboard`, `/teleprompter`, `/taskdna`, `/tasks`, `/launchpad`) are formally converged into a **Single Working Canvas** powered by React Flow v12, Zustand reactive store, FastAPI, PostgreSQL 16 schema (`hub_memory`), Redis 7, and real-time WebSocket delta synchronization with offline IndexedDB fallback.

```yaml
convergence_status:
  mvp_phase:
    step_1_ssot: "✅ COMPLETE (useCanvasStore - Single Source of Truth)"
    step_2_whiteboard: "✅ COMPLETE (WhiteboardOverlay - Dual-Layer Sketch Viewport Sync)"
    step_3_stitch_dock: "✅ COMPLETE (StitchFloatingDock + MediaSidebar Templates)"
    step_4_autosave: "✅ COMPLETE (PostgreSQL 16 Delta Sync + WebSocket + IndexedDB)"
    completion: "100% (4/4 Steps Verified)"
  production_phases:
    phase_3_copilot: "🔄 IN PROGRESS (Swarm Co-Pilot: CopilotToolbar + Intent Resolver + Budget Guard)"
    phase_4_photo_studio: "⏳ PENDING (BiRefNet Cutout + IC-Light Relighting + FLUX.1)"
    phase_5_video_intelligence: "⏳ PENDING (@dnk/video-audit-core Integration + Retention Curve)"
    phase_6_remotion_shopify: "⏳ PENDING (9:16 Shorts Generation + Live Shopify OS 2.0 Sync)"
    progress: "25% Active (Phase 3 Underway)"
  test_gate:
    regression_tests: "1488+ PASSED (100% Green)"
    python_syntax_errors: 0
    absolute_path_violations: 0
```

---

## 🏛️ 2. Canonical Unified System Architecture

```
+---------------------------------------------------------------------------------------------------+
| TOP BAR: [Project Selector] [Mode: Graph / Sketch / Preview] [Active Swarm Agent] [Share / Export]|
+---------------+-------------------------------------------------------------------+---------------+
| LEFT DOCK     |                      CENTRAL UNIFIED CANVAS                       | RIGHT PANEL   |
| (Tools)       |                                                                   |               |
|               |  [Strategy Node] ──────(DataFlow)─────> [Design Gallery Node]     | [Node Props]  |
| [⚡ Prompt]   |         │                                       │                 |               |
| [📁 Nodes]    |    (ControlFlow)                           (DataFlow)             | [Swarm Co-    |
| [🎨 Whiteboard|         ▼                                       ▼                 |  Pilot Panel] |
|   Overlay]    |  [Kanban Sprint Node]                 [Shopify Liquid Node]       |               |
| [🎬 Video]    |                                                 │                 | [SCONES Brand |
| [🛒 Shopify]  |                                           (Live Preview)          |  Memory]      |
|               |                                                 ▼                 |               |
|               |                                        [Live Preview Node]        |               |
+---------------+-------------------------------------------------------------------+---------------+
| BOTTOM DOCK: [StitchFloatingDock / CopilotToolbar (Cmd+K)] [Undo/Redo] [Zoom / MiniMap]           |
+---------------------------------------------------------------------------------------------------+
```

### 2.1 Frontend Subsystem (`apps/web`)

1. **Reactive State SSOT (`useCanvasStore.ts`)**:
   - Manages graph state (`nodes`, `edges`, `viewport`), selection, history (`past`, `future`), and dirty delta queues.
   - Debounced persistence triggers (750ms) dispatching atomic incremental patches.
2. **Dual-Layer Sketching (`WhiteboardOverlay.tsx`)**:
   - Transparent vector sketching layer mounted directly over React Flow.
   - Synchronized pan/zoom transform matrices ensuring hand-drawn elements scale and translate precisely with canvas nodes.
3. **Floating Interaction Dock (`StitchFloatingDock.tsx` & `MediaSidebar.tsx`)**:
   - Bottom-pinned reactive prompt input with agent selector and streaming execution logs.
   - Drag-and-drop template catalog for instantaneous node instantiation on the canvas.
4. **Specialized Spatial Nodes (`apps/web/components/canvas/nodes/`)**:
   - `StrategyMarkdownNode`: Generative product briefs, competitor teardowns, and positioning matrix.
   - `DesignGalleryNode`: Multi-variant visual moodboards, palette pickers, and layout assets.
   - `ShopifyBuilderNode`: Interactive Liquid section builder with bi-directional AST synchronization.
   - `SprintKanbanNode`: Real-time agile execution board linked to TaskDNA DAG tasks.
   - `VideoStoryboardNoteNode`: 9:16 mobile aspect ratio scenes with audio waveforms and timestamps.
   - `LiveWebPreviewNode`: Sandboxed iframe renderer for instant theme preview.

### 2.2 Backend Subsystem (`services/dnk_canvas_api`)

1. **FastAPI Engine (`port 8000`)**:
   - Endpoints:
     - `POST /api/v1/canvases/{canvas_id}/delta`: High-frequency delta synchronization applying node/edge mutations.
     - `GET /api/v1/canvases/{canvas_id}`: Hydrates full canvas document state.
     - `GET /api/v1/canvases/{canvas_id}/revisions`: Retrieves historical revision snapshots.
     - `POST /api/v1/canvases/{canvas_id}/revisions/{revision_id}/restore`: Time-travel state recovery.
   - WebSockets:
     - `WS /api/v1/ws/canvas/{canvas_id}`: Real-time broadcast for cursor movements, active agent telemetries, and multi-user delta updates.
2. **Storage & Database (`PostgreSQL 16`)**:
   - Schema: `hub_memory`
   - Tables:
     - `canvas_documents`: Canvas metadata, root attributes, and current scene checksum (`SHA-256`).
     - `canvas_nodes`: Spatial coordinates (`x, y, zIndex`), dimensions, node types, and nested JSON payload.
     - `canvas_edges`: Source/target bindings, edge styles, labels, and animated data conduits.
     - `canvas_revisions`: Immutable revision log enabling deterministic audit and rollback.
3. **Resilience & Offline Layer (`IndexedDB`)**:
   - `canvasApi.ts` encapsulates local IndexedDB caching.
   - Network disconnections queue uncommitted deltas locally; upon reconnection, the queue flushes and reconciles via vector clocks.

---

## ⚡ 3. Phase 3: Swarm Co-Pilot Specification (Active Phase)

### 3.1 Objective
Empower every canvas node with contextual AI capabilities via an in-place `CopilotToolbar`, an intelligent `Intent Resolver` mapping user prompts to specialized swarm agents, a proactive `Budget Guard` protecting API consumption, and reactive topological cascade updates (`propagateSwarm`).

### 3.2 Target Components & File Structure
```yaml
phase_3_components:
  frontend:
    toolbar: "apps/web/components/copilot/CopilotToolbar.tsx"
    intent_engine: "apps/web/lib/intentResolver.ts"
    budget_guard: "apps/web/lib/budgetGuard.ts"
    copilot_store: "apps/web/store/useCopilotStore.ts"
  backend:
    swarm_router: "services/dnk_canvas_api/swarm.py"
    streaming_service: "services/dnk_canvas_api/streaming.py"
```

### 3.3 Component Specifications

#### A. In-Place Copilot Toolbar (`CopilotToolbar.tsx`)
- **Trigger**: Hotkey `Cmd+K` / `Ctrl+K` when one or more nodes are selected, or floating above the active node header.
- **Context Awareness**: Automatically serializes selected node schemas, predecessor nodes, and upstream Brand DNA from `sconesStore`.
- **Quick Action Chips**:
  - `⚡ Expand Detail`: Elaborates requirements or generates sub-tasks.
  - `🎨 Reskin Design`: Triggers colorway and layout mutations.
  - `🛍️ Transpile to Liquid`: Generates Shopify OS 2.0 section schema.
  - `🎬 Storyboard Script`: Formats marketing script into 3s hook, retention body, and CTA.

#### B. Swarm Intent Resolver (`intentResolver.ts`)
- Evaluates raw natural language input and classifies execution routes into target agents:
  ```typescript
  export type SwarmAgentTarget = 
    | 'gerych_builder'       // Code, UI layouts, components
    | 'dnk_shopify'          // Liquid AST, sections, metafields
    | 'dnk_video_ai_creator' // Scripts, storyboard, voiceover
    | 'dnk_dev_fullstack'    // API routes, database schemas
    | 'gerych_researcher'    // Competitive intelligence, benchmarks
    | 'gerych_auditor';      // Security scan, quality gate verification
  ```
- Generates a structured TaskDNA DAG proposal before executing expensive operations.

#### C. Budget & Token Guard (`budgetGuard.ts`)
- Pre-execution cost estimator calculating token consumption and dollar expenditure:
  - Input token cost + estimated output tokens.
  - Visual badge: `🟢 ~$0.002 (Low)` | `🟡 ~$0.04 (Medium)` | `🔴 >$0.25 (High Approval Required)`.
  - Hard limit guards preventing runaway recursive agent loops.

#### D. Real-Time Token Streaming & Downstream Reactive Cascade (`propagateSwarm`)
- Direct streaming of LLM tokens into target node visual state via SSE / WebSocket.
- Once a parent node completes generation, `propagateSwarm` evaluates outgoing edges and triggers downstream node re-evaluations without requiring full canvas re-renders.

---

## 🗺️ 4. Subsequent Production Roadmap (Phases 4 - 6)

### Phase 4: CapCut AI Photo Studio (`PhotoStudioNode.tsx`)
- **Core Engine**: BiRefNet (high-precision background extraction), IC-Light (light source relighting), FLUX.1 + LayerDiffuse.
- **Canvas Interaction**: Direct bounding box selection on image nodes with in-canvas cutout, relighting, and background replacement.

### Phase 5: Video Intelligence Node (`VideoAuditReportNode.tsx`)
- **Core Engine**: Integration of `@dnk/video-audit-core` package.
- **Capabilities**: URL ingestion (TikTok, Instagram Reels, YouTube Shorts), WhisperX transcription, first-3s hook retention curve, audio tempo analysis, and visual claim verification.

### Phase 6: Remotion Video Factory & Live Shopify OS 2.0
- **Core Engine**: Server-side and browser Remotion rendering pipeline.
- **Capabilities**: Automated 9:16 vertical video compilation with dynamic voiceover, animated kinetic typography, and bidirectional synchronization with live Shopify Admin API themes.

---

## 🛡️ 5. Quality, Security & Verification Contracts

1. **Zero Path Violations**: 100% compliance with relative path invariants (`./`, `../`). No absolute paths in code, tests, or manifests.
2. **Quality Gate Compliance**: All feature implementations must maintain green status across the 1488+ test suite (`bash scripts/verify_all.sh`).
3. **Data Integrity**: JSON Canvas 1.0 standard compliance guaranteed for all import/export operations, ensuring zero vendor lock-in.
4. **Tenant Isolation**: Strict isolation using `workspace_id` across database queries, Redis channels, and SCONES memory partitions.
