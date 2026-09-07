# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-VISUAL-OS-001_working_cabinet.md"
# purpose: "Technical Specification for Visual DNK OS MVP Working Cabinet (Robochyi Kabinet)"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-VISUAL-OS-001"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🖥️ Visual DNK OS MVP: Working Cabinet Technical Specification (DNK-VISUAL-OS-001)

## 1. Overview & System Objectives
The **Visual DNK OS Working Cabinet (Robochyi Kabinet)** serves as the canonical interactive desktop and web console for the DNK OS ecosystem. It bridges human decision-makers (Maxim / Mentor) and autonomous agent swarms (Gerych, Antigravity, subagents) into a unified, deterministic, and visual operational control center.

Key goals:
- **Zero-Latency Observability:** Real-time visibility into agent tasks, task trees, artifacts, and multi-agent communications.
- **Fail-Closed Security:** Strict workspace-level access control, granular security gate approvals, and cryptographic auditability.
- **Unified Multimodal Workspace:** Seamless integration of Task Forest (5-plant hierarchy), Infinite Canvas (tldraw/ReactFlow), Agent Swarm inspection, and Evidence Lifecycles.

---

## 2. Workspace Identity & Multi-Tenancy Architecture
Each working cabinet session is strictly bound to a verified `workspace_id` and tenant context.

```
       +-------------------------------------------------------------+
       |                  HTTP Request / WS Client                   |
       +------------------------------+------------------------------+
                                      |
                     Headers: `X-Workspace-Id`, `Authorization`
                                      v
       +-------------------------------------------------------------+
       |           Fail-Closed Workspace Authorization Guard          |
       +------------------------------+------------------------------+
                                      |
              Matches session token to active tenant workspace
                                      v
       +-------------------------------------------------------------+
       |             Isolated Cabinet Data Context (DB/FS)           |
       +-------------------------------------------------------------+
```

- **Headers:** Canonical header spelling is `X-Workspace-Id: <uuid>`.
- **Isolation:** Operations on flowers, nodes, canvas assets, and logs are query-scoped by `workspace_id`. Cross-workspace access returns `403 Forbidden` / `404 Not Found`.

### 2.1. Server-Authorized Discovery & Auth Bootstrap Contract
1. **Authentication Bootstrap:** `WorkspaceProvider` requires `authToken` (Bearer JWT) from props, session, or client storage. If absent, the cabinet immediately halts in `authStatus: 'unauthorized'` without making unauthenticated discovery requests.
2. **Server-Side Authorized Discovery:** With a valid `authToken`, `WorkspaceProvider` queries `GET /api/v1/workspaces` passing `Authorization: Bearer <token>` and `AbortSignal`. The backend guarantees that the returned list contains only workspaces authorized for that identity:
   ```json
   [
     {
       "id": "11111111-2222-3333-4444-555555555555",
       "name": "Production Workspace",
       "role": "Owner"
     }
   ]
   ```
   The frontend validates RFC4122 non-zero UUIDs and binds the server-assigned `id`, `name`, and `role`.
3. **Deterministic State Mapping:**
   - `401 Unauthorized` -> `authStatus: 'unauthorized'`
   - `403 Forbidden` -> `authStatus: 'forbidden'`
   - `5xx / Network Error / Malformed` -> `authStatus: 'degraded'`
   - Empty or invalid list -> `authStatus: 'missing_context'`
4. **Scoped Data Reset & Request Abort:** On workspace switch, prior in-flight requests are aborted via `AbortController`, `clearScopedData()` resets active module state, and data is reloaded under the new boundary.

### 2.2. Health Check Scope & Polling Contract
- **Public Infrastructure Health:** `GET /api/v1/health` checks public system reachability (API status, PostgreSQL, Redis) via a bounded 30s polling interval. It requires NO `X-Workspace-Id` header.
- **Workspace-Scoped Telemetry:** Telemetry and stats scoped to a specific workspace use `fetchWithContext('/api/v1/workspace/status')` and strictly carry the validated canonical `X-Workspace-Id` and `Authorization` headers.

---

## 3. Working Cabinet Layout & Structure
The interface follows an ergonomic three-pane workspace with collapsible drawers:

```
+----------------------------------------------------------------------------------------------------+
| 🧬 DNK OS | Workspace: Alpha [v] | Status: Operational | Swarm: Active | Auth: Maxim (Owner)       |
+-------------------+---------------------------------------------------------+----------------------+
|  🧭 NAVIGATION   |  🗺️ BREADCRUMBS: Workspace > Task Forest > Flower-003    |  ⚡ ACTIVE AGENTS    |
+-------------------+---------------------------------------------------------+----------------------+
| 📊 Overview       |                                                         | 🤖 Gerych (Building) |
| 🌸 Task Flowers   |                                                         | 🧠 Antigravity (Idle)|
| 🎨 Canvas         |                   MAIN WORKSPACE VIEWPORT               | 🔍 Dev-01 (Testing)  |
| 🤖 Agent Swarms   |                                                         |                      |
| 🛡️ Approvals [2]  |       (Renders active view: Overview / Flower /         +----------------------+
| 📑 Reports        |        Canvas / Swarm / Approvals / Reports)            |  🔍 INSPECTOR PANEL  |
| ⚙️ Settings       |                                                         | Node / Asset / Diff  |
|                   |                                                         | Properties & Logs    |
+-------------------+---------------------------------------------------------+----------------------+
| 🔔 Terminal / Execution Drawer [Status: All systems nominal | CI: Green | Docker: Healthy]         |
+----------------------------------------------------------------------------------------------------+
```

### Layout Elements:
1. **Top Header / App Bar (48px):** Workspace selector, read-only telemetry health indicators (`dnk-api`, `postgres`, `redis`), global sync status, user profile.
2. **Left Navigation Rail (240px / Collapsible to 64px):** Primary module navigation, badge counts for pending approvals.
3. **Central Viewport (Fluid flex-1):** Contextual active workspace module.
4. **Right Contextual Inspector (320px / Toggleable):** Live metadata, asset previews, agent memory inspector, parameter tuners.
5. **Bottom Event Drawer (Collapsible 36px/240px):** System events and execution logs (Phase 1: polling / static placeholder; WebSocket streaming deferred).

---

## 4. Modules & Views

### 4.1. Overview (Dashboard)
- **KPI Metrics:** Total flowers, active swarm processes, pending security approvals, cycle velocity.
- **Active Task Feed:** Stream of latest agent state transitions.
- **System Health:** Docker container status, PostgreSQL connection pool, Redis status (Read-Only Telemetry).

### 4.2. Task Flowers (Task Forest Engine)
- **Hierarchical Plant Scale View:**
  1. `Project_Field` ➔ 2. `Sector_Zone` ➔ 3. `Epic_Tree` ➔ 4. `Feature_Bush` ➔ 5. `Task_Flower`.
- **Flower Lifecycle Visualizer:** Shows active stage (`Pollenation` ➔ `Budding` ➔ `Blooming` ➔ `Seeding` ➔ `Harvested`).
- **Live Cycle Logs:** Real-time stdout/stderr from subagents executing specific tasks.

### 4.3. Infinite Multimodal Canvas
- **Hybrid Viewport:** Integrated `tldraw` vector surface and `ReactFlow` graph engine.
- **Node Primitives:**
  - `Research Node`: Markdown findings, external reference cards.
  - `Evidence / Asset Node`: Images, binary files, PDFs with physical SHA-256 integrity badges.
  - `Agent Scratchpad`: Live streaming agent thoughts and generation diffs.
  - `Synthesis Node`: Live compiled UI preview or code sandbox.
- **Asset Integrity:** Physical verification tag (`storage_type: local_fixture`, `sha256: verified`).

### 4.4. Agent Swarms
- **Swarm Topology:** Visual DAG of active parent orchestrator (`Gerych`) and spawned leaf agents.
- **Context Budget Monitor:** Real-time token usage meter per subagent to enforce Zero Token Bloat (<10k context target).
- **Steering Console:** Input prompt to inject steering instructions into running subagents.

### 4.5. Approvals (Security Gate)
- **Pending Actions Queue:** High-risk actions (file overwrites, git commits, external mutations, migrations).
- **Unified Diff Inspector:** Visual side-by-side diff of proposed changes.
- **Decision Controls:** `Approve & Execute`, `Reject & Amend`, `Delegate with Constraint`.

### 4.6. Reports & Execution Cycles
- **Execution Cycle Archives:** Filterable directory of all historical execution cycle markdown records.
- **DoD Compliance Matrix:** Automated checklist showing test coverage, hygiene verification, and artifact signatures.
- **Export Engine:** One-click bundle generation for audit reports.

---

## 5. API Contracts & Data Models

### 5.1. Core Types
```typescript
export interface WorkspaceIdentity {
  workspace_id: string;
  name: string;
  role: 'owner' | 'architect' | 'developer' | 'viewer';
  created_at: string;
}

export interface TaskFlowerSummary {
  flower_id: string;
  title: string;
  plant_scale: 'Task_Flower' | 'Feature_Bush' | 'Epic_Tree';
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  active_agent?: string;
  cycle_count: number;
  updated_at: string;
}

export interface SecurityApprovalRequest {
  approval_id: string;
  action_type: 'filesystem_write' | 'git_push' | 'migration' | 'api_mutation';
  target_resource: string;
  diff_preview?: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  requested_by_agent: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}
```

### 5.2. Primary Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/workspace/overview` | Aggregated dashboard telemetry and KPI counts |
| `GET` | `/api/v1/workspace/flowers` | List task flowers with hierarchy filters |
| `GET` | `/api/v1/canvas/{canvas_id}/state` | Load complete canvas graph and asset metadata |
| `POST` | `/api/v1/canvas/{canvas_id}/assets`| Upload verified physical binary asset |
| `GET` | `/api/v1/agents/swarm/status` | Active subagent topologies and token budgets |
| `GET` | `/api/v1/security/approvals` | List pending security gate approval requests |
| `POST` | `/api/v1/security/approvals/{id}/decision` | Submit decision (`approve` / `reject`) |
| `GET` | `/api/v1/reports/cycles` | Query historical execution cycle reports |

---

## 6. UI States, Error Handling & Resilience

1. **Loading State:**
   - Skeleton screens for dashboard cards and task lists.
   - Canvas loader with background state restoration.
2. **Empty State:**
   - Clear contextual guidance and action buttons (e.g., "Create First Task Flower", "Initialize Canvas").
3. **Error Boundaries:**
   - Isolated widget error cards with localized retry triggers (a failure in the log stream does not crash the Canvas).
4. **Disconnected / Offline State:**
   - Non-blocking amber banner indicator: "Connection to dnk-api interrupted. Retrying...".
   - Read-only UI state preservation.

---

## 7. Security & Governance Invariants
- **Fail-Closed Workspace Headers:** Every API call missing or carrying invalid `X-Workspace-Id` fails immediately with `401 Unauthorized` or `403 Forbidden`.
- **Zero Host Path Leaks:** Absolute local paths are scrubbed by `PathHygieneGuard` before reaching the UI or API responses.
- **Audit Immutability:** All approval decisions and state changes emit structured audit logs to Postgres Timeline DB.

---

## 8. Definition of Done (DoD) & Verification Gates
1. **TypeScript / Linter Strictness:** Zero TypeScript errors, clean ESLint rules.
2. **API Contract Verification:** Test coverage on routers backing cabinet endpoints.
3. **E2E Component Integration:** Automated verification for:
   - Workspace switching and `X-Workspace-Id` headers.
   - Real-time task flower progress updates.
   - Canvas asset rendering and SHA-256 verification badges.
   - Security gate approval submission flow.
4. **Zero Host Pollution:** All visual shell services execute within Docker containers (`docker-compose.yml`).
