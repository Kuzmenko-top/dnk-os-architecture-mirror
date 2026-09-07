# PostgreSQL 16 (hub_memory) Delta Sync, WebSocket Collaboration & Offline Hydration

## Architectural Pattern Overview
When scaling Canvas Engine beyond ephemeral LocalStorage to enterprise multi-tenant databases, replace full-scene snapshots with atomic delta synchronization, WebSocket peer broadcasting, and IndexedDB offline hydration.

## 1. Database Schema (`hub_memory`)
- **`canvas_documents`**: Root document tracking `canvas_id`, `workspace_id`, `scene_state` (full JSONB scene), `current_revision` (monotonic int), and `scene_checksum` (SHA-256).
- **`canvas_revisions`**: Immutable snapshot log storing `revision_id`, `canvas_id`, `delta` (JSONB), and `snapshot` for time-travel undo beyond the active browser session.

## 2. Atomic Delta Contract
Instead of serializing the entire scene graph on every node drag or parameter edit, serialize only the mutated subset:
```json
{
  "upsert_nodes": [{"id": "node_1", "type": "taskNode", "position": {"x": 100, "y": 200}, "data": {}}],
  "delete_node_ids": ["node_legacy"],
  "upsert_edges": [{"id": "edge_1", "source": "node_1", "target": "node_2"}],
  "delete_edge_ids": [],
  "viewport": {"x": 0, "y": 0, "zoom": 1.0},
  "summary": "Updated node_1 position"
}
```

## 3. Conflict Resolution (Last-Write-Wins + Revisions)
- Upon delta arrival, apply dictionary merge against current `scene_state`.
- Calculate new SHA-256 `scene_checksum`.
- Monotonically increment `current_revision = current_revision + 1`.
- Append revision entry to `canvas_revisions`.

## 4. Dual-Path Real-Time Collaboration
- **HTTP POST `/api/v1/canvases/{id}/delta`**: Durable persistence path. Triggers background WebSocket broadcast to peer clients.
- **WebSocket `/api/v1/ws/canvas/{id}`**: Ephemeral peer collaboration for active cursor movement (`cursor_move`), selection highlights, and low-latency delta relays.
- Peer clients apply incoming deltas via `applyRemoteDelta` directly to their local ReactFlow/Zustand store without re-broadcasting.

## 5. Offline-First Hydration (IndexedDB Fallback)
- On network failure or offline mode, deltas are queued in IndexedDB (`dnk_canvas_offline_db`).
- On canvas load, attempt server fetch; if network unreachable, hydrate seamlessly from IndexedDB cached document state.
- Once connectivity is restored, drain and flush pending deltas to the server.
