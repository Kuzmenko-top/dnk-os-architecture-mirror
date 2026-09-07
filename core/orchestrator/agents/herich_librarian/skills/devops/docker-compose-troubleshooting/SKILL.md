---
name: docker-compose-troubleshooting
description: "Troubleshoot Docker Compose: disk, daemon, networks & build."
version: 1.0.0
author: Gerych Core + Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [docker, compose, containers, devops, troubleshooting, healthcheck]
    category: devops
    requires_toolsets: [terminal]
---

# Docker Compose Troubleshooting & Recovery

Systematic guide for diagnosing, unblocking, and verifying containerized workloads managed by Docker Compose.

## When to Use

Use this skill when:
- Docker build fails due to disk limits (`No space left on device`, read-only VM layer).
- Docker daemon / Desktop freezes or hangs (e.g. macOS `-1712` timeout).
- Containers restart continuously or get stuck in `unhealthy` state.
- Healthcheck probes fail with `Connection refused` or IPv4/IPv6 binding mismatches.
- API workers crash on missing runtime packages or missing system dynamic libraries.

## Diagnostic Protocol

### 1. Disk & Resource Exhaustion & macOS APFS Write Locks

When builds fail due to storage exhaustion or commands hang with `context deadline exceeded` / SQLite WAL write errors (`session storage could not be written`):

**Root Cause**: When available host storage on macOS drops below ~4-5 GB (>95% disk capacity), APFS restricts write operations and Docker VM socket operations hang indefinitely.

```bash
# 1. Check host & Docker VM storage allocation
df -h /
docker system df

# 2. Prune unused images, stopped containers, build cache, and volumes
docker system prune -af --volumes
docker builder prune -af

# 3. Clean user/system package manager caches if disk is critically low (<5GB)
npm cache clean --force 2>/dev/null || true
rm -rf ~/.cache/* 2>/dev/null || true
```

### 2. macOS Docker Desktop Hang Recovery

When `docker info` hangs or macOS reports `-1712`:

```bash
# Force terminate lingering backend daemons and stuck buildx workers
pkill -9 -f "com.docker.backend" || true
pkill -9 -f "docker-buildx" || true
pkill -9 -f "docker-agent" || true
sleep 3

# Launch Docker Desktop cleanly and poll until ready
open -a /Applications/Docker.app
until docker info > /dev/null 2>&1; do
  echo "Waiting for Docker daemon..."
  sleep 2
done
```

### 3. Python Multi-Stage Container Virtualenv Pattern

**Problem**: Using `pip install --user` in a multi-stage `builder` and `COPY --from=builder /root/.local /home/appuser/.local` in `runtime` fails with:
`failed to copy file info: failed to chmod ... /home/appuser/.local/...: read-only file system` (containerd overlayfs permission collision).

**Fix**: Use a standalone `/opt/venv` across stages:
```dockerfile
# Builder stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
```

### 4. `uv export` Requirements for Docker Builds

**Problem**: Default `uv export` outputs editable root packages (`-e .`) and hashes, causing `pip install -r requirements.txt` to crash inside Docker (`The editable requirement file:///app cannot be installed when requiring hashes`).

**Fix**: Export clean standalone requirements:
```bash
uv export --no-hashes --no-emit-project -o requirements.txt
```

### 5. Container Network & Healthcheck IPv4/IPv6 Binding

**Problem**: Container logs show service listening (e.g. `Local: http://<container-id>:3000`), but Docker healthcheck (`wget http://localhost:3000`) fails with `Connection refused`.

**Root Cause**: In modern Node.js/Next.js standalone runners or Python servers, the process binds strictly to the container hostname or IPv6, ignoring `127.0.0.1`.

**Fix**: Ensure `Dockerfile` sets explicit zero-binding:
```dockerfile
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000
```

### 6. Fast Triage of Multi-Service Stacks

```bash
# List service statuses
docker compose ps

# Inspect logs of failing or unhealthy service
docker compose logs <service-name> --tail=50

# Rebuild only the modified container without stopping others
docker compose up --build -d <service-name>
```

### 7. Port Conflicts & Stale Multi-Stack Collisions

**Problem**: Starting a container fails with `bind: address already in use` or opening `http://localhost:<port>` returns a stale/unexpected service (e.g. previous project's web frontend).

**Diagnostic**:
```bash
# 1. Identify which Docker container owns the published port
docker ps --filter "publish=<port>"

# 2. Check if a host-native daemon or process is listening
lsof -nP -iTCP:<port> -sTCP:LISTEN
```

**Fix**:
1. Stop the stale container from the legacy stack:
   ```bash
   docker stop <container-id-or-name>
   ```
2. Check the project's centralized port registry (e.g., `PORT_REGISTRY.md` or architectural specs) to confirm canonical port assignments before creating new bindings.

### 8. `container_name` vs `replicas > 1` Collision

**Problem**: Running `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` fails with:
`services.deploy.replicas: can't set container_name and api as container name must be unique: invalid compose project`

**Root Cause**: Docker Compose requires container names to be unique. Setting `container_name: dnk_api` in the base `docker-compose.yml` while defining `deploy.replicas: 3` in `docker-compose.prod.yml` creates a name collision.

**Fix**: Omit `container_name` from `docker-compose.yml` when service scaling (`replicas > 1`) is enabled in production overrides, allowing Compose to automatically append instance indices (e.g. `project-api-1`, `project-api-2`).

### 9. Next.js Standalone Runner API Proxying & CORS

**Problem**: Client-side Next.js components fetching `/api/canvas/...` return `404 Not Found` or `CORS` errors when Next.js standalone runner (`output: 'standalone'`) is served on port 3000 while FastAPI runs on port 8000.

**Fix**: Add an explicit `rewrites()` rule in `next.config.mjs`:
```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8000/api/:path*',
    },
  ];
}
```

## Pitfalls

- **OverlayFS Permission Errors in Multi-Stage Pip Builds:** Using `pip install --user` in root builder and copying `/root/.local` into non-root user directory can trigger `chmod read-only file system` errors. Always use `/opt/venv` across multi-stage boundaries.
- **Editable packages and hashes in requirements.txt:** Exporting via `uv export` includes `-e .` and hashes by default, breaking Docker `pip install`. Use `uv export --no-hashes --no-emit-project -o requirements.txt`.
- **Lingering Docker Buildx backend processes:** Quitting Docker Desktop via GUI often leaves background `docker-buildx` processes alive, blocking daemon restart. Kill them with `pkill -9 -f "docker-buildx"`.
- **Rebuilding everything blindly:** Rebuilding the entire stack on single-service fixes wastes time. Use `docker compose up --build -d <service>` for targeted iterations.
- **Overlooking lingering multi-stack containers:** Multiple Docker Compose projects often share common defaults (`3000`, `8000`, `5432`). Always check `docker ps --filter "publish=<port>"` when an unexpected UI/API responds.
- **Missing public directory in Next.js multi-stage build:** `COPY --from=builder /app/public ./public` in runner stage fails with `failed to calculate checksum ... "/app/public": not found` if `public/` does not exist in the source tree. Add `RUN mkdir -p public` in the builder stage or create `public/.gitkeep`.
- **Apt package name pitfalls in Debian/Ubuntu:** Debian/Ubuntu packages `ffmpeg` bundle `ffprobe` directly. Specifying `apt-get install ffmpeg ffprobe` causes `E: Unable to locate package ffprobe`.
- **Huge Docker build contexts:** Forgetting `data/` and `storage/` in `.dockerignore` sends gigabytes of media/cache to the Docker daemon (`transferring context: 1.5GB+`).
- **Ignoring host volume permissions:** When Postgres or Redis fail to boot, check volume mount permissions and port conflicts with host services.
- **Missing runtime libraries in slim images:** Python `psutil` or `asyncpg` require C-extensions or runtime shared libraries (`libpq5`).
- **`container_name` vs `replicas` collision in Docker Compose:** Hardcoding `container_name` in base `docker-compose.yml` breaks multi-instance scaling (`replicas > 1`) in compose overrides with `can't set container_name and api as container name must be unique`.
- **Missing API Proxying in Next.js Standalone Mode:** Client-side components calling relative `/api/...` routes fail with 404 or CORS in `standalone` Next.js builds unless `rewrites()` is explicitly configured in `next.config.mjs`.
