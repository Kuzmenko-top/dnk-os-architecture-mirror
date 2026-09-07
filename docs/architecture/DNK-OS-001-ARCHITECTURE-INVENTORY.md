# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture/DNK-OS-001-ARCHITECTURE-INVENTORY.md"
# purpose: "Architecture Inventory and Runtime Canonical Decision for DNK-OS-001 Visual Workspace MVP"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-OS-001"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🏛️ DNK-OS-001: Architecture Inventory & Canonical Runtime Decision

## 1. Executive Summary & Problem Statement

DNK OS MVP contains two parallel frontend structures (`visual_shell/web_ui` vs `apps/web`) and multiple backend entrypoints (`apps/api/main.py` vs `services/dnk_canvas_api/main.py`). Developing features across disparate entrypoints introduces token bloat, architectural fragmentation, and integration risks.

This document establishes the **Canonical Runtime Boundaries** for **DNK-OS-001 (Visual Workspace MVP — Shell, TaskDNA Dashboard & Canvas Foundation)**, locking in architectural decisions before any UI code is written.

---

## 2. Canonical Decisions Matrix

| Domain | Canonical Selection | Justification | Legacy/Alternative Policy |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | `apps/web` (Next.js 15 App Router, React 18/19, TypeScript) | Modern component hierarchy, server/client component boundaries, standard routing `/canvas/[canvasId]`, `/analytics`, `/taskdna`. | `visual_shell/web_ui` remains intact as frozen legacy reference. Zero deletion or alteration without dedicated migration task. |
| **Backend API** | `apps/api` (FastAPI 0.110+, Python 3.12) | Centralized middleware pipeline (`SecurityMiddleware`), unified router registration (`canvas`, `agent`, `artifact`, `analytics`, `taskdna`). | `services/dnk_canvas_api` isolated as service worker logic only. `apps/api/main.py` is the single source of truth for HTTP/WebSocket traffic. |
| **Canvas Engine** | `apps/web/components/canvas/CanvasEditor.tsx` (`@xyflow/react`) | Leverages ReactFlow v12 ecosystem, hardware-accelerated pan/zoom, typed node/edge structures (`TaskNode`, `SupervisorNode`, `WorkerNode`, `GateNode`, `PRNode`). | Existing nodes in `visual_shell/web_ui/components` serve as behavioral reference only. |
| **Persistence / DB** | In-Memory / Deterministic Fixtures (M1) | Zero premature migrations. PostgreSQL/pgvector and Redis schemas are deferred until write operations or persistent checkpointers are authorized in M2/M3. | No DB tables or Alembic migrations created in M1. |
| **GitHub Integration** | Server-Side Normalizing Adapter (`apps/api/routers/taskdna.py`) | Browser client never receives or stores GitHub API tokens. All GitHub REST/GraphQL data is transformed into canonical TaskDNA read models server-side. | Zero GitHub write operations in M1. Purely read-only inspection. |
| **Security & Auth** | Fail-Closed Workspace Gate | Mandatory `X-Workspace-ID` header and JWT Bearer validation. Missing or invalid workspace context returns `403 Forbidden`. | Enforced across all API routes via `apps/api/middleware/security.py`. |

---

## 3. Directory Layout & Boundary Definitions

```text
DNK OS/
├── apps/
│   ├── api/                           <-- CANONICAL BACKEND
│   │   ├── main.py                    # App entrypoint & router registry
│   │   ├── middleware/security.py     # Fail-closed workspace & auth guard
│   │   ├── routers/
│   │   │   ├── taskdna.py             # [DNK-OS-001] TaskDNA read model & timeline
│   │   │   ├── canvas.py              # Canvas state & nodes
│   │   │   ├── analytics.py           # Metrics & telemetry
│   │   │   └── artifact.py            # Evidence & artifacts
│   │   └── database.py
│   └── web/                           <-- CANONICAL FRONTEND
│       ├── app/
│       │   ├── layout.tsx             # Root Shell & Navigation Rail
│       │   ├── page.tsx               # Workspace Overview
│       │   ├── taskdna/page.tsx       # [DNK-OS-001] TaskDNA Dashboard
│       │   ├── canvas/[canvasId]/     # [DNK-OS-001] Visual Canvas
│       │   └── analytics/page.tsx     # Telemetry & Timeline
│       └── components/
│           ├── workspace/             # Shell, Header, Nav, Drawer
│           ├── taskdna/               # Task Card, Gate Progress, PR Badge
│           └── canvas/                # CanvasEditor, Custom Nodes, Inspector
├── visual_shell/
│   └── web_ui/                        <-- FROZEN REFERENCE (DO NOT TOUCH)
├── docs/
│   └── architecture/
│       ├── DNK-OS-001-ARCHITECTURE-INVENTORY.md
│       └── DNK-OS-001-TASKDNA-API-CONTRACT.md
└── tests/
    └── dnk_os_001/                    <-- TEST SUITE
        ├── test_taskdna_mapping.py    # Unit tests for domain models
        └── test_taskdna_api.py        # API contract integration tests
```

---

## 4. Auth & Security Invariants

1. **Header Propagation:**
   Every client request from `apps/web` MUST inject:
   - `X-Workspace-ID: <uuid | string>`
   - `Authorization: Bearer <token>` (if authenticated)
2. **Fail-Closed Policy:**
   If `X-Workspace-ID` is missing, the backend immediately terminates the request with `403 Forbidden` (`{"detail": "Missing X-Workspace-ID header", "error_type": "SecurityGateDenied"}`).
3. **Network Isolation:**
   Visual components NEVER initiate direct external HTTP requests (e.g. to `api.github.com` or Shopify). All external data is mediated through `apps/api`.
4. **Token Containment:**
   GitHub tokens, OpenAI/Claude API keys, and database credentials remain strictly in backend environment variables and are NEVER exposed to the frontend browser bundle.

---

## 5. Docker Runtime Path

The single command to run the DNK OS ecosystem locally without host pollution:

```bash
docker-compose -f docker-compose.yml up --build
```

- **Backend:** `http://localhost:8000` (FastAPI)
- **Frontend:** `http://localhost:3000` (Next.js App Router)
- **Postgres:** `localhost:5432` (Healthcheck verified)
- **Redis:** `localhost:6379` (Healthcheck verified)
