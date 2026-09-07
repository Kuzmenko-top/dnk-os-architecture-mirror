---
name: workspace-realtime-collaboration
description: "Use when implementing WebSocket sync, presence, and OCC."
version: "1.0.2"
author: "DNK-e.com Maksym"
license: "MIT"
metadata:
  hermes:
    tags: ["websocket", "realtime", "presence", "collaboration", "occ", "locking", "fastapi"]
    related_skills: ["software-development/dnk-mvp-code-standards", "software-development/fastapi-postgres-docker-connectivity"]
---

# Workspace Real-Time Collaboration & Concurrency Architecture

A class-level guide for implementing robust, multi-user real-time collaboration engines using FastAPI, WebSockets, Redis / in-memory lock managers, and Optimistic Concurrency Control (OCC).

## When to Use
- Building or extending real-time collaborative editing features in workspace/canvas applications.
- Implementing WebSocket event brokers with presence, active member tracking, and live cursor streaming.
- Adding pessimistic section locking with automatic TTL expiration or optimistic concurrency control (OCC).
- Debugging WebSocket teardown race conditions, ASGI TestClient timeouts, or state sync collisions.

## Core Architectural Pillars

### 1. Unified WebSocket Protocol (`/ws/workspaces/{id}`)
Standardize on typed JSON frame contracts for all bi-directional events:
- `workspace:sync` — Client requests full snapshot (state, current version, active peers, active locks).
- `presence:join` / `presence:leave` — Peer join and teardown notifications.
- `presence:cursor` — Low-latency cursor coordinates `(x, y, node_id)` broadcast to peers excluding sender.
- `workspace:lock` — Pessimistic lock acquisition/release per editable section/node with TTL.
- `workspace:mutation` — Optimistic mutation submission carrying `expected_version`.
- `workspace:conflict` — Conflict rejection notifications (`OCC_VERSION_MISMATCH`, `SECTION_ALREADY_LOCKED`, `SECTION_LOCKED_BY_ANOTHER_USER`).

### 2. Pessimistic Section Locking (`WorkspaceLockManager`)
- **Key Strategy:** `dnk:lock:{workspace_id}:{section_id}` with Redis `SET key val NX EX ttl` and thread-safe in-memory dictionary fallback.
- **Re-entrancy:** Allow the same `user_id` to extend TTL without throwing conflict.
- **Auto-Release on Disconnect:** Ensure connection termination immediately scans and frees all locks held by that user.

### 3. Optimistic Concurrency Control (OCC) Engine
- Verify `expected_version == current_version` prior to applying any mutation payload.
- On mismatch, perform a 3-way structural diff (`compute_3way_diff`) comparing `base`, `current` (remote), and `incoming` (local) states.
- Auto-merge non-conflicting changes (fine-grained attribute updates, non-overlapping node/edge additions) via `merge_graph_state()`.
- Detect explicit conflicts (`ConflictType`: node modification, delete vs modify, property collisions).
- Resolve conflicts manually via `resolve_conflicts_manually()` strategies (`use_incoming`, `use_current`, `use_base`, `custom`).
- Deterministic LWW tie-breaker: When timestamps are identical in Last-Write-Wins, break ties deterministically using `operation.userId > latestConflict.userId`.
- On success, atomically increment graph version (`bump_version()`) and broadcast updated state to all connected peers.

### 4. A2A Agent Action & Canvas Collaboration Integration
- In agentic canvas applications, WebSocket event brokers pass `agent_action` events alongside cursor and graph state mutations.
- Route `agent_action` events through `A2AProtocolEngine` (`MessageRouter`) using `CommunicationPattern.BROADCAST` or `SUPERVISOR_WORKER`.
- Agent execution nodes dynamically report metrics (`latency_ms`, `asr`, `tokens_used`, `status`) over the WebSocket channel to keep all connected clients' canvas state synchronized in real time.

### 4. REST RBAC & Security Gates
- **RBAC Hierarchy:** Implement `require_admin`, `require_member_or_higher`, and `can_manage_invitations` dependencies.
- **Security Gates:** Enforce Nil UUID rejection, `X-Workspace-Id` vs path match validation, and autonomous AI agent self-approval blocking.

### 5. Horizontal Scaling, Sharding & Redis Pub/Sub
- **PostgreSQL Read Replicas:** Route write operations to Master and read operations across Read Replicas via Round-Robin, falling back gracefully to Master.
- **Tenant Sharding:** Deterministically map `tenant_id` to database shards (`md5(tenant_id) % num_shards`) via `TenantShardRouter` and `TenantRouterMiddleware`.
- **Redis Cluster Slot Pinning:** Use `{workspace_id}` hash-tagging for Pub/Sub channels and locks to pin keys to a single Redis Cluster slot.
- **Cross-Node Event Bus:** Broadcast presence, cursors, locks, and OCC mutations across nodes via `RedisPubSubManager` with `origin_node` echo suppression.

### 6. Workspace Analytics & Metrics Collection
- **Unified Event Bus:** Intercept presence joins/leaves, lock contentions, OCC version conflicts, and mutations directly in the collaboration hub.
- **Time-Series Storage:** Buffer metrics with retention policies (30 days) and rollups (`1m`, `1h`, `1d`).
- **Percentiles Indexing:** Calculate p50, p95, p99 latencies using nearest-rank index `int((n - 1) * P)` for 0-indexed arrays.
- **Frontend Live Dashboard:** React hooks (`useWorkspaceAnalytics`, `useWorkspaceLiveMetrics` with heartbeat/auto-reconnect) and modular UI widgets (`LiveMetricsPulseCard`, `ActivityTimelineChart`, `PerformancePercentilesCard`, `WorkspaceUsersActivityTable`, `WorkspaceErrorsLog`).

## Critical Pitfalls & Solutions

### 1. Single-Frame Disconnect Teardown in ASGI / TestClient
* **Pitfall:** Emitting separate sequential broadcast calls (e.g. `broadcast(lock_released)` then `broadcast(presence:leave)`) inside the `except WebSocketDisconnect:` block can cause race conditions or hang ASGI test portals (like Starlette / AnyIO TestClient) when the disconnecting socket's task is being cancelled.
* **Fix:** Consolidate teardown into a single atomic frame: `presence:leave` payload carrying `released_locks: [...]` and updated `active_users: [...]`.

### 2. Dict vs Pydantic Attribute Lookups for OCC Versioning
* **Pitfall:** `st.metadata.version` fails silently or defaults to 1 when state repositories return raw dictionaries (`dict`), bypassing OCC collision checks.
* **Fix:** Safely inspect both formats:
  ```python
  if isinstance(state, dict):
      current_version = state.get("metadata", {}).get("version", 1)
  elif hasattr(state, "metadata"):
      current_version = getattr(state.metadata, "version", 1)
  ```

### 3. Selective Cursor Broadcasting
* **Pitfall:** Echoing cursor movement back to the originator causes jitter and unnecessary client re-renders.
* **Fix:** Always supply `exclude_websocket=sender_websocket` during `presence:cursor` broadcasts.

### 4. Redis Pub/Sub Background Listener & Event Loop Isolation
* **Pitfall:** Singleton Redis clients or connection pools reused across pytest tests cause `RuntimeError: Task attached to a different loop` when running function-scoped event loops. Busy-polling `get_message(timeout=...)` in background listener loops also introduces latency spikes and test timeouts.
* **Fix:** In `RedisClient.get_client()`, detect whether the active `asyncio.get_running_loop()` matches the loop the client was created in, resetting connections on loop change. For Pub/Sub consumers, consume directly via `async for msg in ps.listen():` inside the background task.

### 5. Storage Layer Key Consistency for Distributed Locks
* **Pitfall:** Mismatched key templates between Redis Cluster hash tags (`dnk:lock:{workspace_id}:{section_id}`) and in-memory fallback dictionaries cause bulk release operations (`release_all_user_locks`) to silently miss keys during tests or failovers.
* **Fix:** Use a single canonical key generation method (e.g. `_make_key(workspace_id, section_id)`) across both Redis client calls and in-memory dictionary storage.

### 6. A2A MessageRouter Return Type in Async Tests
* **Pitfall:** Asserting `delivered == int` on `MessageRouter.route()` calls fails because routing methods return lists of delivered `A2AMessage` objects rather than integer counts.
* **Fix:** Assert `isinstance(delivered, list)` and check `len(delivered)` for delivered message counts in pytest suites.

### 7. WebSocket OCC Patch Operation Type Casing Mismatches
* **Pitfall:** WebSocket payloads sent by different frontend clients or test cases may supply operation types as lower/snake_case (`node_add`) while server Enums expect uppercase (`NODE_ADD`), causing unexpected `patch_rejected` events.
* **Fix:** Normalize string case prior to Enum lookup: `op_type_str = str(patch_dict.get("op_type", "")).upper()` before validating `PatchOpType(op_type_str)`.

## Supporting Documentation
- See `references/canvas_spatial_indexing_and_ai_generation.md` for R-Tree bounding box spatial indexing, presence tracking, cursor streams, history snapshots, AI node generation requests, and semantic grouping models.
- See `references/workspace_analytics_and_metrics.md` for metrics taxonomy, retention buffer cleanup, time-bucket rollups, nearest-rank percentiles, and hub event interception.
- See `references/horizontal_scaling_and_sharding.md` for PostgreSQL Read Replicas routing, Tenant Sharding router, Redis Cluster hash tags, and cross-node Pub/Sub broadcasting.
- See `references/occ_concurrency_engine.md` for 3-way structural diff, auto-merge, conflict detection, manual resolution strategies, and version bump mechanics.
- See `references/canvas_and_generative_ui_realtime_sync.md` for world-space cursor normalization, node-level drag locking, generative UI sandboxing, and multi-agent flow propagation.
- See `references/ws_testing_and_execution.md` for virtualenv test execution directives (`uv run pytest`) and multi-client Starlette `TestClient` WebSocket fixture patterns.
- See `references/rbac_and_security_gates.md` for multi-workspace RBAC dependency tiers, header validation rules, and agent self-approval security gates.

