# --- DNK-MRH-HEADER ---
# mrh_id: "docs/api/api_reference.md"
# purpose: "Complete DNK OS REST and WebSocket API Reference specification."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "3.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 📡 DNK OS API Reference

## Base URL
```
https://api.dnk-os.com/api/v3
```
*Local Development: `http://localhost:8000`*

## Authentication
All API requests require Bearer token in Authorization header:
```http
Authorization: Bearer <your_token>
X-Workspace-ID: ws-alpha-001
```

---

## 1. System & Health Endpoints

### `GET /health`
Returns system health, database connectivity, and uptime metrics.
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "version": "4.5.0",
  "services": {
    "database": "online",
    "swarm_orchestrator": "online",
    "canvas_engine": "online"
  }
}
```

### `GET /metrics`
Prometheus-formatted telemetry metrics.

---

## 2. Tasks API (`/api/v3/tasks`)

### `POST /api/v3/tasks`
Create a new asynchronous task or evolutionary TaskDNA.
- **Request Body**:
```json
{
  "title": "Build Landing Page",
  "description": "Generate high-converting Shopify landing section",
  "priority": "high",
  "assigned_agent": "dnk_shopify"
}
```
- **Response**: `201 Created`
```json
{
  "id": "task_984f12ab",
  "status": "pending",
  "title": "Build Landing Page",
  "created_at": "2026-09-05T12:00:00Z"
}
```

### `GET /api/v3/tasks`
List existing tasks with optional filtering.
- **Query Parameters**:
  - `status`: `pending` | `in_progress` | `completed`
  - `limit`: Integer (default: 50)
- **Response**: `200 OK`

### `GET /api/v3/tasks/{task_id}`
Retrieve task details, execution logs, and output artifacts.

---

## 3. Swarm Orchestrator API (`/api/v3/swarm`)

### `POST /api/v3/swarm/dispatch`
Dispatch an isolated subtask to a specialized worker.
- **Request Body**:
```json
{
  "agent": "gerych_builder",
  "mode": "direct",
  "task_description": "Implement responsive canvas control toolbar",
  "workspace_id": "ws-alpha-001"
}
```

### `POST /api/v3/swarm/parallel`
Concurrently execute multiple subagent slices across parallel threads.
- **Request Body**:
```json
{
  "tasks": [
    { "agent": "dnk_shopify", "action": "validate_liquid" },
    { "agent": "gerych_auditor", "action": "security_scan" }
  ]
}
```

---

## 4. WebSocket Telemetry

### `WS /ws/telemetry`
Real-time bidirectional event streaming for Canvas state changes and agent status.
- **Protocol**: JSON-RPC / WebSocket
- **Connection Handshake**: `101 Switching Protocols`
- **Ping/Pong**: Keep-alive ping interval 30s.

---

## 5. Error Codes & Handling

| Status Code | Error Code | Description |
| :--- | :--- | :--- |
| `400` | `INVALID_PAYLOAD` | Request body failed schema validation. |
| `401` | `UNAUTHORIZED` | Missing or invalid Bearer token. |
| `403` | `FORBIDDEN` | Workspace access denied. |
| `404` | `NOT_FOUND` | Specified resource was not found. |
| `429` | `RATE_LIMITED` | Exceeded tenant quota (default: 100 req/sec). |
| `500` | `INTERNAL_ERROR` | Server exception; error distillation event recorded. |
