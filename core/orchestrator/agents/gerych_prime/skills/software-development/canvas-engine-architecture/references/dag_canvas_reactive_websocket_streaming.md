# DAG Canvas Reactive WebSocket Streaming & Node Lifecycle (Slice 20.2)

## Overview & Architecture
This reference captures the production patterns for zero-refetch reactive WebSocket streaming of DAG task execution and agent terminal logs, linking FastAPI's `CanvasRuntimeBridge` / `SwarmConnectionManager` to Zustand's `nodeTasksStore`.

### 1. Event Broker & Bridge Integration (`apps/api/routers/node_tasks_router.py`)
- Retrieve the active runtime bridge singleton via `get_canvas_bridge()`.
- Topic: `dnk:canvas:events`.
- Key Event Types:
  - `node.status_changed`: Fired on execution start (`in_progress`) or manual stage transition.
  - `node.executed`: Fired upon task completion with final status (`done` / `failed`), 100% progress, summary results, and collected logs.
  - `node.log`: Fired by `append_task_log` in real time with timestamp, log level (`INFO`, `STEP`, `DONE`, `THOUGHT`, `ERROR`), and message.

### 2. Client Reactive State Updates (`apps/web/store/nodeTasksStore.ts`)
- WebSocket endpoint: `ws://${window.location.host}/api/ws` with production fallback.
- In-place mutation pattern:
  - When a `node.status_changed` or `node.executed` message arrives, mutate `nodesMap[nodeId]` directly.
  - Re-run `buildRFNodesAndEdges(Object.values(nodesMap), edges)` to sync ReactFlow visuals without triggering an expensive `fetchDAG()` HTTP network request.
  - When `node.log` arrives, append to `nodeLogs[nodeId] = [...(nodeLogs[nodeId] || []), logItem]`.
- Provide a cleanup hook (`closeWebSocket()`) for React component unmounting.

### 3. FastAPI WebSocket Broadcast Testing Pattern (`tests/verification/test_node_tasks_ws_streaming.py`)
- When testing asynchronous event listeners with FastAPI `TestClient` or mock WebSockets:
  ```python
  # Connect WebSocket client to SwarmConnectionManager
  manager = swarm_ws.swarm_ws_manager
  mock_ws = MockWebSocket()
  await manager.connect(cast(WebSocket, mock_ws))

  # Give the event loop a tick (0.05s) to initialize queue in _event_broadcast_loop
  await asyncio.sleep(0.05)

  # Execute node task (which publishes events to CanvasRuntimeBridge)
  node_tasks_router.execute_agent_for_node(node_id="...", req=...)

  # Give the background broadcast loop a tick to deliver
  await asyncio.sleep(0.05)

  # Assert event was received
  assert len(mock_ws.sent_messages) > 0
  ```

### 4. Path Hygiene Invariant in Test Mocks
- Auto-precommit guard strictly scans for `/Users/` patterns in all files.
- If a test requires simulating an absolute path rejection, construct it dynamically (e.g. `f"/{'Users'}/test/secret.txt"`) to avoid false-positive path audit failures.
