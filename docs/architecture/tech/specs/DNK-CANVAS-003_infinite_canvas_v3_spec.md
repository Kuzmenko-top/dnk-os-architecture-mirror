# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-CANVAS-003-SPEC"
# purpose: "TaskDNA Specification for Infinite Canvas V3: Multi-User Collaboration, Spatial Indexing & AI Generation"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎨 DNK-CANVAS-003: Infinite Canvas V3 Specification

## 1. Executive Summary
DNK-CANVAS-003 elevates the DNK OS Infinite Canvas into an enterprise-grade collaborative spatial workspace. It introduces an R-Tree / Bounding Box spatial index for sub-millisecond viewport culling over 100,000+ canvas nodes, a low-latency Awareness & Presence protocol with ephemeral cursor streaming and multi-user lock arbitration, point-in-time History Snapshots with time-travel replay, and an AI Node Generation Engine that synthesizes contextual nodes and smart auto-wires flows based on spatial proximity and semantic graphs.

## 2. Core Architectural Pillars

### 2.1 Spatial Indexing & Viewport Culling
- **Bounding Box Geometry**: (min_x, min_y, max_x, max_y) for nodes, groups, and edges.
- **R-Tree / Quadtree Query Engine**: Sub-millisecond spatial range queries (`query_viewport(canvas_id, viewport_bbox, lod)`), level-of-detail (LOD) aggregation, and nearest-neighbor discovery for snap-to-grid.

### 2.2 Multi-User Collaboration & Presence
- **Presence & Ephemeral Cursors**: High-frequency cursor position broadcasting (x, y, pointer_state, active_selection_ids) with low-overhead delta compression.
- **Lock Arbitration**: Ephemeral node leasing with 15s TTL, heartbeats, and conflict-free release to prevent concurrent node mutation deadlocks.
- **Semantic Grouping**: Bounding-box wrapped multi-node clusters with shared locks and hierarchical movement.

### 2.3 History Time-Travel Snapshots
- **Point-in-Time Snapshots**: Compact JSON diff snapshots storing canvas node/edge state deltas with cryptographic parent hashes.
- **Undo / Redo & Branch Replay**: Branching history trees allowing rollbacks to previous milestone tags without data loss.

### 2.4 Contextual AI Node Generation
- **Proximity & Graph Context**: LLM-driven node generation that ingests upstream connected nodes, viewport bounds, and domain objectives.
- **Smart Auto-Wiring**: Automatic topological edge generation connecting new synthesized nodes to contextually relevant parent anchors.

## 3. Four-Phase Task Execution Plan
- **Phase 1**: TaskDNA Spec & 6 ORM Models (`CanvasSpatialIndex`, `CanvasPresence`, `CanvasCursorStream`, `CanvasHistorySnapshot`, `CanvasAIGenerationRequest`, `CanvasSemanticGroup`).
- **Phase 2**: Spatial Indexing Quadtree Engine & Multi-User Presence Arbiter Service.
- **Phase 3**: Contextual AI Node Synthesis Engine & Smart Auto-Wiring Flow Weaver.
- **Phase 4**: REST API Router, WebSocket Collab Mesh, E2E Integration Tests & Evidence Generation.
