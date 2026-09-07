# Staging Performance Validation & Container Benchmarking Recipes

This guide documents the procedures, metrics collection techniques, and pitfalls when running performance and load tests against real Docker containers in a staging environment without test mocking flags (`TESTING=1`).

---

## 1. Real Container vs In-Process TestClient

| Dimension | In-Process (`TestClient(app)`) | Staging Live Container (`httpx`/`websockets`) |
|---|---|---|
| **Network Stack** | Direct Python ASGI memory calls | Real TCP/IP, loopback socket stack, Nginx gateway |
| **Security Middleware** | Usually bypassed via `TESTING=1` | Active rate limiting, DDoS protections, IP tracking |
| **Concurrency Model** | GIL-bound thread pool within pytest | Real multiprocessing (`uvicorn` workers) + container isolation |
| **Status Codes** | 429 is masked or avoided | **HTTP 429 Too Many Requests** is expected under burst traffic |
| **Resource Saturation** | Measures local Python process | Measures real container CPU, RAM, Network I/O, Block I/O |

---

## 2. Telemetry Extraction Without External Dependencies

Collect telemetry directly from Docker daemon and container CLIs every 5–30 seconds during load runs:

### Docker Container Resource Stats
```bash
docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}"
```
Output format parses easily in Python/bash:
`dnk_backend,0.27%,310.9MiB / 3.825GiB,3.39MB / 4.6MB,157MB / 242kB`

### PostgreSQL Active Connections
```bash
docker exec dnk_postgres psql -U dnk -d dnk_os -t -A -c "SELECT count(*) FROM pg_stat_activity;"
```
*Note*: Always inspect container environment (`docker exec <container> env | grep POSTGRES`) to avoid role mismatches (e.g. using `postgres` instead of configured `POSTGRES_USER=dnk`).

### Redis Connected Clients
```bash
docker exec dnk_redis redis-cli info clients | grep connected_clients | cut -d: -f2
```

---

## 3. Handling Rate Limiting (HTTP 429) in Load Benchmarks

When staging runs without `TESTING=1`:
1. **Never treat 429 as an unhandled error**: In test runners, track `http_429_count` separately from unhandled 5xx errors or network drops.
2. **Client Session Adaptation**:
   - Provide an option to route traffic either to `TestClient` (for fast local CI) or via `STAGING_URL` / `STAGING_WS_URL` to the live container gateway.
   - Example pattern:
   ```python
   staging_url = os.environ.get("STAGING_URL")
   if staging_url:
       with httpx.Client(base_url=staging_url, timeout=15.0) as client:
           resp = client.get("/health/ready")
           if resp.status_code == 429:
               count_429 += 1
   ```
3. **WebSocket Handshake 429**:
   - Catch `InvalidStatusCode` or string exceptions containing `429` during `websockets.sync.client.connect`.
