# Canvas & Generative UI Real-Time Synchronization Patterns

## Overview
When scaling real-time collaboration from standard document/block editors to infinite visual canvases (such as DNK-CANVAS-002), specific synchronization patterns and constraints emerge.

## 1. Canvas Viewport & Coordinate Space Synchronization
- **Viewport State**: Maintain pan `(viewport_x, viewport_y)` and `zoom` per collaborator locally, but broadcast viewports during shared presentation / "follow user" modes (`canvas:follow_user`).
- **Cursor Normalization**: Live cursor coordinates must always be broadcast in **world-space canvas coordinates** `(world_x, world_y)`, not client screen pixel coordinates. Clients transform incoming peer cursors to their local viewport:
  ```ts
  screenX = (worldX - viewportX) * zoom;
  screenY = (worldY - viewportY) * zoom;
  ```

## 2. Multi-Level Node Locking vs Fine-Grained OCC
- **Pessimistic Node Drag / Edit Locks**: Acquire lightweight node locks on `pointerdown` / `node:drag_start` (`dnk:lock:canvas:{canvas_id}:node:{node_id}`) with short TTL (e.g. 5-10s) auto-extended during dragging.
- **Optimistic Concurrency Control (OCC) for Graph Mutations**: Batch node coordinate commits and edge additions with OCC `expected_version`. Case-insensitive matching (`op_type.upper()`) for incoming patch operation types (`NODE_ADD`, `NODE_MOVE`, `NODE_UPDATE`, `NODE_DELETE`, `EDGE_ADD`, `EDGE_DELETE`) ensures robust WebSocket message processing regardless of payload casing.
- **Conflict Resolution on Node Position Overlap**: If two users move connected nodes concurrently, apply non-destructive 3-way graph merge, prioritizing the latest timestamp with deterministic `user_id` tie-breaking.

## 3. Generative UI Component Sandboxing & Live State
- **Shadow DOM & IFrame Sandboxing**: When AI agents stream generative UI components (React/Vue/Svelte) onto canvas nodes, isolate execution context in sandboxed iframes (`sandbox="allow-scripts"`) or Web Components with Shadow DOM to prevent CSS leaks and global scope pollution.
- **Props Schema & Code Metadata**: Component metadata exports clean `source_code`, `props_schema`, and `default_props`. Validate incoming component prop updates against `props_schema` before broadcasting state mutations to peers.

## 4. Multi-Agent Flow Propagation
- **Supervisor-Worker Canvas Nodes**: Agent execution nodes report progress, tool calls, and artifact generation over the canvas WebSocket channel (`agent:action_stream`, `agent:node_status`).
- **Live Edge Animation**: Active data flow along edges (`CanvasEdgeModel`) is signaled via ephemeral WebSocket frames (`edge:pulse`, `edge:data_transfer`) without persisting unnecessary database mutations for transient animation states.
