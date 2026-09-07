# --- DNK-MRH-HEADER ---
# mrh_id: "DEPLOYMENT_MVP.md"
# purpose: "Master Deployment and Operations Runbook for DNK OS Canvas MVP"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-03"
# --- END DNK-MRH-HEADER ---

# 🚀 DNK OS Canvas MVP Deployment & Operations Manual

This runbook provides the definitive instructions for deploying, operating, and verifying the Minimal Viable Product (MVP) of the **DNK OS Canvas Studio**.

---

## 📋 System Requirements
- **Docker Engine**: >= 24.0.0
- **Docker Compose**: >= 2.20.0
- **Node.js**: >= 20.0.0 (optional, for local frontend dev)
- **Python**: >= 3.12 (optional, for local API dev)
- **Required Ports**: `3000` (Web UI), `8000` (API Gateway), `5432` (PostgreSQL), `6379` (Redis)

---

## ⚡ Quick Start: Automated Deployment

The fastest way to deploy the complete MVP stack with pre-flight health validations is via the dedicated deployment script:

```bash
# Make script executable (if needed)
chmod +x ./scripts/deploy-mvp.sh

# Deploy MVP stack with automated health verification
./scripts/deploy-mvp.sh
```

### Manual Deployment Instructions

If you prefer direct Docker Compose commands:

```bash
# 1. Build images and start all 4 services in the background
docker compose -f docker-compose.mvp.yml up -d --build

# 2. Check service status
docker compose -f docker-compose.mvp.yml ps

# 3. Stream real-time logs
docker compose -f docker-compose.mvp.yml logs -f

# 4. Tear down the stack
docker compose -f docker-compose.mvp.yml down
```

---

## 📊 Topology & Service Matrix

The MVP runtime consists of **4 containerized microservices**:

| Service Name | Container / Image | Internal Port | Host Port | Role |
| :--- | :--- | :--- | :--- | :--- |
| **`canvas-web`** | `dnk_hub-canvas-web` (Node 20 Alpine) | `3000` | `3000` | Next.js 14 Visual Shell & React Flow Canvas UI |
| **`canvas-api`** | `dnk_hub-canvas-api` (Python 3.12 Slim) | `8000` | `8000` | FastAPI Gateway, AI Swarm Orchestration & Session Store |
| **`postgres`** | `postgres:16-alpine` | `5432` | `5432` | PostgreSQL 16 database (`dnk_canvas`) with `hub_memory` schema |
| **`redis`** | `redis:7-alpine` | `6379` | `6379` | Redis 7 distributed session cache and real-time pub/sub bus |

---

## 🗄️ Database Architecture & Schema Isolation

- **PostgreSQL Version**: 16 Alpine
- **Database Name**: `dnk_canvas`
- **Default User**: `user`
- **Isolated Schema**: `hub_memory`
- **Schema Auto-Creation Invariant**:
  The FastAPI service (`canvas-api`) automatically executes `CREATE SCHEMA IF NOT EXISTS hub_memory` on lifespan startup before binding SQLAlchemy models (`Base.metadata.create_all`).
- **Core Entities Managed**:
  - `users` — Authentication & user profiles
  - `canvases` — Canvas state, graph metadata & configuration
  - `nodes` — Canvas node specifications (Strategy, Design, Code, Kanban)
  - `edges` — Node connection links & swarm propagation topologies
  - `sessions` — Live user and agent collaboration sessions
- **Zero-SQLite Invariant**: In MVP Docker mode, all writes land directly in PostgreSQL with zero SQLite fallback.

---

## 🚦 Dual-Layer Health Checks

Verify that both public-facing and backend endpoints are functioning normally:

### 1. Backend API Health Check
```bash
curl -i http://localhost:8000/health
```
**Expected Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{"status":"ok"}
```

### 2. Frontend Web UI Health Check
```bash
curl -i http://localhost:3000/health
```
**Expected Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{"status":"healthy","service":"canvas-web"}
```

---

## 🔍 Troubleshooting & Runbook

### 1. Port Conflicts (`Address already in use`)
If port `3000`, `8000`, `5432`, or `6379` is already bound by another process:
```bash
# Check what is listening on port 8000 or 5432
lsof -i :8000
lsof -i :5432

# Terminate offending processes or change host port mapping in docker-compose.mvp.yml
```

### 2. PostgreSQL Connection Failures
If `canvas-api` fails to connect to PostgreSQL:
```bash
# Check PostgreSQL container logs
docker compose -f docker-compose.mvp.yml logs postgres

# Verify PostgreSQL is accepting connections
docker exec -it $(docker compose -f docker-compose.mvp.yml ps -q postgres) pg_isready -U user -d dnk_canvas
```

### 3. Resetting Volumes & Clean Restart
If database credentials or state need a complete reset:
```bash
# Stop and remove volumes
docker compose -f docker-compose.mvp.yml down -v

# Redeploy from scratch
./scripts/deploy-mvp.sh
```

### 4. Viewing Detailed Logs
```bash
# API logs
docker compose -f docker-compose.mvp.yml logs -f canvas-api

# Web UI logs
docker compose -f docker-compose.mvp.yml logs -f canvas-web
```
