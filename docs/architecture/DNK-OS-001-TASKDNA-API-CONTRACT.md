# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture/DNK-OS-001-TASKDNA-API-CONTRACT.md"
# purpose: "TaskDNA Domain Model, REST API Contract, and Read-Model Specification for DNK-OS-001"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-OS-001"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🧬 DNK-OS-001: TaskDNA Domain Model & API Contract Specification

## 1. Domain Entities & Schemas

### 1.1. Workspace
```json
{
  "id": "ws-alpha-001",
  "name": "DNK OS Core Delivery",
  "status": "active",
  "created_at": "2026-08-23T10:00:00Z",
  "updated_at": "2026-08-23T12:00:00Z"
}
```

### 1.2. Task (TaskDNA Read Model)
```json
{
  "id": "DNK-SHOPIFY-011",
  "workspace_id": "ws-alpha-001",
  "title": "PDP Conversion Runtime baseline verification & test suite",
  "phase": "Phase 5: Handoff & Merge",
  "status": "COMPLETED",
  "owner": "Maxim (Mentor)",
  "supervisor": {
    "id": "antigravity-01",
    "role": "Supervisor",
    "name": "Antigravity",
    "status": "IDLE"
  },
  "worker": {
    "id": "gerych-01",
    "role": "Worker",
    "name": "Gerych",
    "status": "IDLE"
  },
  "git_context": {
    "repository": "DNKShopify/DNK-e.com",
    "branch": "mentor/shopify/DNK-SHOPIFY-011-pdp-conversion-runtime",
    "base_branch": "feature/01-tinker-analysis",
    "base_sha": "985e60b2ae658fff284ab4bdacd8c6697cd1eb66",
    "head_sha": "fb863474a87e0877ed18109de83848a8b60c4db5",
    "merge_sha": "daac1b1c20cd4c80f4c62fd56bfa79f202a8111e"
  },
  "validation_gates": [
    {
      "id": "gate-pdp-inventory",
      "name": "PDP Inventory & Spec",
      "status": "PASSED",
      "evidence_ref": "docs/migration/DNK-SHOPIFY-011-PDP-INVENTORY.md",
      "completed_at": "2026-08-23T14:30:00Z"
    },
    {
      "id": "gate-tests",
      "name": "Unit & Static Tests",
      "status": "PASSED",
      "evidence_ref": "tests/shopify/test_pdp_runtime.py",
      "completed_at": "2026-08-23T15:00:00Z"
    },
    {
      "id": "gate-theme-preview",
      "name": "Theme Preview (14/14 Scenarios)",
      "status": "PASSED",
      "evidence_ref": "docs/migration/DNK-SHOPIFY-011-THEME-PREVIEW-EVIDENCE.md",
      "completed_at": "2026-08-23T16:00:00Z"
    },
    {
      "id": "gate-ci",
      "name": "GitHub Actions CI",
      "status": "PASSED",
      "evidence_ref": "Check Runs: completed / success",
      "completed_at": "2026-08-23T16:15:00Z"
    }
  ],
  "pull_request": {
    "number": 4,
    "title": "feat(pdp): PDP Conversion Runtime baseline verification & test suite (DNK-SHOPIFY-011)",
    "state": "MERGED",
    "head_sha": "fb863474a87e0877ed18109de83848a8b60c4db5",
    "base_branch": "feature/01-tinker-analysis",
    "checks_status": "SUCCESS",
    "mergeable": true,
    "merged_at": "2026-08-23T16:45:00Z"
  },
  "blockers": [],
  "dod_progress": {
    "total": 6,
    "completed": 6,
    "percentage": 100
  },
  "created_at": "2026-08-23T14:00:00Z",
  "updated_at": "2026-08-23T16:45:00Z"
}
```

### 1.3. Canvas Graph Model (`/api/tasks/{task_id}/graph`)
```json
{
  "task_id": "DNK-SHOPIFY-011",
  "nodes": [
    {
      "id": "node-task",
      "type": "taskNode",
      "position": { "x": 250, "y": 50 },
      "data": {
        "label": "DNK-SHOPIFY-011",
        "title": "PDP Conversion Runtime",
        "status": "COMPLETED",
        "phase": "Phase 5"
      }
    },
    {
      "id": "node-supervisor",
      "type": "agentNode",
      "position": { "x": 50, "y": 180 },
      "data": { "name": "Antigravity", "role": "Supervisor", "status": "IDLE" }
    },
    {
      "id": "node-worker",
      "type": "agentNode",
      "position": { "x": 450, "y": 180 },
      "data": { "name": "Gerych", "role": "Worker", "status": "IDLE" }
    },
    {
      "id": "node-gate-tests",
      "type": "gateNode",
      "position": { "x": 150, "y": 320 },
      "data": { "name": "Static & Unit Tests", "status": "PASSED" }
    },
    {
      "id": "node-gate-preview",
      "type": "gateNode",
      "position": { "x": 350, "y": 320 },
      "data": { "name": "Theme Preview (14/14)", "status": "PASSED" }
    },
    {
      "id": "node-pr",
      "type": "prNode",
      "position": { "x": 250, "y": 450 },
      "data": { "number": 4, "state": "MERGED", "checks": "SUCCESS" }
    }
  ],
  "edges": [
    { "id": "e-task-supervisor", "source": "node-task", "target": "node-supervisor", "label": "governs" },
    { "id": "e-task-worker", "source": "node-task", "target": "node-worker", "label": "executes" },
    { "id": "e-worker-gate-tests", "source": "node-worker", "target": "node-gate-tests", "label": "produces" },
    { "id": "e-worker-gate-preview", "source": "node-worker", "target": "node-gate-preview", "label": "verifies" },
    { "id": "e-gates-pr", "source": "node-gate-tests", "target": "node-pr", "label": "unlocks" },
    { "id": "e-preview-pr", "source": "node-gate-preview", "target": "node-pr", "label": "unlocks" }
  ]
}
```

---

## 2. API Endpoints Specification

### 2.1. `GET /api/workspaces/{workspace_id}`
- **Headers:** `X-Workspace-ID: <string>`
- **Response:** `200 OK` Workspace object.

### 2.2. `GET /api/tasks`
- **Headers:** `X-Workspace-ID: <string>`
- **Query Params:** `status` (optional), `limit` (default: 50)
- **Response:** `200 OK` Array of TaskDNA summary objects.

### 2.3. `GET /api/tasks/{task_id}`
- **Headers:** `X-Workspace-ID: <string>`
- **Response:** `200 OK` Full TaskDNA object.

### 2.4. `GET /api/tasks/{task_id}/timeline`
- **Headers:** `X-Workspace-ID: <string>`
- **Response:** `200 OK` Ordered array of timeline events.

### 2.5. `GET /api/tasks/{task_id}/graph`
- **Headers:** `X-Workspace-ID: <string>`
- **Response:** `200 OK` ReactFlow-compatible `{ nodes, edges }` JSON object.

---

## 3. Error Model

All error responses strictly follow RFC 7807 problem details:

```json
{
  "detail": "Descriptive error message",
  "error_type": "SecurityGateDenied | TaskNotFound | WorkspaceNotFound | ValidationError",
  "status_code": 403
}
```

| HTTP Status | Error Type | Trigger Condition |
| :--- | :--- | :--- |
| `400 Bad Request` | `ValidationError` | Invalid query/path parameters or payload |
| `403 Forbidden` | `SecurityGateDenied` | Missing or invalid `X-Workspace-ID` |
| `404 Not Found` | `TaskNotFound` / `WorkspaceNotFound` | Task or Workspace ID does not exist |
| `500 Internal Error` | `InternalServerError` | Unhandled runtime exception |

---

## 4. Fixture vs GitHub Read Model Strategy

```text
[HTTP Request] 
      │
      ▼
[SecurityMiddleware] (Validates X-Workspace-ID)
      │
      ▼
[TaskDNARepository Protocol]
      ├── If TASKDNA_DATA_SOURCE == "fixture" (Default) ──> Loads deterministic JSON fixtures
      └── If TASKDNA_DATA_SOURCE == "github"  ──> Fetches via gh/REST & normalizes to TaskDNA schema
```

- In **M1**, the default backend repository operates in `fixture` mode to enable completely offline, zero-network, deterministic visual previews and unit testing.
- When `TASKDNA_DATA_SOURCE=github` is enabled, the backend maps GitHub PR/checks data without ever allowing frontend write access or exposing secret tokens.
