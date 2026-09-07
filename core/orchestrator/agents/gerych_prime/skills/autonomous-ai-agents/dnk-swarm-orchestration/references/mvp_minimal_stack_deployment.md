# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/mvp_minimal_stack_deployment.md"
# purpose: "Technical Reference for Minimal MVP Compose Stacks & Port Verification Protocols in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🚀 Minimal MVP Stack Deployment & Automated Port Verification

## Overview
When deploying quick-feedback MVP stages (such as the Canvas Studio MVP), the deployment should remain highly lightweight, fast to compile, and isolated from heavy-weight monitoring or analytics services (such as Prometheus, Grafana, or Jaeger) which are deferred to production.

## 🏗️ Core MVP Stack Layout
A typical MVP stack requires exactly four core services:
1. **Web App Frontend** (e.g., `canvas-web` on port `3000`)
2. **API Backend** (e.g., `canvas-api` on port `8000`)
3. **Primary Database** (e.g., `postgres` on port `5432`)
4. **Caching/Broker Layer** (e.g., `redis` on port `6379`)

### Modern Compose V2 Syntax Invariant
In modern Docker Compose V2, omit the top-level `version: '3.8'` attribute. Including it triggers:
`level=warning msg="the attribute version is obsolete, it will be ignored, please remove it to avoid potential confusion"`.
Define services directly at the top level under `services:`.

### Clean Multi-Stage Build Strategy
API backends must use multi-stage Docker builds to keep image size small:
- **Builder Stage**: Uses a complete development image to install system packages, build wheel files, and resolve requirements.
- **Runtime Stage**: A minimal, security-hardened `slim` base image (e.g., `python:3.11-slim`) copying only the installed packages and virtual environment.

## 🏥 Next.js 14 App Router Native Health Probe
For Next.js App Router frontends (`apps/web/`), establish a dedicated health probe route handler at `app/health/route.ts`:

```typescript
// apps/web/app/health/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'canvas-web'
  });
}
```

## 🗄️ PostgreSQL Isolated Schema Auto-Creation Invariant
When SQLAlchemy models target a non-default schema (e.g. `__table_args__ = {"schema": "hub_memory"}`), calling `Base.metadata.create_all(bind=engine)` does **not** create the schema itself on clean PostgreSQL volumes. This results in:
`psycopg2.errors.InvalidSchemaName: schema "hub_memory" does not exist`.

### Required Lifespan Initialization Pattern:
Before calling `Base.metadata.create_all`, explicitly execute `CREATE SCHEMA IF NOT EXISTS` within an engine transaction block:

```python
AUTO_CREATE_SCHEMA = os.getenv("AUTO_CREATE_SCHEMA", "true").lower() == "true"

if AUTO_CREATE_SCHEMA:
    with engine.begin() as conn:
        from sqlalchemy import text
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS hub_memory"))
    Base.metadata.create_all(bind=engine)
```
This guarantees production-grade schema isolation on PostgreSQL v16 without requiring silent fallback to SQLite.

## ⚡ Pre-Flight Port Conflict Verification Protocol
Since developers frequently run the full development environment on their machines, deploying an MVP stack on standard ports (`3000`, `8000`, `5432`, `6379`) will fail if the background stack is active.

### The Verification Pattern (POSIX Shell)
Before running `docker compose up`, always programmatically check for occupied ports and offer options or auto-terminate:

```bash
CHECK_PORTS=(3000 8000 5432 6379)
CONFLICT=false

for port in "${CHECK_PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️ Port $port is already in use!"
        CONFLICT=true
    fi
done

if [ "$CONFLICT" = true ]; then
    echo "❌ Port conflicts detected. Please stop the conflicting services before proceeding."
    exit 1
fi
```

## 🔍 Real-Time Probe & Health Gate Verification
Never consider deployment complete when `docker compose up -d` exits with status `0`. Always verify service readiness:

1. **Wait & Loop**: Probe the health endpoint up to $N$ times with exponential backoff.
2. **Web Health Check**: Probe `http://localhost:3000/health` with fallback to `http://localhost:3000/` (for backward compatibility if pre-existing containers have not yet rebuilt the route handler).
3. **API Health Check**: Probe `http://localhost:8000/health`.

### Verification Code:
```bash
echo "🔍 Verifying services health..."
for i in {1..12}; do
    API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || true)
    WEB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health || curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ || true)
    
    if [ "$API_STATUS" = "200" ] && [ "$WEB_STATUS" = "200" ]; then
        echo "🟢 All services are healthy!"
        break
    fi
    echo "⏳ Waiting for services... (attempt $i/12)"
    sleep 5
done
```

## 🛡️ Documentation & Handoff Path Hygiene Invariant
Pre-commit sanitizers (`verify_all.sh` / `test_no_raw_user_absolute_paths`) scan Markdown reports, notes, and templates for raw home directories (`/Users/...`).
- **Rule**: Never print or commit literal user paths (e.g. `/Users/kuzmenko.top/...`) even in explanatory prose, error transcripts, or historical notes.
- **Remediation**: Use placeholders such as `<USER_HOME>/...` or `[REDACTED_USER_PATH]` when capturing diffs, postmortems, or setup steps in documentation.

## 📋 Beta Launch Operational Cadence & 5-Minute Onboarding Protocol
For early MVP releases and beta cohorts (e.g. 5–10 beta testers over 7 days):
1. **Core Experience Targets**:
   - **SUS (System Usability Score)**: > 75
   - **TTFV (Time To First Value)**: < 5 minutes
   - **NPS**: > 50
2. **Canonical 5-Minute User Onboarding Sequence**:
   - Access UI at `http://localhost:3000`
   - Trigger "E-Com швидкий старт" wizard (Goal, Audience, Visual Style, UTP)
   - Click `⚡ AI Co-Pilot` on the Strategy node to initiate streaming AI response
   - Trigger Swarm Propagation: `Strategy` ➔ `Design` (palette) ➔ `Code` (Liquid AST) ➔ `Kanban` (tasks)
   - Export canvas as `.canvas` (Obsidian compatible) or `JSON`
3. **Dual-Channel Output Delivery (Terminal + Markdown)**:
   - When preparing release briefings or execution summaries for Maxim, format terminal responses as clean, non-markdown ASCII tables/sections for native CLI rendering.
   - Concurrently generate a permanent, structured Markdown report with valid `DNK-STD-0075` MRH headers under `docs/reports/` for human review and archival.

## 🛠️ Rapid Triage Runbook
- **Port Conflict Flush**: `lsof -i :3000 -i :8000 -i :5432 -i :6379 | awk 'NR>1 {print $2}' | xargs kill -9`
- **Docker VM Disk Saturation & Lock File Failure**: If Postgres container crashes with `FATAL: could not write lock file "postmaster.pid": No space left on device` causing compose failure `dependency failed to start: container ... exited (1)`:
  * Check disk usage: `docker system df`
  * Prune accumulated build cache: `docker builder prune -f && docker system prune -f`
  * Reclaim broken volumes: `docker compose -f docker-compose.mvp.yml down -v`
  * Rerun deployment: `./scripts/deploy-mvp.sh`
- **Workspace ID UUID Type Invariant for Canvas API**:
  * Canvas endpoints require the `X-Workspace-Id` header (e.g. `POST /api/v1/canvases`).
  * Since `hub_memory.canvas_documents.workspace_id` is a native `UUID` column, passing arbitrary non-UUID strings (e.g. `ws-alpha-001`) causes:
    `sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input syntax for type uuid`.
  * Always supply a valid UUID string (e.g. `a0000000-0000-0000-0000-000000000001` or generated via `uuid.uuid4()`).
- **Container Log Inspection**: `docker compose -f docker-compose.mvp.yml logs -f <service>`
- **Postgres Readiness Probe**: `docker compose -f docker-compose.mvp.yml exec postgres pg_isready -U user -d dnk_canvas`
- **Clean State Teardown**: `docker compose -f docker-compose.mvp.yml down -v && ./scripts/deploy-mvp.sh`

