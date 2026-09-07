# --- DNK-MRH-HEADER ---
# mrh_id: "docs/user-guides/API_REFERENCE.md"
# purpose: "Comprehensive REST and WebSocket API Reference for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# DNK OS Complete API Reference

Welcome to the DNK OS API Reference. This documentation describes the core REST and WebSocket interfaces for interacting with DNK OS, managing multi-agent swarms, controlling canvas graphs, and executing automated workflows.

---

## 1. Authentication & Security Gate
All requests to DNK OS endpoints require secure authentication via Bearer API token or Session Header.
- **Header**: `Authorization: Bearer <DNK_API_KEY>`
- **Workspace Header**: `X-Workspace-ID: ws-alpha-001`
- **Security Decorator**: `@security_gate(allowed_roles=["admin", "operator"])` enforces role-based access control.

```http
GET /api/v1/auth/verify HTTP/1.1
Host: localhost:8000
Authorization: Bearer dnk_live_sec_token_v4
X-Workspace-ID: ws-alpha-001
```

---

## 2. Workspaces & Tenant Management
Manages multi-tenant environments, isolated storage boundaries, and workspace budgets.
- `GET /api/v1/workspaces`: List all accessible workspaces.
- `POST /api/v1/workspaces`: Create a new workspace context with assigned token budget.
- `GET /api/v1/workspaces/{workspace_id}/spending`: Retrieve token metrics, USD costs, and duration telemetry.

---

## 3. Canvas Engine Graph API
Allows querying and mutating the reactive 2D/3D visual canvas graph, nodes, edges, and spatial layouts.
- `GET /api/v1/canvas/graph`: Get the current graph snapshot (nodes, edges, viewport).
- `POST /api/v1/canvas/nodes`: Create a new canvas node (e.g. `agent_node`, `archify_node`, `task_forest_node`).
- `PUT /api/v1/canvas/nodes/{id}`: Update position, bounding box, or custom attributes.
- `DELETE /api/v1/canvas/nodes/{id}`: Safely prune a node and its incident edges.

---

## 4. Real-time WebSocket Protocol (`/ws/canvas`)
Provides bi-directional, low-latency streaming of graph mutations, presence indicators, and live tool execution output.
- **Handshake URL**: `ws://localhost:8000/ws/canvas?client_id=usr_9921`
- **Supported Messages**:
  - `GRAPH_MUTATION`: Broadcasts node additions, moves, and edge links.
  - `TIME_TRAVEL_RESTORE`: Rewinds canvas state to a historical checkpoint.
  - `AGENT_TELEMETRY`: Streams subagent execution traces and logs.

---

## 5. Swarm Orchestration & Agent Dispatch
Dispatches tasks to the 14 specialized swarm workers (`gerych_builder`, `dnk_dev_fullstack`, `dnk_shopify`, `gerych_auditor`, etc.).
- `POST /api/v1/swarm/dispatch`:
  - **Body**: `{ "agent": "gerych_builder", "task_description": "...", "mode": "direct" }`
- `POST /api/v1/swarm/parallel`:
  - Dispatches multiple subagent tasks concurrently with thread-safe model tier routing.
- `GET /api/v1/swarm/status`: Telemetry and availability matrix for all active workers.

---

## 6. SCONES Cognitive Memory Engine
Provides long-term episodic, semantic, and architectural memory storage.
- `POST /api/v1/scones/memories`: Store a new cognitive episode or architectural rule.
- `GET /api/v1/scones/memories/search?query={q}&limit=5`: Retrieve top matching memory records.
- **Attributes**: `topic`, `content`, `importance` (0.1 - 1.0), `workspace_id`.

---

## 7. Shopify E-Commerce & Liquid Engine
Endpoints for generating, testing, and compiling Shopify themes, Liquid ASTs, and WebAssembly Function extensions.
- `POST /api/v1/shopify/validate-liquid`: Validates Liquid template syntax, schema JSON, and tag balancing.
- `POST /api/v1/shopify/compile-wasm`: Compiles Rust/WASM discount and cart validation rules.
- `POST /api/v1/shopify/product-launch`: Executes full autonomous One-Click Product Launch pipeline.

---

## 8. Video Studio & Remotion Composition
Synthesizes video creatives, dynamic stories, reels, and video ads programmatically.
- `POST /api/v1/video/compositions`: Generate Remotion / FrameCN composition descriptors.
- `GET /api/v1/video/renders/{render_id}`: Poll rendering progress and download finalized MP4 assets.
- **Formats**: `story_9_16`, `landscape_16_9`, `square_1_1`.

---

## 9. Error Distillation & Self-Healing Database
Stores distilled root causes and confirmed code fixes to prevent repetitive build failures.
- `GET /api/v1/distiller/solutions?error={text}`: Query verified solutions for a stack trace.
- `POST /api/v1/distiller/solutions`: Record a newly resolved error, root cause, and patch solution.

---

## 10. Rate Limits, Quotas & Error Contracts
Standards for error payloads, status codes, and SpendGuard rate limiting.
- **Rate Limit**: 120 requests/minute per API key; WebSocket connection heartbeats every 30 seconds.
- **HTTP 429**: Quota exceeded. Response includes `Retry-After: <seconds>`.
- **Standard Error Payload**:
  ```json
  {
    "error": {
      "code": "SECURITY_GATE_DENIED",
      "message": "Bearer token does not have role 'admin'.",
      "status_code": 403,
      "trace_id": "req-98fa-1029"
    }
  }
  ```
