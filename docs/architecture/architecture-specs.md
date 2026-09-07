# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture-specs.md"
# purpose: "Canonical Architecture Specifications, Topology and Multi-Agent Mermaid Diagrams for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "3.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🏛️ DNK OS MVP — Architecture Specifications & Mermaid Blueprints

This document contains the definitive architectural blueprint, data flow dynamics, component hierarchy, and deployment topology for **DNK OS MVP Multi-Agent Core**.

---

## 📑 Table of Contents
1. [System Architecture Diagram](#1-system-architecture-diagram)
2. [Multi-Agent Flow Sequence](#2-multi-agent-flow-diagram)
3. [Component Architecture Hierarchy](#3-component-architecture)
4. [Data Flow Pipeline](#4-data-flow-diagram)
5. [Deployment Topology & Container Mesh](#5-deployment-topology)
6. [Security & Isolation Matrix](#6-security--isolation-matrix)

---

## 1. System Architecture Diagram

The DNK OS MVP adopts a tiered multi-layer architecture separating Client Interface, Reverse Proxy / Load Balancing, Horizontally Scalable Workers, and Distributed Data Storage.

```mermaid
graph TB
    subgraph "Client Layer"
        A[Browser / API Client]
    end
    
    subgraph "Nginx Layer"
        B[Nginx Reverse Proxy :80]
    end
    
    subgraph "Load Balancer"
        C[Round-Robin LB]
    end
    
    subgraph "API Cluster"
        D1[FastAPI Worker 1 :8000]
        D2[FastAPI Worker 2 :8000]
        D3[FastAPI Worker 3 :8000]
    end
    
    subgraph "Data Layer"
        E1[PostgreSQL 16 :5435]
        E2[Redis 7 :6379]
        E3[pgvector :5433]
    end
    
    subgraph "Frontend"
        F[Next.js 14 :3000]
    end
    
    A --> B
    B --> C
    C --> D1
    C --> D2
    C --> D3
    D1 --> E1
    D2 --> E1
    D3 --> E1
    D1 --> E2
    D2 --> E2
    D3 --> E2
    D1 --> E3
    D2 --> E3
    D3 --> E3
    F --> B
```

### Layer Details:
- **Client Layer**: Desktop browsers and HTTP/WebSocket clients communicating via REST and SSE.
- **Nginx Layer**: High-performance ingress proxy handling SSL, gzip compression, client rate limiting, and reverse proxying.
- **Load Balancer**: Round-robin distribution of API traffic across the worker pool.
- **API Cluster**: Horizontally scalable FastAPI worker instances (`dnk-api-1`, `dnk-api-2`, `dnk-api-3`).
- **Data Layer**:
  - `PostgreSQL 16`: Relational state, audit logs, Row-Level Security (RLS).
  - `Redis 7`: High-speed session checkpointing, distributed locks, Pub/Sub.
  - `pgvector`: 1536-dimensional embeddings for SCONES memory and RAG.
- **Frontend**: Next.js 14 App Router hosting React Flow Canvas and Stitch interface.

---

## 2. Multi-Agent Flow Diagram

Orchestration sequence showing user interaction, supervisor delegation, worker concurrency, and streaming response lifecycle.

```mermaid
sequenceDiagram
    participant U as User
    participant N as Nginx
    participant S as Supervisor (Antigravity)
    participant W1 as Worker 1
    participant W2 as Worker 2
    participant W3 as Worker 3
    participant DB as PostgreSQL
    participant R as Redis
    participant V as pgvector
    
    U->>N: POST /api/generate
    N->>S: Route to Supervisor
    S->>W1: Delegate Task 1
    S->>W2: Delegate Task 2
    S->>W3: Delegate Task 3
    W1->>DB: Query
    W2->>R: Cache
    W3->>V: Vector Search
    W1-->>S: Result 1
    W2-->>S: Result 2
    W3-->>S: Result 3
    S-->>N: Aggregate Results
    N-->>U: SSE Stream Response
```

### Execution Steps:
1. **User Dispatch**: The client submits a multi-step task generation prompt.
2. **Supervisor Delegation**: The `Antigravity` supervisor parses the TaskDNA and partitions work across workers.
3. **Parallel Worker Execution**:
   - `Worker 1` queries PostgreSQL for workspace entities and RLS state.
   - `Worker 2` interacts with Redis for cached session contexts and checkpointer keys.
   - `Worker 3` performs vector cosine-similarity lookups via `pgvector`.
4. **State Aggregation**: The supervisor compiles intermediate worker states into a unified DAG state.
5. **SSE Streaming**: Live tokens and status updates are piped through Nginx to the client browser in real time.

---

## 3. Component Architecture

Component hierarchy detailing the interface between framework adapters, orchestration core, checkpointers, and infrastructure.

```mermaid
graph LR
    subgraph "Adapters"
        A1[Transformers]
        A2[LlamaIndex]
        A3[CrewAI]
        A4[AutoGen]
        A5[LangGraph]
    end
    
    subgraph "Core"
        C1[Supervisor]
        C2[Worker]
        C3[Checkpointer]
        C4[ApprovalGate]
    end
    
    subgraph "Infrastructure"
        I1[Docker]
        I2[Nginx]
        I3[Load Balancer]
    end
    
    A1 --> C2
    A2 --> C2
    A3 --> C2
    A4 --> C2
    A5 --> C2
    C1 --> C2
    C2 --> C3
    C2 --> C4
    C2 --> I1
    I1 --> I2
    I2 --> I3
```

### Component Roles:
- **Framework Adapters (`adapters/`)**: Pluggable abstraction layer normalizing execution interfaces across HuggingFace Transformers, LlamaIndex, CrewAI, AutoGen, and LangGraph.
- **Core Engine (`core/`)**:
  - `Supervisor`: State machine coordinator managing multi-agent DAGs.
  - `Worker`: Execution nodes executing atomic tasks and tools.
  - `Checkpointer`: State snapshotting engine supporting Memory, SQLite, and Redis/PostgreSQL backends.
  - `ApprovalGate`: Human-in-the-loop security gate for sensitive and mutating actions.
- **Infrastructure**: Container runtime, reverse proxy, and routing fabric.

---

## 4. Data Flow Diagram

End-to-end data processing lifecycle from initial client ingress down to persistence storage and outbound event streaming.

```mermaid
flowchart TD
    subgraph "Request Flow"
        A[Client Request] --> B[Nginx :80]
        B --> C[Load Balancer]
        C --> D[API Worker 1/2/3]
    end
    
    subgraph "Processing"
        D --> E[Supervisor]
        E --> F[Worker]
        F --> G[Adapter]
    end
    
    subgraph "Data Access"
        G --> H[PostgreSQL]
        G --> I[Redis]
        G --> J[pgvector]
    end
    
    subgraph "Response"
        G --> K[SSE Stream]
        K --> L[Client]
    end
```

---

## 5. Deployment Topology

Container mesh topology mapping inter-container network links, ports, and isolation boundaries inside Docker Compose.

```mermaid
graph TB
    subgraph "Docker Network"
        subgraph "Frontend"
            F[Next.js :3000]
        end
        
        subgraph "Proxy"
            N[Nginx :80]
        end
        
        subgraph "API Cluster"
            A1[FastAPI :8000]
            A2[FastAPI :8000]
            A3[FastAPI :8000]
        end
        
        subgraph "Data"
            P[PostgreSQL :5435]
            R[Redis :6379]
            V[pgvector :5433]
        end
    end
    
    External[Client] --> N
    N --> F
    N --> A1
    N --> A2
    N --> A3
    A1 --> P
    A2 --> P
    A3 --> P
    A1 --> R
    A2 --> R
    A3 --> R
    A1 --> V
    A2 --> V
    A3 --> V
```

---

## 6. Security & Isolation Matrix

| Layer / Component | Security Control | Isolation Mechanism |
| :--- | :--- | :--- |
| **Ingress Proxy** | Nginx Rate Limiting (`rate_limit.conf`) | Max 100 req/sec per IP, burst=20 |
| **API Endpoints** | JWT Bearer & Workspace Header | `X-Workspace-ID` strict UUID RFC4122 validation |
| **Relational DB** | PostgreSQL RLS (Row-Level Security) | Tenant-isolated schemas (`ws-alpha-001`) |
| **Cache & State** | Key Namespacing & Token Expiry | `tenant:ws:session_id` strict key prefixing |
| **Approval Gate** | 2-Stage Verification Protocol | Human-in-the-loop blocking on destructive mutations |
