# Monorepo Docker & Compose Architecture Guide

This reference captures concrete patterns and lessons learned when containerizing high-performance fullstack monorepos with FastAPI, Next.js 14, PostgreSQL (pgvector), and Redis.

## 1. Next.js Standalone Build & Native Dependency Handling

Next.js apps in monorepos frequently import packages with native dependencies (e.g. `canvas`, `@napi-rs/*`, `sharp`, `node-gyp`). When building in lightweight Alpine containers (`node:20-alpine`), native builds fail unless Python, Make, and GCC are installed or script executions are suppressed.

### The Reliable Alpine Recipe
```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/
# Bypass native build scripts during container bundling:
RUN npm install --legacy-peer-deps --ignore-scripts

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm --prefix apps/web run build

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
```

### Static Asset Routing in Standalone Mode (FOUC Prevention)
Next.js `output: "standalone"` traces files required to run the server, but explicitly omits static assets. If `.next/static` is not mapped relative to where `server.js` executes, all stylesheet (`/_next/static/css/*.css`) and chunk requests return `404 Not Found`.

**Rule**:
- If `server.js` lives at `/app/.next/standalone/server.js`, static files must be placed at `/app/.next/standalone/.next/static` and `/app/.next/standalone/public`.
- Always embed a safe fallback in the Dockerfile `CMD` or post-build script:
```bash
if [ -d .next/standalone ]; then \
  (cp -rn .next/static .next/standalone/.next/ 2>/dev/null || true); \
  (cp -rn public .next/standalone/ 2>/dev/null || true); \
  node .next/standalone/server.js; \
fi
```

## 2. In-Container Test Execution for Backend

To verify backend health via `docker compose exec backend pytest tests/`:
- The container must include test requirements (`pytest`, `pytest-cov`, `pytest-asyncio`).
- Keep the test requirements inside a dedicated `/opt/venv` layer so production builds can either strip or isolate them.
- Ensure `PYTHONPATH` includes the repository root so sibling packages (e.g. `apps/api`, `services/`, `core/`) resolve identically to local virtual environments:
```dockerfile
ENV PYTHONPATH="/app:/app/services"
ENV PATH="/opt/venv/bin:$PATH"
```

## 3. PostgreSQL & pgvector Persistent Volume Gotchas

When testing new database credentials in Docker Compose:
- **Default PG Behavior**: PostgreSQL only executes scripts in `/docker-entrypoint-initdb.d/` and sets passwords when `/var/lib/postgresql/data` is empty.
- **The Stale Volume Trap**: If an existing volume named `postgres_data` is mounted, PostgreSQL reuses existing password hashes. Changing `POSTGRES_PASSWORD` in `docker-compose.yml` will NOT update the password inside the existing data directory.
- **Clean Reset**:
  ```bash
  docker compose down -v
  docker compose up -d
  ```
- **pgvector Extension Initialization**:
  Always ensure the database extension is enabled on container startup or via an initialization script:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

## 4. Production Compose High-Availability Invariants

- **Horizontal Scaling & `container_name`**: Never combine `deploy.replicas: N` (where N > 1) with `container_name`. Docker Compose requires container names to be unique; naming a scalable service causes an orchestration conflict.
- **Network Segmentation**: Separate edge traffic (Nginx -> Frontend / API) from database traffic:
  - `frontend_net`: Nginx <-> Next.js
  - `backend_net`: Nginx <-> FastAPI
  - `data_net`: FastAPI <-> PostgreSQL, Redis (no external port exposure in production)

## 5. Fast Local Verification Protocol (Hybrid Bind-Mount vs Standalone Rebuild)

When validating newly introduced API endpoints or frontend UI components locally:
- **FastAPI Backend (Bind-Mount)**: The backend container typically mounts repository code (`.:/app`). However, active Python worker processes do not detect new routers unless running with `--reload` or restarted. Run `docker restart dnk_backend` to immediately activate new routes. Test via:
  ```bash
  curl -s http://localhost:8000/api/v3/<endpoint> | jq .
  ```
- **Next.js Frontend (Standalone Image)**: Standalone production containers do not mount `apps/web/` live. To test updated UI:
  1. Fast BuildKit Rebuild:
     ```bash
     docker compose build frontend && docker compose up -d frontend
     ```
  2. Or run host dev server (`npm run dev`) on `apps/web/` for zero-build hot reload during active design turns.
- **Verification Delivery**: Always provide the user with:
  1. Direct browser URL (e.g. `http://localhost:3000/<route>`).
  2. 3 concrete visual test steps (what buttons to click, expected glow/badges, live drawer behavior).
  3. Terminal verification one-liners (`curl` or `docker logs`).

## 6. Monorepo Bind-Mount Dependency Drift & DDL Migrations

### Bind-Mount Dependency Drift Pattern
When working in local monorepos where backend source code is bind-mounted (`.:/app` or `./apps/api:/app/apps/api`), newly imported packages (e.g. `prometheus_client`, telemetry libraries) added to the repository cause runtime crashes on container restart if the container's isolated `/opt/venv` was built prior:
- **Instant Hotfix**:
  ```bash
  docker exec -u root <container_name> /opt/venv/bin/pip install <package_name>
  docker restart <container_name>
  ```
- **Code Defensive Pattern**:
  Always guard optional monitoring, tracing, or metrics collectors with defensive imports:
  ```python
  try:
      import prometheus_client
  except ImportError:
      prometheus_client = None
  ```

### Multi-Statement SQLite / DuckDB DDL Bootstrap
When migrating or bootstrapping database schemas from multiline SQL strings containing multiple semicolon-delimited statements:
- Standard `cursor.execute(sql)` raises `sqlite3.ProgrammingError: You can only execute one statement at a time.`
- Use `cursor.executescript(sql)` instead:
  ```python
  # Safe multi-statement DDL execution:
  cursor.executescript(schema_sql)
  ```

