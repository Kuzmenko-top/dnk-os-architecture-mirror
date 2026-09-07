# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech-specs-dnk-std-0080.md"
# purpose: "Formal Technical Specification (DNK-STD-0080) for DNK OS Architecture, Database Schema, API Contracts & Deployment Standards"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 📘 DNK-STD-0080: DNK OS Technical Specification

This document establishes the canonical technical baseline for DNK OS, covering system architecture, relational & vector data schemas, API contracts, security enforcement (RLS), and deployment standards.

---

## 📑 Table of Contents
1. [Phase 1: Overview & Dependencies Matrix](#1-overview--dependencies-matrix)
2. [Phase 2: Database Schema & Storage Topologies](#2-database-schema--storage-topologies)
   - [2.1 PostgreSQL Relational Schema & ERD](#21-postgresql-relational-schema--erd)
   - [2.2 pgvector Vector Schema](#22-pgvector-vector-schema)
   - [2.3 Redis Key Spaces & Pub/Sub Channels](#23-redis-key-spaces--pubsub-channels)
   - [2.4 Row-Level Security (RLS) Isolation Policies](#24-row-level-security-rls-isolation-policies)
3. [Phase 3: API Contracts & Interface Standards](#3-api-contracts--interface-standards)
   - [3.1 Core Endpoints & Schemas](#31-core-endpoints--schemas)
   - [3.2 Error Model & Error Codes](#32-error-model--error-codes)
   - [3.3 Rate Limiting & Throttling](#33-rate-limiting--throttling)
4. [Phase 4: Deployment, Orchestration & Operations](#4-deployment-orchestration--operations)
   - [4.1 Service Topology (Docker Compose)](#41-service-topology-docker-compose)
   - [4.2 Environment Variable Matrix](#42-environment-variable-matrix)
   - [4.3 Health Check Standards](#43-health-check-standards)
   - [4.4 Rollback & Disaster Recovery Procedures](#44-rollback--disaster-recovery-procedures)

---

## 1. Overview & Dependencies Matrix

### 1.1 Specification Metadata
- **Standard Identifier**: `DNK-STD-0080`
- **Application Target**: `DNK OS Multi-Agent Production Core`
- **Target Environments**: Local Development, Staging, Production (OCI / Baremetal / Cloud)
- **Compliance**: Zero-Waste Protocol, Fail-Closed Security, MRH Standard (`DNK-STD-0075`)

### 1.2 Tech Stack & Dependency Matrix

| Component | Technology / Runtime | Version | Role in Architecture |
|---|---|---|---|
| **Core API** | Python / FastAPI / Uvicorn | `>= 3.11 / 0.110+` | Core REST API, WebSocket hub & orchestration |
| **Multi-Agent Engine** | LangGraph / CrewAI / AutoGen / SCONES | Internal v3.0 | Swarm orchestration & stateful agent graphs |
| **Relational Database** | PostgreSQL | `>= 16.0` | Primary state, checkpointer, audit trails & metadata |
| **Vector Database** | PostgreSQL + pgvector extension | `pgvector >= 0.5` | SCONES semantic embeddings & similarity search |
| **Cache & Pub/Sub** | Redis | `>= 7.2` | Ephemeral caching, rate-limiting, agent message bus |
| **Frontend Shell** | Next.js / React / TailwindCSS | `14+ / React 18+` | Visual workspace canvas & operator UI |
| **Media Renderer** | Node.js / Remotion / Chromium | `Node 20+` | Video generation & programmatic animation pipeline |
| **E-Commerce Engine** | Shopify Theme Tools / Vite | Vite 5+ | Liquid AST parsing & Shopify theme pipeline |

---

## 2. Database Schema & Storage Topologies

### 2.1 PostgreSQL Relational Schema & ERD

The relational layer coordinates workspaces, agent graph checkpoints, audit trails, and multi-tenant isolation.

```mermaid
erDiagram
    TENANTS ||--o{ WORKSPACES : owns
    WORKSPACES ||--o{ WORKSPACE_NODES : contains
    WORKSPACES ||--o{ WORKSPACE_EDGES : contains
    WORKSPACES ||--o{ WORKSPACE_PROMPTS : logs
    WORKSPACES ||--o{ WORKSPACE_DIFFS : tracks
    WORKSPACES ||--o{ WORKSPACE_APPROVALS : requests
    WORKSPACES ||--o{ WORKSPACE_SNAPSHOTS : records
    WORKSPACES ||--o{ WORKSPACE_COMMITS : versions
    WORKSPACES ||--o{ WORKSPACE_AUDIT_TRAIL : records

    WORKSPACES {
        uuid id PK
        string tenant_id FK
        string name
        string status
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    WORKSPACE_NODES {
        uuid id PK
        uuid workspace_id FK
        string node_type
        jsonb position
        jsonb data
        timestamp updated_at
    }

    WORKSPACE_EDGES {
        uuid id PK
        uuid workspace_id FK
        uuid source_node_id FK
        uuid target_node_id FK
        jsonb data
    }

    WORKSPACE_AUDIT_TRAIL {
        uuid id PK
        string tenant_id FK
        uuid workspace_id FK
        string actor_id
        string action
        jsonb payload
        timestamp created_at
    }

    WORKSPACE_IDEMPOTENCY_CACHE {
        string idempotency_key PK
        string tenant_id
        jsonb response_payload
        timestamp expires_at
    }
```

### 2.2 pgvector Vector Schema

The vector store backs the SCONES cognitive memory engine and knowledge assimilation pipeline.

```sql
-- Extension Setup
CREATE EXTENSION IF NOT EXISTS vector;

-- Memory Embeddings Table
CREATE TABLE IF NOT EXISTS scones_memory_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    workspace_id VARCHAR(64),
    memory_type VARCHAR(32) NOT NULL, -- 'episodic', 'semantic', 'procedural'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(1536), -- OpenAI text-embedding-3-small or equivalent
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW Vector Index for High-Velocity Cosine Search
CREATE INDEX IF NOT EXISTS idx_scones_memory_vectors_hnsw
ON scones_memory_vectors
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Tenant Partition Index
CREATE INDEX IF NOT EXISTS idx_scones_vectors_tenant_lookup
ON scones_memory_vectors (tenant_id, memory_type);
```

### 2.3 Redis Key Spaces & Pub/Sub Channels

| Key / Channel Pattern | Data Structure | TTL | Purpose |
|---|---|---|---|
| `ws:{tenant_id}:{workspace_id}:state` | String (JSON) | 24 hours | Fast active state cache for workspace nodes |
| `agent:{agent_id}:session:{session_id}` | Hash | 1 hour | Transient conversational & memory context |
| `rate_limit:{tenant_id}:{endpoint}` | String (Counter) | 60 sec | Distributed sliding-window rate limiting |
| `collab:{workspace_id}:presence` | Sorted Set | 60 sec | Real-time active operator / cursor tracking |
| **Channel**: `swarm:events:{tenant_id}` | Pub/Sub Channel | Real-time | Broadcast swarm agent tasks & state changes |
| **Channel**: `canvas:updates:{workspace_id}` | Pub/Sub Channel | Real-time | Real-time visual canvas delta synchronization |

### 2.4 Row-Level Security (RLS) Isolation Policies

Per `Alembic Revision 005`, all tenant tables enforce hardware-level isolation using PostgreSQL RLS and session settings.

```sql
-- 1. Enable RLS on Direct Tenant Tables
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_audit_trail ENABLE ROW LEVEL SECURITY;
ALTER TABLE scones_memory_vectors ENABLE ROW LEVEL SECURITY;

-- 2. Tenant Isolation Policy (Fail-Closed)
CREATE POLICY workspaces_tenant_isolation ON workspaces
FOR ALL
USING (
    tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')
)
WITH CHECK (
    tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')
);

-- 3. Indirect Isolation via Workspace Parent (e.g. workspace_nodes)
ALTER TABLE workspace_nodes ENABLE ROW LEVEL SECURITY;

CREATE POLICY workspace_nodes_tenant_isolation ON workspace_nodes
FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM workspaces w
        WHERE w.id = workspace_nodes.workspace_id
        AND w.tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM workspaces w
        WHERE w.id = workspace_nodes.workspace_id
        AND w.tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')
    )
);

-- 4. Service Role Superuser Bypass
CREATE POLICY workspaces_service_role_bypass ON workspaces
FOR ALL TO service_role USING (true) WITH CHECK (true);
```

---

## 3. API Contracts & Interface Standards

### 3.1 Core Endpoints & Schemas

All API contracts enforce strict JSON request/response formats, RFC-3339 timestamps, and tenant header propagation (`X-Tenant-ID`).

#### `POST /api/v1/workspaces`
- **Purpose**: Creates a dedicated multi-agent collaborative workspace.
- **Headers**: `X-Tenant-ID: string (Required)`
- **Request Body**:
```json
{
  "name": "E-Commerce Optimization",
  "description": "Black Friday liquid theme & video assets",
  "template": "ecom_growth_v1"
}
```
- **Response (201 Created)**:
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "tenant_id": "tenant-alpha-001",
  "name": "E-Commerce Optimization",
  "status": "active",
  "created_at": "2026-08-28T09:00:00Z",
  "updated_at": "2026-08-28T09:00:00Z"
}
```

#### `POST /api/v1/swarm/run`
- **Purpose**: Initiates task decomposition and dispatches swarm agents.
- **Request Body**:
```json
{
  "workspace_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "goal": "Generate promotional Remotion video and update Liquid promo banner",
  "agents": ["dnk_video_ai_creator", "dnk_shopify"],
  "mode": "parallel"
}
```
- **Response (202 Accepted)**:
```json
{
  "task_id": "task_e587b129",
  "status": "in_progress",
  "dag_nodes": 2,
  "assigned_agents": ["dnk_video_ai_creator", "dnk_shopify"]
}
```

### 3.2 Error Model & Error Codes

All errors conform to the standard DNK structured error response format:

```json
{
  "error": {
    "code": "TENANT_ACCESS_DENIED",
    "message": "Access to workspace 7c9e6679 forbidden for tenant tenant-beta-002",
    "details": {
      "tenant_id": "tenant-beta-002",
      "resource_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
    },
    "timestamp": "2026-08-28T09:30:00Z",
    "request_id": "req_88f910ab"
  }
}
```

| HTTP Status | Error Code | Description | Action / Recovery |
|---|---|---|---|
| **400** | `INVALID_PAYLOAD` | Request validation error against Pydantic schema | Fix request payload format |
| **401** | `UNAUTHORIZED` | Missing or expired JWT / API key | Re-authenticate or refresh token |
| **403** | `TENANT_ACCESS_DENIED` | RLS violation or cross-tenant query attempt | Ensure matching `X-Tenant-ID` header |
| **404** | `RESOURCE_NOT_FOUND` | Specified workspace, node, or task not found | Verify UUID existence |
| **429** | `RATE_LIMIT_EXCEEDED` | Request threshold exceeded | Back off and retry with exponential delay |
| **500** | `INTERNAL_AGENT_ERROR` | Uncaught failure during swarm execution | Check SCONES error distillation log |

### 3.3 Rate Limiting & Throttling
- **Standard Tier**: 120 requests/minute per tenant.
- **Burst Tier**: 250 requests/minute per tenant.
- **AI Execution Tier (`/swarm/run`)**: 20 concurrent tasks per workspace.
- **Header Signals**:
  - `X-RateLimit-Limit: 120`
  - `X-RateLimit-Remaining: 114`
  - `X-RateLimit-Reset: 1756371600`

---

## 4. Deployment, Orchestration & Operations

### 4.1 Service Topology (Docker Compose)

The production stack consists of 8 interconnected microservices:

```mermaid
graph TD
    Client[Web & API Clients] --> Gateway[Traefik / Nginx Gateway]
    Gateway --> API[dnk-api :8000]
    Gateway --> UI[dnk-frontend :3000]
    
    API --> PG[(PostgreSQL :5432)]
    API --> PGV[(pgvector :5432)]
    API --> REDIS[(Redis :6379)]
    
    API --> SwarmEngine[Swarm Multi-Agent Core]
    SwarmEngine --> MediaService[dnk-media-remotion :8081]
    SwarmEngine --> ShopifyService[dnk-shopify-vite :8082]
    SwarmEngine --> IsolatedFS[dnk-isolated-fs :8083]
```

### 4.2 Environment Variable Matrix

| Variable Name | Required | Default / Example | Purpose |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | `postgresql://dnk:pwd@postgres:5432/dnk_os` | Main relational DB connection |
| `VECTOR_DB_URL` | **Yes** | `postgresql://dnk:pwd@pgvector:5432/dnk_vectors` | pgvector vector store URL |
| `REDIS_URL` | **Yes** | `redis://redis:6379/0` | Cache and message bus connection |
| `CHECKPOINTER_BACKEND` | **Yes** | `postgres` | LangGraph persistence backend (`postgres` / `memory`) |
| `JWT_SECRET_KEY` | **Yes** | `secret_32_bytes_min_...` | Auth token signing |
| `APP_CURRENT_TENANT_ID`| Dynamic | `tenant-alpha-001` | Session-level tenant context for RLS |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARN`, `ERROR`) |
| `CORS_ORIGINS` | No | `http://localhost:3000,https://app.dnk-e.com` | Allowed CORS origins |

### 4.3 Health Check Standards

Each container and service provides automated `/health` probes returning status, subsystem latencies, and uptime.

```json
// GET /health
{
  "status": "healthy",
  "version": "3.0.0",
  "timestamp": "2026-08-28T09:45:00Z",
  "checks": {
    "database": "connected",
    "vector_store": "connected",
    "redis": "connected",
    "swarm_workers": 14,
    "active_workspaces": 5
  }
}
```

- **Liveness probe**: HTTP GET `/health` every 15 seconds.
- **Readiness probe**: Validates DB pool acquisition and Redis ping within 3 seconds.

### 4.4 Rollback & Disaster Recovery Procedures

1. **Alembic Database Rollback**:
   ```bash
   # Revert migration 1 step back
   uv run alembic downgrade -1
   
   # Revert to specific revision
   uv run alembic downgrade 004
   ```

2. **Docker Zero-Downtime Rolling Update**:
   ```bash
   docker compose up -d --no-deps --build dnk-api
   ```

3. **PostgreSQL Point-In-Time Recovery (PITR)**:
   - Automated WAL archiving to S3/Object Storage.
   - Daily automated logical dumps (`pg_dump`) executed at 03:00 UTC.

4. **Master Quality Invariant**:
   - Every release candidate MUST pass 100% of test suites prior to deployment:
   ```bash
   bash scripts/verify_all.sh
   ```

---

*DNK-STD-0080 — Canonical Technical Specification approved by Maxim (DNK-e.com).*
