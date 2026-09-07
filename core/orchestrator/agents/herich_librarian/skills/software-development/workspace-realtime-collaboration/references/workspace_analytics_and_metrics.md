# Workspace Analytics, Time-Series Storage & Metrics Collection

## 1. Metrics Taxonomy
- **Workspace Activity**: `workspace:prompt_submitted`, `workspace:diff_staged`, `workspace:approval_created`, `workspace:commit_executed`, `workspace:rollback_executed`, `workspace:kill_switch_triggered`, `workspace:mutation`.
- **User Activity**: `user:login`, `user:workspace_switch`, `user:presence_join`, `user:presence_leave`.
- **Performance**: API latency, DB query latency, Redis operations latency, WebSocket latency.
- **Error & Conflicts**: 4xx/5xx responses, DB/Redis connection failures, and OCC / pessimistic lock conflicts (`OCC_VERSION_MISMATCH`, `SECTION_LOCKED_BY_ANOTHER_USER`).

## 2. In-Memory Time-Series Buffer & Retention Policy
- Implement an in-memory buffer with a rolling retention window (e.g. 30 days) for dev/test/local environments, with automated truncation of timestamps older than `now() - retention_days`.
- Support time-bucket aggregation (`1m`, `1h`, `1d`) via bucket key grouping (`%Y-%m-%d-%H` / `%Y-%m-%d-%H-%M`).

## 3. Nearest-Rank Percentile Calculations
When computing p50, p95, p99 on a 0-indexed sorted list of $N$ latencies:
```python
latencies.sort()
n = len(latencies)
p50 = latencies[int((n - 1) * 0.50)]
p95 = latencies[int((n - 1) * 0.95)]
p99 = latencies[int((n - 1) * 0.99)]
```
Using `(n - 1) * P` ensures exact alignment with 0-based array indexing for both odd and even datasets (e.g., $N=100 \implies$ index 94 for p95, index 98 for p99).

## 4. Hooking Analytics into Real-Time Collaboration
- On client WebSocket connection -> emit `user:presence_join`.
- On client WebSocket disconnect -> emit `user:presence_leave`.
- On mutation commit -> emit `workspace:mutation`.
- On OCC / Lock conflict -> emit `record_error_metric()` with error type and status code 409/423.

## 5. REST & Real-Time WebSocket Analytics Endpoints
- **REST Surface (`/api/v1/analytics/workspaces/{workspace_id}`)**:
  - `GET /activity`: Aggregate workspace activity breakdown & time-series data.
  - `GET /users`: Active user counts & activity distribution.
  - `GET /users/me/activity`: Current authenticated user's audit trail.
  - `GET /performance`: Summary of latencies (`p50`, `p95`, `p99`, `avg`) grouped by endpoint or operation.
  - `GET /errors`: Error logs and failure distributions.
- **Live WebSocket Stream (`/api/v1/analytics/workspaces/{workspace_id}/live`)**:
  - Requires JWT token validation (`?token=...`) on handshake.
  - Employs standardized WebSocket close codes: `4401` (Unauthenticated) and `4403` (Forbidden/Workspace Access Denied).
  - Handles client heartbeat frames (`{"type": "ping"}` -> `{"type": "pong", "timestamp": ...}`).
  - Periodic metrics broadcast (e.g., every 5 seconds) to subscribed dashboards.
- **Testing Pattern with TestClient**:
  - Use `client.websocket_connect(...)` with `pytest.raises(WebSocketDisconnect)` to verify unauthorized token rejection and exact code assertions (`exc.value.code == 4401` / `4403`).

## 6. Frontend Dashboard Integration & React Hooks
- **`useWorkspaceAnalytics(workspaceId, timeRangeHours)` Hook**:
  - Parallel REST queries (`Promise.all`) fetching `activity`, `performance`, `errors`, and `users`.
  - Normalizes null/missing structures to default empty lists/maps to avoid frontend rendering crashes.
  - Exposes `refetch()` trigger for on-demand manual refresh or time-range switches (`1h`, `24h`, `7d`, `30d`).
- **`useWorkspaceLiveMetrics(workspaceId)` WebSocket Hook**:
  - Establishes connection to `/api/v1/analytics/workspaces/${workspaceId}/live` with auto-reconnect backoff (e.g. 5s timer on disconnect).
  - Maintains client heartbeat ping interval (every 30s: `{"type": "ping"}`) and verifies incoming `pong` responses.
  - Parses `type === "metrics_update"` frames and updates state reactively.
- **Modular Dashboard Component Architecture**:
  - **`LiveMetricsPulseCard`**: Real-time pulse indicator showing 5-min activity count, average latency, error counter, and live WebSocket pulse dot.
  - **`ActivityTimelineChart`**: Dynamic bar visualization of event distribution over time with interactive tooltips and time range selector.
  - **`PerformancePercentilesCard`**: Endpoint latency breakdown (`p50`, `p95`, `p99`, `avg`) with count badges.
  - **`WorkspaceUsersActivityTable`**: Member roster with roles, activity counts, and relative "last active" timestamps.
  - **`WorkspaceErrorsLog`**: Triage log for 4xx/5xx errors, lock contentions, and OCC conflicts with severity tags.
