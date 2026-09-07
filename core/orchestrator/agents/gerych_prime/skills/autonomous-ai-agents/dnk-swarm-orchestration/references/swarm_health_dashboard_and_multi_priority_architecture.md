# 🩺 Swarm Health Dashboard & Multi-Priority Unified Observability Protocol (HEALTH-DASH-001)

## 1. Executive Summary & Purpose
This protocol specifies the canonical architecture and operating invariants for the **DNK OS Swarm Health Dashboard & Observability Engine (v1.0)**, synthesized across the 4 foundational Mentor Architectural Priorities. It provides real-time, low-latency, cross-subsystem diagnostics bridging background worker coordinators, anomaly watchdogs, spend accounting, and frontend spatial canvas visualization.

---

## 2. The 4 Mentor Architectural Priorities

```
                                  [DNK OS Swarm Hub]
                                           │
          ┌────────────────────────────────┼────────────────────────────────┐
          ▼                                ▼                                ▼
  [Priority 1: Push]             [Priority 2: Merge]              [Priority 3: HUD]
Reactive FileWatcher            OCC 3-Way Graph Merge           Live Swarm Status HUD
(Watchdog -> WS Event)         (Base + Server + Client)        (14 Agent Badges/Colors)
          │                                │                                │
          └────────────────────────────────┼────────────────────────────────┘
                                           │
                                           ▼
                                 [Priority 4: Health]
                              Swarm Health Engine & Stream
                              (/api/v1/health/swarm + WS)
                                           │
                ┌──────────────────────────┼──────────────────────────┐
                ▼                          ▼                          ▼
     [Gerych Swarm Coord]         [Session Sentinel]         [Accounting Engine]
      14 Workers + Hex Colors     Anomalies & Self-Heal     Token Burn & SpendGuard
```

### 2.1 Priority 1: Reactive FileWatcher for Canvas Bridge (`PUSH_NOT_POLL`)
- **Problem**: Polling the filesystem for canvas mutations creates unnecessary CPU/disk churn and noticeable latency in multi-agent environments.
- **Solution**: Background `watchdog` observer (`FileSystemEventHandler`) monitoring canvas JSON graph files (`data/node_task_graph.json` or custom workspaces).
- **Mechanism**: File updates trigger real-time WebSocket push notifications (`CANVAS_FILE_MUTATED` / `CANVAS_RELOAD_REQUIRED`) to connected clients via `CanvasBridgeConnectionManager.broadcast_event()`.

### 2.2 Priority 2: OCC 3-Way Structural Merge Engine (`OCC_3WAY_MERGE`)
- **Problem**: Concurrent edits from UI human operators and autonomous background swarm agents lead to silent graph overwrite conflicts (Lost Update problem).
- **Solution**: Optimistic Concurrency Control (OCC) with 3-way structural graph merging:
  - Compares `base_state`, `current_state` (server), and `incoming_state` (mutation).
  - Resolves node additions, modifications, and deletions at the node/edge attribute level.
  - Automatically merges non-conflicting disjoint mutations; flags overlapping conflicting edits without destructive overwrites.

### 2.3 Priority 3: Live Swarm HUD on React Flow Canvas (`SWARM_LIVE_HUD`)
- **Problem**: Operators cannot visually discern which agent is executing what node or what stage the swarm workflow is currently in.
- **Solution**: Spatial WebSocket telemetry streaming stage lifecycle events (`SWARM_STATUS_UPDATE`):
  - 14 specialized workers mapped to SSOT hex and canvas color badges (`SWARM_WORKER_COLORS`).
  - Active nodes pulse with the assigned agent's signature theme on the React Flow canvas.
  - Telemetry payload includes `task_id`, `assigned_agent`, `event_type` (`started`, `progress`, `completed`, `failed`), and progress percentage.

### 2.4 Priority 4: Unified Swarm Health Dashboard & WebSocket Stream (`SWARM_HEALTH_DASH`)
- **Problem**: Diagnostic metrics (worker status, Sentinel anomalies, token burn, WebSocket connections, system resources) were scattered across disparate CLI tools, logs, and internal modules.
- **Solution**: Canonical `SwarmHealthEngine` (`core/orchestrator/swarm_health.py`) offering single-point REST (`/api/v1/health/swarm`) and WebSocket (`/api/v1/health/swarm/ws`) diagnostic feeds.

---

## 3. SwarmHealthEngine Subsystem Integrations

### 3.1 Swarm Workers Status (`get_workers_health`)
- Queries `GerychSwarmCoordinator(agents_dir=...).list_agents()`.
- Enriches all 14 agents with `SWARM_WORKER_COLORS`: HEX badge, canvas color, role, and capabilities.
- Computes `ready_count`, `busy_count`, and provides both `total_agents` and `total_workers` for multi-client compatibility.

### 3.2 Sentinel Anomaly Watchdog (`get_sentinel_health`)
- Inspects `data/sentinel_alerts.json` and counts active anomalies.
- Classifies into `critical_alerts_count` (e.g. `FALSE_COMPLIANCE`, `AUTH_ERROR`) and `warning_alerts_count`.
- Scans `docs/plans/self_heal/` for unresolved task specs (`TASK-DNK-SELFHEAL-*.md`).
- Returns status: `clean` (0 alerts), `critical` (>=1 critical alert), or `warning`.

### 3.3 Token Accounting & SpendGuard (`get_accounting_health`)
- Integrates with `AccountingEngine(log_path=...)`.
- Aggregates `total_tokens`, `total_cost`, request count, and cache hit metrics.
- Calculates `spend_saturation_pct` against configurable `spend_limit_usd` (default: $10.00).
- Emits status: `normal` (<80%), `near_limit` (80-100%), or `exceeded` (>100%).

### 3.4 Canvas Bridge WebSocket Telemetry (`get_canvas_bridge_health`)
- Interrogates `CanvasBridgeConnectionManager.get_stats()`.
- Reports active client connections, tracked canvases, and cumulative `total_events_broadcast`.
- Returns status: `streaming` (active connections > 0) or `idle`.

### 3.5 System Resources & Overall Health Calculation
- Gathers host OS metrics: process RSS memory in MB, CPU utilization percentage, and system uptime.
- Computes `overall_status`:
  - `unhealthy`: If critical Sentinel alerts exist, SpendGuard limit is exceeded, or 0 workers ready.
  - `degraded`: If warning alerts exist or SpendGuard is near limit (>80%).
  - `healthy`: All subsystems operating within normal parameters.

---

## 4. REST & WebSocket API Specification

### 4.1 REST Endpoint: `GET /api/v1/health/swarm` (and `GET /health/swarm`)
**Query Parameters**:
- `workspace_id` (string, default: `"ws-alpha-001"`): Target workspace partition.
- `details` (bool, default: `true`): Include full worker cards vs count summary.
- `spend_limit_usd` (float, optional): Custom session budget threshold.

**Sample JSON Response**:
```json
{
  "overall_status": "healthy",
  "timestamp": "2026-09-06T15:00:00.000000Z",
  "status_reasons": [],
  "workspace_id": "ws-alpha-001",
  "workers": {
    "total_agents": 14,
    "total_workers": 14,
    "ready_count": 14,
    "ready_workers": 14,
    "busy_count": 0,
    "agents": [...]
  },
  "sentinel": {
    "status": "clean",
    "active_alerts_count": 0,
    "critical_alerts_count": 0,
    "warning_alerts_count": 0,
    "pending_self_heal_plans": 0
  },
  "accounting": {
    "status": "healthy",
    "total_tokens": 124500,
    "total_cost": 0.42,
    "spend_limit_usd": 10.0,
    "spend_saturation_pct": 4.2
  },
  "canvas_bridge": {
    "status": "streaming",
    "active_connections": 1,
    "total_events_broadcast": 42
  },
  "system_resources": {
    "memory_rss_mb": 142.5,
    "cpu_percent": 3.2,
    "uptime_seconds": 3600.0
  }
}
```

### 4.2 WebSocket Stream: `WS /api/v1/health/swarm/ws`
- **On Connect**: Immediately broadcasts initial `SWARM_HEALTH_SNAPSHOT`.
- **Client Actions**:
  - `{"action": "refresh"}` or `{"action": "GET_STATUS"}`: Triggers an updated `SWARM_HEALTH_UPDATE`.
  - `{"action": "ping"}`: Immediate `{"type": "PONG", "timestamp": "..."}` response.

---

## 5. Verification Invariants & Pitfalls

1. **Dual Endpoint Registration**: Always register the health endpoint both on `health_router.py` (under `/api/v1/health/swarm`) and `health.py` (`/health/swarm`) to ensure resilience regardless of which router prefix is mounted in `apps/api/main.py`.
2. **Contract Key Synonymity**: Provide synonymous keys (`total_agents` and `total_workers`, `ready_count` and `ready_workers`, `system_resources` and `system_metrics`) so heterogeneous legacy and modern consumers never suffer from `KeyError`.
3. **Safe File Absence Defaults**: If `sentinel_alerts.json` or accounting database does not yet exist on disk, return clean/empty structures rather than raising `FileNotFoundError`.
4. **End-to-End TypeScript Contracts**: All API structures must have 100% synchronized TypeScript types in `apps/web/types/canvasBridge.ts`, validated via `tsc -p apps/web/tsconfig.json --noEmit`.

---

## 6. Concurrency-Safe Atomic Storage Engine (`core/atomic_store.py`)

### 6.1 The Concurrent Telemetry Race Condition
When 14 specialized swarm agents execute parallel pipelines, multiple background threads simultaneously write to shared JSON files:
- `data/sentinel_alerts.json` (Watchdog alerts)
- `data/accounting_log.json` (SpendGuard token ledger)
- `apps/api/visual_shell_db.json` (Canvas graph state)

A naive `open(path, 'w')` causes silent file truncation, partial overwrites, and `json.decoder.JSONDecodeError` on concurrent reads.

### 6.2 Architecture: POSIX `fcntl` Locking + Atomic Replace
```python
# Canonical read pattern: Shared Lock (LOCK_SH)
with open(path, "r", encoding="utf-8") as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
    try:
        return json.load(f)
    finally:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

# Canonical write pattern: Exclusive Lock (LOCK_EX) + Tempfile + Atomic Replace
with open(lock_path, "w") as lock_file:
    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
    try:
        # Write to temporary file on same filesystem
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as tmp:
            json.dump(data, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_path = tmp.name
        os.replace(temp_path, path)  # POSIX atomic swap
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
```
- **Helper functions**: `atomic_json_read(path, default=None)`, `atomic_json_write(path, data)`, `atomic_json_update(path, mutator_fn, default=None)`.

---

## 7. Active Swarm Auto-Healing Protocol

### 7.1 Reactive Healing vs Passive Alerting
Passive dashboards only flag degraded states. The Active Auto-Healing protocol empowers the operator and automated watchdogs to self-resolve anomalies:
1. **REST Action**: `POST /api/v1/health/swarm/heal` with body `{"alert_id": "...", "resolution_note": "..."}`.
2. **WebSocket Action**: `{"action": "heal", "alert_id": "..."}` transmitted over `/api/v1/health/swarm/ws`.
3. **Execution**:
   - `SwarmHealthEngine.resolve_or_heal_alert()` marks alert status `resolved`.
   - Closed alerts are atomically archived to `data/sentinel_alerts_archive.json`.
   - Matching self-healing markdown specs in `docs/plans/self_heal/` are moved to `docs/plans/self_heal/archive/`.
   - Immediate push broadcast of updated `SWARM_HEALTH_UPDATE` to all connected clients.

---

## 8. Resilient WebSocket Bridge & Client Architecture

### 8.1 Client-Side Resilience Invariants (`apps/web/lib/api/canvas_bridge_client.ts`)
- **Exponential Backoff**: On socket disconnection, delay reconnections incrementally (1.5s -> 3s -> 6s -> max 10s) with jitter.
- **Outgoing Event Buffering**: During server restarts or network blips, mutations and merge requests are enqueued in an in-memory ring buffer (up to 100 events) and drained automatically once the link re-establishes.
- **Heartbeat Guard**: Ping/pong interval every 25 seconds ensures dead TCP sockets are detected and reconnected before state drift occurs.
