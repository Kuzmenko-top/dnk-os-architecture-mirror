# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-CANVAS-002-SPEC"
# purpose: "TaskDNA Specification for Visual Canvas & Generative UI 2.0 (DNK-CANVAS-002)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎨 TaskDNA Spec: DNK-CANVAS-002 — Visual Canvas & Generative UI 2.0

## 1. Executive Summary & Goals
DNK-CANVAS-002 establishes an interactive, multi-agent Infinite Canvas and Generative UI 2.0 environment:
- **Infinite Canvas Engine**: High-performance pan/zoom navigation, snap-to-grid, bounding box selection, multi-selection, and coordinate matrix transformations.
- **Real-time Component Sandbox**: Sandboxed rendering (Shadow DOM + iframe security) for live React, Vue, Svelte, and Tailwind components.
- **Multi-Agent Workflow Coordination**: Visual DAG authoring with Supervisor-Worker node types, smart edge data connectors, and reactive state streaming.
- **Generative UI 2.0 Engine**: AI-assisted UI synthesis, auto-layout heuristics, semantic node clustering, and prompt-to-component rendering.
- **Collaborative Sync (OCC + WebSockets)**: Live multi-user cursors, optimistic concurrency control with 3-way graph merge, and section locking.

## 2. TaskDNA Evolutionary DAG
```text
Phase 1: TaskDNA Spec & Core ORM Models (Canvas, CanvasNode, CanvasEdge, CanvasComponent, CanvasSession, CanvasCollaborator)
   │
   ▼
Phase 2: Infinite Canvas Engine & Generative UI 2.0 Pipeline (Transformation Matrix, Shadow DOM Sandbox, GenUI Compiler)
   │
   ▼
Phase 3: Multi-Agent Workflow Engine & OCC Graph Synchronization (DAG Executor, Conflict Resolver, Section Locker)
   │
   ▼
Phase 4: REST API Endpoints, WebSocket Live Stream & E2E Integration Suite
```

## 3. Core Models & Entity Schema
1. **CanvasModel (`canvases`)**: Represents the top-level infinite canvas workspace, dimensions, viewport state, grid settings, and version metadata.
2. **CanvasNodeModel (`canvas_nodes`)**: Represents nodes on the canvas (components, agents, text, shapes, containers) with (x, y, w, h), z-index, and data payload.
3. **CanvasEdgeModel (`canvas_edges`)**: Represents directional connections between node ports with routing style (bezier, orthogonal, straight) and condition expressions.
4. **CanvasComponentModel (`canvas_components`)**: Library of reusable generative UI components with framework (React, Vue, Svelte), template source, and props schema.
5. **CanvasSessionModel (`canvas_sessions`)**: Real-time collaborative sessions tracking active locks, state snapshots, and heartbeat timestamps.
6. **CanvasCollaboratorModel (`canvas_collaborators`)**: Active users/agents in a canvas session with cursor coordinates (x, y), selection IDs, and role.

## 4. Mandatory Invariants & Quality Standards
- **MRH Headers**: All Python, TS, and Markdown files must include DNK-STD-0075 compliant headers.
- **Path Hygiene**: Relative paths only (`./`, `../`), no hardcoded absolute paths.
- **Zero-Waste Protocol**: Sub-20k context token consumption, verified green tests at each phase.
- **Master Quality Gate**: 100% pass rate across all regression suites.
