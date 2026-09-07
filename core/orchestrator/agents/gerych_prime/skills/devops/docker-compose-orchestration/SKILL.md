---
name: docker-compose-orchestration
description: Use when building multi-tier Docker and Compose stacks.
version: 1.0.0
author: DNK OS Swarm
license: MIT
metadata:
  hermes:
    tags: [docker, compose, fast-api, nextjs, pgvector, redis, devops]
    related_skills: [production-promotion-and-standby-management, sdlc-review]
---

# Docker and Compose Monorepo Orchestration

## When to Use
Use this skill when containerizing, configuring, optimizing, or troubleshooting multi-tier services (FastAPI/Python, Next.js/Node, PostgreSQL+pgvector, Redis, Nginx) within monorepos.

## Core Architectural Invariants

1. **Independent Service Containers**:
   - Backend (Python/FastAPI) and Frontend (Next.js) live in isolated containers.
   - Database (`pgvector/pgvector:pg16`) and Cache (`redis:7-alpine`) have independent volumes and isolated internal network bridges.
2. **Multi-Stage Builds & Minimal Runtime Footprints**:
   - Python: Separate build stage (`gcc`, `libpq-dev`, virtualenv build) from slim runtime runner (`python:3.11-slim` or `python:3.12-slim`).
   - Node/Next.js: Three-tier multi-stage (`deps` -> `builder` -> `runner` on `node:20-alpine`) utilizing Next.js `output: "standalone"`.
3. **Explicit Build Context Optimization**:
   - Never build a Docker image without a comprehensive `.dockerignore` excluding `.venv`, `node_modules`, `.next`, `dist`, `.git`, and test caches. Large contexts cause 300s+ timeout hangs.

---

## Standard Orchestration Steps

### 1. Build Context Hygiene (`.dockerignore`)
Ensure `.dockerignore` exists at repo root:
```text
.git
.venv
**/node_modules
apps/web/.next
apps/web/out
**/__pycache__
**/.pytest_cache
*.log
```

### 2. Multi-Stage Dockerfiles

#### FastAPI Backend (`Dockerfile.backend`)
- Target: `/app` working directory.
- Pre-install system dependencies (`gcc`, `libpq-dev`, `curl`).
- Install dependencies into `/opt/venv` and bind `ENV PATH="/opt/venv/bin:$PATH"`.
- Include test framework (`pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`) so verification can run directly in the container.
- Run as non-root user (`appuser:10001`).

#### Next.js Frontend (`Dockerfile.frontend`)
- Target: `node:20-alpine` with `libc6-compat`.
- During dependency installation, invoke `npm install --legacy-peer-deps --ignore-scripts` to bypass native compilation failures (e.g. `node-gyp`, `canvas`) in headless containers.
- **BuildKit Cache Mounts (10x Speedup)**:
  - Cache npm package downloads: `RUN --mount=type=cache,target=/root/.npm npm install ...` in `deps`.
  - Cache Next.js incremental build artifacts: `RUN --mount=type=cache,target=/app/apps/web/.next/cache npm run build` in `builder`.
  - Reduces rebuild times from ~90s down to 10–15s when changing source files.
- Copy standalone output:
  - `COPY --from=builder /app/apps/web/.next/standalone ./`
  - `COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static`
  - `COPY --from=builder /app/apps/web/public ./apps/web/public`
- Run as `nextjs:nodejs` (UID 10001).

### 3. Docker Compose Configuration (`docker-compose.yml`)
- Define services: `backend`, `frontend`, `postgres`, `pgvector`, `redis`.
- Declare healthchecks for each service (`/health` HTTP check for API, `pg_isready` for Postgres, `redis-cli ping` for Redis).
- Bind named volumes for database persistence (`postgres_data`, `redis_data`).
- Define local development binds (`./apps/api:/app/apps/api`) for live hot-reload without container rebuilds.

### 4. Verification Workflow
Always verify container health and in-container test suites before certifying completion:
```bash
# 1. Start all services in detached mode
docker compose up -d

# 2. Check service health
docker compose ps

# 3. Test HTTP endpoints
curl -fsS http://localhost:8000/health
curl -I http://localhost:3000/

# 4. Execute test suite INSIDE backend container
docker compose exec backend pytest tests/deployment/ -v

# 5. Inspect tail logs for unhandled exceptions
docker compose logs --tail=50
```

---

## Critical Pitfalls & Distilled Workarounds

| Pitfall | Symptom | Root Cause | Distilled Fix |
|---|---|---|---|
| **Build Context Bloat** | `docker build` times out (>300s) | Sending `.venv` and `node_modules` (>200MB) to Docker daemon | Add `.venv`, `node_modules`, `.next` to root `.dockerignore`. |
| **Native C++ Addon Build Failure** | `npm install` exits with error compiling `node-gyp` or `canvas` in Alpine | Missing Python / build tools in Alpine | Use `npm install --legacy-peer-deps --ignore-scripts`. |
| **PostgreSQL Credential Lockout** | `FATAL: password authentication failed for user "..."` | Re-using an existing `postgres_data` volume initialized with previous credentials | Run `docker compose down -v` to reset data volumes cleanly during credential changes. |
| **Scale / Replica Conflict** | Compose error: `can't set container_name as container name must be unique` | Setting fixed `container_name` on services using `deploy.replicas > 1` | Remove explicit `container_name` on horizontally scaled services in `docker-compose.prod.yml`. |
| **Next.js Standalone Missing Assets** | Webpage renders unstyled HTML (FOUC), `/_next/static/css/*.css` returns 404 | Next.js `output: "standalone"` does NOT bundle `.next/static` or `public` into standalone folder | Copy `.next/static` to `.next/standalone/.next/static` and `public` to `.next/standalone/public` in builder and verify in `CMD`. |
| **In-Container Test Import Error** | `ModuleNotFoundError: No module named 'apps'` inside `docker compose exec backend pytest` | Container `PYTHONPATH` does not include root monorepo | Set `ENV PYTHONPATH="/app:/app/services"` in `Dockerfile.backend`. |
| **Stale Frontend Image in Monorepo** | Next.js serves stale HTML/routes after modifying `apps/web/` despite restarting `dnk_frontend` | `Dockerfile.frontend` copies `apps/web/` into image at build time without bind mounts | Execute `docker compose build frontend && docker compose up -d frontend` to rebuild and recreate runner container. |
| **Slow Next.js Container Rebuilds** | `docker compose build frontend` takes 90–120s on every minor source change | Re-downloading npm packages and discarding `.next/cache` across Docker builds | Use BuildKit cache mounts: `--mount=type=cache,target=/root/.npm` during install and `--mount=type=cache,target=/app/apps/web/.next/cache` during build. |
| **Daemon Foreground Command Lock** | Tool hook flags `docker compose up -d` as long-lived server process | Agent sandbox heuristic detects service start commands | Run `terminal(command="docker compose up -d ...", background=True, notify_on_complete=True)` and await completion via `process(action='wait')`. |
| **Postgres Exec Role Mismatch** | `FATAL: role "postgres" does not exist` during `docker exec` query | Default Postgres user overridden by `POSTGRES_USER=dnk` in compose env | Inspect container env via `docker exec <cnt> env \| grep POSTGRES` and use `-U dnk -d dnk_os`. |
| **Staging Rate-Limit (429) Invalidation** | Benchmarks report false positive failures with HTTP 429 | Testing staging without `TESTING=1` activates SecurityMiddleware rate limits | Track HTTP 429 as expected defensive behavior; apply client-side backoff or dedicated metric counters. |
| **Next.js Rewrites Internal Proxy Failure** | `connect ECONNREFUSED 127.0.0.1:8000` / HTTP 500 HTML response on `/api/*` / JSON parse error `Unexpected token 'I'` | Next.js compiles `routes-manifest.json` during `next build` (builder stage). If `BACKEND_INTERNAL_URL` is omitted in the builder stage, Next.js bakes in the fallback `http://localhost:8000`. Inside Docker, `127.0.0.1` hits frontend itself. | Set `ENV BACKEND_INTERNAL_URL="http://backend:8000"` in BOTH `builder` and `runner` stages of `Dockerfile.frontend` and in `docker-compose.yml`. In store, read `res.text()` before `res.json()` on non-200. |
| **Bind-Mount Dependency Drift** | `ModuleNotFoundError: No module named '<pkg>'` on `docker restart` (e.g. `prometheus_client`) | Code in bind-mount (`apps/`, `services/`) imports new dependency added after container image build | Hotfix: `docker exec -u root <cnt> /opt/venv/bin/pip install <pkg>`. Codebase: wrap optional telemetry/monitoring in `try...except ImportError`. |
| **Multi-Statement DDL Bootstrap Failure** | `sqlite3.ProgrammingError: You can only execute one statement at a time.` | Executing multi-statement SQL migration string via `cursor.execute(...)` | Use `cursor.executescript(...)` instead of `cursor.execute(...)` for multi-statement DDL bootstrap scripts. |

---

## Linked References
- Detailed Monorepo recipes & troubleshooting: see `references/monorepo_pitfalls_and_recipes.md`.
- Staging container benchmarks & telemetry: see `references/staging_performance_validation_and_container_benchmarks.md`.
