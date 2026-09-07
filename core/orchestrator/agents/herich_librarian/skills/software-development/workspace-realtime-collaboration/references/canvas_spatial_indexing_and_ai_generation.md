# Infinite Canvas V3: Spatial Indexing, Collaboration & AI Flow Synthesis

## Overview
Architectural reference for Infinite Canvas V3 multi-user spatial indexing, real-time presence tracking, history snapshots, LLM-driven AI node synthesis models & service engines, and REST/WebSocket API multiplexers.

## 1. ORM Models & Data Contracts (`apps/api/db/models/`)

### Spatial Indexing (`CanvasSpatialIndexModel`)
- **Purpose**: Fast R-Tree / Quadtree bounding box range queries and Level-of-Detail (LOD) viewport culling.
- **Key Fields**: `canvas_id`, `node_id`, `group_id`, `min_x`, `min_y`, `max_x`, `max_y`, `lod_level`, `is_active`.
- **Query Pattern**: Viewport intersection `intersects((min_x, min_y, max_x, max_y))` returning visible node/group IDs.

### Real-Time Presence (`CanvasPresenceModel`)
- **Purpose**: Track active collaborators, viewport coordinates, selected node IDs, and active tools.
- **Key Fields**: `canvas_id`, `user_id`, `user_name`, `user_color`, `cursor_x`, `cursor_y`, `viewport_bounds`, `selected_node_ids`, `active_tool`, `is_online`.

### Ephemeral Cursor Stream (`CanvasCursorStreamModel`)
- **Purpose**: Delta event log for cursor movements and canvas interactions (`POINTER_MOVE`, `SELECTION_CHANGE`, `VIEWPORT_PAN`, `NODE_DRAG`).
- **Key Fields**: `canvas_id`, `user_id`, `event_type`, `x`, `y`, `payload`, `timestamp`.

### Time-Travel History Snapshot (`CanvasHistorySnapshotModel`)
- **Purpose**: State snapshots and diff logs for Undo/Redo time travel and collaborative version branching.
- **Key Fields**: `canvas_id`, `version_index`, `snapshot_tag`, `author_id`, `nodes_count`, `edges_count`, `state_diff_json`, `parent_snapshot_id`.

### AI Node Generation Request (`CanvasAIGenerationRequestModel`)
- **Purpose**: Asynchronous LLM-driven canvas node & flow synthesis requests.
- **Key Fields**: `canvas_id`, `requester_id`, `prompt`, `context_node_ids`, `target_coordinates`, `status` (`PENDING`, `PROCESSING`, `GENERATED`, `APPLIED`, `FAILED`), `generated_nodes`, `generated_edges`.

### Semantic Node Group (`CanvasSemanticGroupModel`)
- **Purpose**: Multi-node semantic clustering, visual containers, and collapsible groups.
- **Key Fields**: `canvas_id`, `title`, `description`, `color`, `node_ids`, `bounding_box`, `is_collapsed`.

---

## 2. Service Engines Architecture (`apps/api/services/`)

### Spatial Indexing Engine (`CanvasSpatialIndexEngine`)
- **Spatial Hash Grid Partitioning**: Uses grid cell quantization `(int(min_x / cell_size), int(min_y / cell_size))` with default cell size (500.0) for $O(1)$ fast-lookup candidate extraction.
- **Viewport Culling**: Evaluates candidate bounding boxes against viewport bounding box `(vx_min, vy_min, vx_max, vy_max)` with optional `lod_filter` (0=full, 1=medium, 2=collapsed).
- **K-Nearest Neighbors (KNN)**: Calculates Euclidean distance to surrounding nodes with `max_distance` thresholding for smart auto-wiring & contextual node placement.
- **Bounding Box Computation**: Computes unified bounding box `(min_x, min_y, max_x, max_y, width, height)` across arbitrary subsets of nodes.

### Collaboration Arbiter (`CanvasCollaborationArbiter`)
- **Node Lock Management**: Exclusive node locking during node drag / editing with TTL (default 15s), re-entrant ownership checks, and race-condition prevention.
- **Presence Heartbeats**: Buffers active collaborator positions, selected node arrays, viewport rectangles, and active tools.
- **Cursor Delta Stream**: Buffers real-time cursor interaction events with auto-pruning of stale events.
- **Stale Presence Pruning**: Auto-cleans expired presence records and releases orphaned node locks when collaborators disconnect or heartbeat fails.

### AI Node Weaver (`CanvasAINodeWeaver`)
- **Contextual Subflow Synthesis**: Decomposes user prompts into taxonomical workflow steps (`trigger`, `condition`, `transformer`, `action`, `database`, `output`).
- **Collision-Free Placement**: Automatically computes origin coordinates placed adjacent to rightmost context nodes (`max_x + spacing * 2`) to avoid visual overlap.
- **Smart Auto-Wiring**: Automatically establishes directed edges connecting context nodes to newly generated subflows.
- **Semantic Grouping**: Calculates tight bounding boxes around generated clusters and wraps them in a `CanvasSemanticGroup`.

### History & Time-Travel Engine (`CanvasHistoryTimeTravelEngine`)
- **Point-in-Time Snapshots**: Immutable history stack maintaining full canvas state or delta diffs.
- **Undo / Redo Stack Navigation**: Bidirectional cursor navigation with automatic truncation of redo futures upon new mutations.
- **Branching & Merging**: Named branches with support for `theirs` (full replace) and `union` (ID-deduplicated node/edge merge) merge strategies.

---

## 3. REST API & WebSocket Multiplexer Architecture (`apps/api/routers/`)

### FastAPI REST Router (`canvas_v3_router.py`)
- **Base Route**: `/api/v3/canvas`
- **Spatial Indexing & Culling**:
  - `POST /{canvas_id}/spatial/index`: Upsert bounding boxes into the Spatial Index Grid.
  - `POST /{canvas_id}/spatial/query`: Query visible elements inside viewport bounding box.
  - `POST /{canvas_id}/spatial/nearest`: Query $k$-nearest nodes with Euclidean cutoff.
- **Concurrency & Presence**:
  - `POST /{canvas_id}/lock/acquire` & `POST /{canvas_id}/lock/release`: Concurrency lock lifecycle with TTL and re-entrancy.
  - `POST /{canvas_id}/presence/heartbeat` & `GET /{canvas_id}/presence/active`: Active collaborator heartbeat registry.
- **AI Synthesis & History**:
  - `POST /{canvas_id}/ai/generate-subflow`: Contextual subflow synthesis.
  - `POST /{canvas_id}/history/snapshot`, `POST /{canvas_id}/history/undo`, `POST /{canvas_id}/history/redo`: Time-travel version controls.

### Real-Time WebSocket Multiplexer (`canvas_v3_ws.py`)
- **Endpoint**: `/api/v3/ws/canvas/{canvas_id}`
- **Protocol Dispatch**: Handles `PRESENCE_HEARTBEAT`, `CURSOR_STREAM`, `LOCK_ACQUIRE`, `LOCK_RELEASE`, `VIEWPORT_PAN`, `PING/PONG`.
- **Broadcasting & Echo Suppression**: Excludes the sending client during real-time delta broadcasts to eliminate client-side jitter.
- **Pydantic v2 Hygiene**: Use `.model_dump()` instead of deprecated `.dict()` for serializing spatial index and node payloads across endpoints.
