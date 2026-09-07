# Unified Single Working Canvas Convergence Pattern

## Core Principle
Disparate UI tools (such as structured node graphs, freehand whiteboards, AI prompt docks, e-commerce sync bars, and teleprompter/video previews) should never remain fragmented across separate routes (`/canvas`, `/whiteboard`, `/teleprompter`, `/tasks`). They must converge into **One Unified Spatial Canvas** centered around a Single Source of Truth (SSOT).

## 4 Pillars of Canvas Convergence

### 1. Single State SSOT (`useCanvasStore`)
- Replace component-local state (`useNodesState`, `useEdgesState`) in studio shells (`DNKStudioWorkspace`) with the centralized Zustand reactive store (`useCanvasStore.ts`).
- Ensure that choosing business templates from launchpads or completing onboarding wizards automatically hydrates the canvas store and preserves node topologies, edges, and data-flow bindings.

### 2. Dual-Layer Spatial Overlay (Graph Nodes + Freehand Whiteboard)
- Avoid forcing users to navigate to a separate `/whiteboard` page.
- Mount Excalidraw or freehand drawing as a toggleable overlay layer (`W` shortcut or toolbar button) directly on top of the structured `@xyflow/react` nodes.
- Maintain synchronized viewport transformations (pan/zoom) so freehand sketches stay anchored to their corresponding domain nodes.

### 3. In-Place Multi-Modal Prompt Dock & Chat Consolidation (Stitch / Co-Pilot)
- Float a bottom prompt dock (`StitchPromptDock`) over the infinite canvas for rapid one-line commands.
- **Conversational Surface Consolidation Invariant (Single Active Input Surface)**:
  - NEVER render an open floating Prompt Dock and a slide-out Chat Drawer simultaneously; doing so confuses users ("2 chats at once").
  - When the detailed Chat Drawer opens (`isChatOpen === true`), automatically tuck away or unmount the floating Prompt Dock.
  - When the Drawer closes, restore the Prompt Dock with a quick-access toggle (`Bot / History`) to reopen full dialogue history.
  - Both surfaces **must** share the identical Zustand store state (`chatMessages`, `isChatOpen`, `chatIntake`), ensuring zero message desynchronization.
- When an AI prompt is executed, the agent swarm (e.g. `gerych_builder`, `dnk_shopify`, `dnk_video_ai_creator`) spawns new typed nodes directly onto the graph and establishes animated `dataFlow` or `controlFlow` edges.

### 4. Persisted Spatial API Synchronization (PostgreSQL 16 `hub_memory`)
- Transition from purely client-side `localStorage` caching to transactional backend persistence via `POST /api/v1/canvases/{id}/revisions`.
- Enforce strict UUID tenancy via `X-Workspace-Id`.
- Support offline-first optimistic updates with debounced background commits.
