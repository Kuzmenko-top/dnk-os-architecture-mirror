# Docker Stack Live Verification, Multi-Stage Builds & Prune Protocol

## 1. Multi-Stage Dockerfile Target Hygiene
When `docker-compose.yml` specifies `target: <stage>` (e.g. `target: node-builder`), ensure the targeted stage has complete runtime directives:
- Explicit environment binding: `ENV HOSTNAME="0.0.0.0"` and `ENV PORT=3000` (Node/Next.js).
- Port exposure: `EXPOSE 3000`.
- Execution entrypoint: `CMD ["npm", "start"]`.
*Pitfall*: Without runtime directives in intermediate targets, Docker builds the image and immediately exits with `Exited (0)` upon container startup.

## 2. Mandatory Live Verification Probing (Zero-Assumption Rule)
Never claim a web or API service is "🟢 HTTP 200 OK" without running explicit terminal probes:
```bash
# 1. Container status check
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Real HTTP status check on frontend & backend
curl -s -o /dev/null -w "Frontend HTTP: %{http_code}\n" http://localhost:3000
curl -s -o /dev/null -w "Backend API HTTP: %{http_code}\n" http://localhost:8000/health

# 3. Backend health response payload
curl -s http://localhost:8000/health
```

## 3. Docker Image Bloat & Orphaned Container Cleanup
When Docker accumulates dangling multi-stage layers (>5-10 GB) or conflicting stopped containers:
```bash
# Step 1: Tear down current compose project with orphans
docker compose down --remove-orphans

# Step 2: Stop and remove any leftover conflicting containers
docker stop <container_ids> && docker rm <container_ids>

# Step 3: Prune all unreferenced images and build caches
docker image prune -a -f

# Step 4: Rebuild cleanly in background with completion notification
# (Via terminal background=true or CLI)
docker compose up -d --build
```
