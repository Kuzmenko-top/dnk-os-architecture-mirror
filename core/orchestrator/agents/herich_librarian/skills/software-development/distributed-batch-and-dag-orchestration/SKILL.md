---
name: distributed-batch-and-dag-orchestration
description: "Use when building batch engines, DAG workflows, and DLQs."
category: software-development
author: "DNK OS Core Team"
license: "MIT"
version: "1.0.0"
metadata:
  hermes:
    tags: ["batch", "dag", "orchestration", "worker-pool", "dlq", "resilience"]
    related_skills: ["fastapi-prometheus-observability", "workspace-realtime-collaboration"]
---

# Distributed Batch Processing & DAG Workflow Orchestration

## When to Use
- Implementing distributed background task queues with asynchronous execution.
- Designing Directed Acyclic Graph (DAG) workflows with topological sorting and cycle detection.
- Managing distributed worker pools with heartbeat health checks, slot-based concurrency, and capability matching.
- Adding resilience mechanisms: exponential backoff with jitter, retry policies, and Dead Letter Queue (DLQ) triage.

## Overview
A comprehensive guide and proven architecture pattern for implementing distributed task queues, DAG workflow engines, worker pool capacity controllers, exponential backoff retries, and Dead Letter Queue (DLQ) resilience.

---

## 🏗️ Core Architecture Components

```
                    ┌───────────────────────────┐
                    │     REST API Router       │
                    │  (/api/v1/batch/jobs/...) │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │    BatchEngineService     │ ◄─── TraceContext / @trace_span
                    │ (Job queue & DAG runner)  │
                    └──────┬──────────────┬─────┘
                           │              │
             ┌─────────────▼────┐    ┌────▼─────────────┐
             │  DAG Scheduler   │    │   Worker Pool    │
             │ (Topological sort│    │ (Slot allocation,│
             │ cycle detection) │    │ heartbeat status)│
             └──────────────────┘    └────┬─────────────┘
                                          │
                                     (Failure / Timeout)
                                          │
                                          ▼
                             ┌──────────────────────────┐
                             │ BatchCoordinatorService  │
                             │ - Exponential backoff    │
                             │ - Heartbeat watchdog     │
                             │ - Dead Letter Queue (DLQ)│
                             └──────────────────────────┘
```

---

## 🔄 1. DAG Dependency Validation & Topological Sorting

Before executing a Directed Acyclic Graph (DAG) workflow:
1. **Cycle Detection (DFS / 3-Coloring or Kahn's Algorithm)**:
   - Mark nodes as `VISITING` (in current recursion stack) and `VISITED`.
   - If a neighbor is in `VISITING`, raise a cycle validation error (`ValueError("Cyclic dependencies detected in workflow")`).
2. **Topological Order Generation**:
   - Compute in-degrees for all nodes.
   - Nodes with zero dependencies run first (parallelizable).
   - Once all parent nodes complete with `COMPLETED` status, trigger dependent child tasks.

```python
def validate_no_cycles(nodes: list[DAGNode]) -> None:
    adj = {node.node_id: list(node.dependencies) for node in nodes}
    visited = {}  # node_id -> 0: unvisited, 1: visiting, 2: visited

    def dfs(node_id: str):
        visited[node_id] = 1
        for dep in adj.get(node_id, []):
            if dep not in visited:
                continue
            if visited[dep] == 1:
                raise ValueError(f"Cyclic dependency detected: {node_id} -> {dep}")
            if visited[dep] == 0:
                dfs(dep)
        visited[node_id] = 2

    for node in nodes:
        if visited.get(node.node_id, 0) == 0:
            dfs(node.node_id)
```

---

## ⚡ 2. Worker Pool & Concurrency Slots

- **Heartbeat Contract**: Workers report status (`cpu_usage_percent`, `memory_usage_mb`, `active_tasks_count`) periodically (e.g. every 10s-30s).
- **Slot Capacity Routing**: Tasks are dispatched only to active workers whose `active_tasks_count < concurrency_slots`.
- **Supported Task Types**: Workers can register supported task capabilities (e.g. `["extract", "ai_inference", "video_encode"]`).

---

## 🛡️ 3. Exponential Backoff & Dead Letter Queue (DLQ)

1. **Jittered Exponential Backoff**:
   $$\text{delay} = \min(\text{max\_backoff}, \text{base\_delay} \times 2^{\text{retry\_count}-1}) \times (1 \pm \text{jitter})$$
2. **DLQ Eviction & Replay**:
   - When a task exhausts `max_retries` or fails with a non-recoverable error, it is recorded in `BatchDeadLetterRecord`.
   - Expose REST endpoints to inspect DLQ records (`GET /api/v1/batch/dlq`), replay them (`POST /api/v1/batch/dlq/{id}/replay`), or discard them.
3. **Heartbeat Watchdog & Auto-Requeuing**:
   - Background coordinator checks for workers with `last_heartbeat_at < now - heartbeat_timeout_seconds`.
   - Mark worker as `OFFLINE`.
   - Find all tasks in `RUNNING` state assigned to that dead worker and reset their status to `PENDING` (`assigned_worker_id=None`) so healthy workers can pick them up.

---

## ⚠️ 4. Visual Canvas & DAG Serialization Pitfalls (Pydantic V2 & FastAPI Routing)

1. **Pydantic V2 Circular Reference Trap on In-Memory DAG Singletons**:
   - When templates or canonical DAGs are registered in memory and mutated during execution (e.g. updating `node.status` or `node.last_output` in place), reusing or serializing the same node/edge object references causes Pydantic V2's serializer to raise `ValueError: Circular reference detected (id repeated)`.
   - *Fix*: Always return deep copies from template registries:
     ```python
     def get_template(self, template_id: str) -> Optional[WorkflowDAG]:
         dag = self._templates.get(template_id)
         return dag.model_copy(deep=True) if dag else None
     ```

2. **FastAPI Route Precedence on Parameterized Paths**:
   - In FastAPI `APIRouter`, literal static routes MUST be declared BEFORE path parameter templates:
     - Correct order: `/workflows/templates` -> `/workflows/{workflow_id}` -> `/{canvas_id}`.
     - If `/{canvas_id}` is declared first, requesting `/workflows/templates` will capture `"workflows"` as `canvas_id` and return `404 Not Found`.

3. **APIRouter Prefix Doubling in Tests**:
   - If an `APIRouter(prefix="/api/v1/canvas")` already defines its own prefix, mounting it with `app.include_router(router, prefix="/api/v1/canvas")` will create `/api/v1/canvas/api/v1/canvas/...`. Mount it without redundant prefixes.

---

## 🧪 Verification & Testing Strategy

1. **Unit Models**: Test state transitions, enum validation, cycle rejection, and serialization.
2. **Engine Async Tests**: Test single task execution, DAG parallel branch execution, and error routing.
3. **Coordinator Tests**: Test backoff formula, worker timeouts, task requeue, and DLQ purge.
4. **Integration Router Tests**: Use `httpx.AsyncClient` with `ASGITransport(app=app)` to test end-to-end REST lifecycle.
