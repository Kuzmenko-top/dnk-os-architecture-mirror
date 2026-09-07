# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/canvas_swarm_websocket_bridge_protocol.md"
# purpose: "Phase 1 Canvas Swarm WebSocket Bridge & Real-Time Node Execution Protocol Specification."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🌉 Phase 1 Canvas Swarm WebSocket Bridge Protocol

## 1. Overview
The Canvas Swarm WebSocket Bridge establishes bi-directional, real-time communication between the React Flow canvas (`apps/web/store/canvasStore.ts`, `ConnectedCanvasEngine.tsx`) and the multi-agent backend (`core/swarm_engine.py`, `core/orchestrator/swarm_coordinator.py`, `apps/api/routers/swarm_ws.py`).

## 2. WebSocket Endpoints
- Canonical Multiplex Endpoints:
  - `ws://<host>:8000/ws`
  - `ws://<host>:8000/api/ws`
  - `ws://<host>:8000/ws/swarm`
- Collaborative Canvas V3 Tunnel:
  - `ws://<host>:8000/ws/canvas/v3/{canvas_id}`

## 3. Wire Protocols & Event Schemas

### 3.1 Inbound Task Execution (`TASK_EXECUTE` / `task_execute`)
Sent from the canvas UI when a user or upstream node triggers an agent task:
```json
{
  "type": "TASK_EXECUTE",
  "nodeId": "node-shopify-audit-01",
  "taskType": "dnk_shopify",
  "prompt": "Audit product liquid schema and checkout speed",
  "context": {
    "projectId": "proj-reburn-001",
    "brand": "ReBurn",
    "userSoul": {
      "user_name": "Maksym",
      "brand_values": "Premium Smokehouse & Outdoor Gear",
      "communication_style": "direct_tactical"
    }
  }
}
```

### 3.2 Outbound Node State Transitions (`TASK_STATUS`)
Broadcast to the canvas to drive UI spinners, borders, and status tags:
```json
{
  "type": "TASK_STATUS",
  "node_id": "node-shopify-audit-01",
  "status": "thinking",
  "progress": 0.15,
  "trace_id": "trace-wf-20260904-a1b2c3d4",
  "timestamp": "2026-09-04T12:00:00Z"
}
```
Valid FSM Status Cycle:
`idle` ➔ `thinking` ➔ `running` ➔ `completed` (or `error`).

### 3.3 Outbound Agent Streaming Logs (`AGENT_LOG` / `SWARM_LOG`)
Streamed to `StitchAgentLog.tsx` for real-time visibility:
```json
{
  "type": "AGENT_LOG",
  "node_id": "node-shopify-audit-01",
  "level": "info",
  "message": "Analyzing theme AST and verifying Liquid templates...",
  "timestamp": "2026-09-04T12:00:02Z"
}
```

## 4. Subsystem Invariants

### 4.1 UserSoul Context Injection
Before dispatching to `swarm_coordinator.dispatch_parallel` or `swarm_engine.execute_node_task`, the endpoint imports `core.user_soul.UserSOUL` and merges user preferences, tone of voice, and brand constraints into the task payload.

### 4.2 Langfuse Tracing & Accounting Telemetry
Every task execution generates a unique `trace_id` (`trace-wf-...`) and logs tokens, USD cost, and execution duration in milliseconds (`int(duration_ms)`) via `AccountingEngine.log_workflow_telemetry`.

### 4.3 Error Distillation & Fail-Safe Resiliency
- Inbound router imports must guard against missing optional flow modules (e.g., `try: from core.flows... except ImportError`) to prevent package import failures.
- Runtime exceptions within WebSocket tasks must pass through `core.distiller.distiller_engine.ErrorDistiller` and emit structured `TASK_STATUS` (`status: "error"`) without terminating the WebSocket session.

## 5. CanvasRuntimeBridge Hydration & Event Streaming

### 5.1 Dual-Bus Event Publishing
In `apps/api/routers/swarm_ws.py`, `CanvasRuntimeBridge` connects the WebSocket gateway to `RuntimeEventBus` and Redis Pub/Sub:
```python
bridge = get_canvas_bridge()
bridge.publish_node_created(
    node_id=node_id,
    node_type=task_type,
    execution_id=trace_id,
    canvas_id=canvas_id,
    thread_id=thread_id,
    tenant_id=tenant_id,
    workspace_id=workspace_id,
)
```
Lifecycle transitions:
- `node.created`: Published on initial task reception via `publish_node_created`.
- `node.started`: Published on pipeline execution start via `publish_node_executed(status="started", event_type="node.started")`.
- `node.completed`: Published on pipeline success via `publish_node_executed(status="completed", event_type="node.completed")`.
- `node.error`: Published in exception handler via `publish_node_executed(status="error", event_type="node.error")`.

### 5.2 Real-Time WebSocket Event Broadcast Loop
`SwarmConnectionManager` runs `_event_broadcast_loop()`, subscribing to `bridge.event_bus.subscribe(execution_id="*", tenant_id="*", workspace_id="*")`:
- Receives all `RuntimeEvent` objects.
- Formats payload as `{"type": "RUNTIME_EVENT", "event": event.to_dict()}`.
- Broadcasts to all active WebSocket clients.

### 5.3 Thread-Safe Loop Enqueue Invariant
When delivering events to an `asyncio.Queue` across different threads or event loops via `q_loop.call_soon_threadsafe`:
- **Never** enclose loop-checking recursion inside the queued callback (e.g., `_enqueue` checking `curr_loop != q_loop`).
- Use an isolated put action `_put()` that strictly calls `queue.put_nowait(event)` to prevent infinite recursion scheduling loops.

### 5.4 Monotonic Sequence Numbering & Execution Keying
- `sequence_number` must strictly monotonically increase (1, 2, 3...) per `execution_id` or `thread_id`.
- `CanvasRuntimeBridge._next_sequence(thread_id)` maintains counters keyed by `thread_id or execution_id`. This prevents cross-thread sequence collisions across concurrent swarm pipelines.

### 5.5 Offline Resiliency & Redis Fallback Strategy
- `CanvasRuntimeBridge` implements resilient dual-channel dispatch:
  1. `RuntimeEventBus.publish(event)` — in-memory bus for local WebSocket broadcasting.
  2. `_publish_to_redis(event)` — distributed pub/sub.
- In offline development, headless CI test environments, or Redis connection downtime, Redis publish exceptions are swallowed silently, preserving local in-memory event delivery and WebSocket client streams without disruption.

### 5.6 Canvas State Synchronization Events
- `publish_graph_snapshot` (`canvas.graph_snapshot`): Transmits full node and edge topologies for reactive client canvas state hydration.
- `publish_selection_batch` (`canvas.selection_batch`): Broadcasts multi-node selections, enabling synchronized multi-user highlighting and swarm agent focus tracking.

### 5.7 Async WebSocket Bridge Verification Testing
When authoring pytest verification suites (`tests/verification/test_swarm_canvas_bridge_ws.py`):
- Avoid blocking `client.websocket_connect()` synchronous loops when testing background task pipelines.
- Inject a fresh or mocked `CanvasRuntimeBridge` via `set_canvas_bridge()` to isolate unit tests from production singleton state.
- Validate status emissions against standard DNK wire contracts (`idle` ➔ `thinking` ➔ `running` ➔ `completed` / `error`).


