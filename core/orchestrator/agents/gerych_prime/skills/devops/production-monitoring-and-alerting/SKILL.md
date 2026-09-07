---
name: production-monitoring-and-alerting
description: Use when building health probes, metrics, or alerting.
author: "DNK-e.com Maksym & Gerych Prime"
license: "DNK-INTERNAL"
version: 1.0.0
metadata:
  hermes:
    tags: ["devops", "monitoring", "alerting", "prometheus", "fastapi"]
    related_skills: ["docker-compose-orchestration", "production-promotion-and-standby-management"]
---

# Production Monitoring & Alerting

Standardized procedures for designing, building, and verifying production-grade observability and alerting subsystems within Python / FastAPI microservices and distributed swarms.

## When to Use

- Building Kubernetes-compliant liveness (`/health/live`) and readiness (`/health/ready`) probe endpoints.
- Instrumenting services with Prometheus / OpenMetrics counters, histograms, and gauges.
- Setting up multi-channel alerting (Slack webhooks, SMTP email) with fingerprint deduplication and cooldowns.
- Writing isolated automated tests for health checks and alert managers.

## Core Architectural Invariants

1. **Liveness vs Readiness Probe Segregation**:
   - **Liveness (`/health/live`)**: Lightest possible heartbeat. Checks exclusively whether the application process and event loop are alive and accepting requests. NEVER call external databases, network caches, or disk I/O in liveness probes — transient external network partitions must not trigger container restarts.
   - **Readiness (`/health/ready`)**: Evaluates operational dependencies (PostgreSQL connection pool, Redis cache ping, critical storage disk capacity). Returns `503 Service Unavailable` if an essential dependency is dead, signaling load balancers and ingress to stop routing inbound traffic.
   - **Deep Diagnostics (`/health/detailed`)**: Comprehensive breakdown with individual component latencies, resource utilization, and error diagnostics for administrative dashboards and operators.

2. **OpenMetrics / Prometheus Collector Pattern**:
   - Utilize a dedicated `MetricsRegistry` wrapping `prometheus_client` with graceful fallback to standard text exposition format (version 0.0.4) if optional dependencies are missing.
   - Standard core metrics:
     - `http_requests_total(method, endpoint, status_code)` (Counter)
     - `http_request_duration_seconds(method, endpoint)` (Histogram with standard SLO buckets)
     - `system_memory_usage_bytes`, `system_cpu_usage_ratio` (Gauge)
     - `active_tasks_total(agent/worker, status)` (Gauge / Counter)
     - `alerts_dispatched_total(severity, channel, status)` (Counter)
   - Content-Type MUST be `text/plain; version=0.0.4; charset=utf-8`.

3. **Multi-Channel Alert Dispatch with Fingerprint Deduplication**:
   - Multi-channel delivery: Slack Webhook (rich attachments / blocks) + Email (SMTP with TLS and multipart HTML/text).
   - **Alert Throttling & Cooldown**: Compute deterministic fingerprint `f"{service}:{component}:{title}"` and record timestamp. Suppress identical non-critical alerts occurring within cooldown window (e.g., 300s).
   - **Critical Bypass**: Alerts with severity `CRITICAL` MUST bypass cooldown suppression to guarantee immediate visibility.

4. **Structured JSON Logging & Async ContextVars Tracing**:
   - Log output MUST be single-line JSON with ISO 8601 UTC timestamp, level, service name (`dnk-api`), UUID v4 `trace_id`, and `span_id`.
   - Propagate tracing context across async coroutines using Python standard `contextvars`. Never pass global mutable dictionaries across threads or task boundaries.
   - Entry points (HTTP `X-Trace-ID` headers, WebSocket handshakes, Swarm task dispatch) establish or inherit the `trace_id`.

## Implementation Guide

### 1. Health Probe Registry Pattern

```python
from enum import Enum
from typing import Dict, Any, Callable, Coroutine
from datetime import datetime, timezone
import time

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheckRegistry:
    def __init__(self, service_version: str = "1.0.0"):
        self.service_version = service_version
        self.start_time = time.time()
        self._probes: Dict[str, Callable[[], Coroutine[Any, Any, Dict[str, Any]]]] = {}

    def register_probe(self, name: str, probe_fn):
        self._probes[name] = probe_fn

    async def check_liveness(self) -> Dict[str, Any]:
        return {
            "status": HealthStatus.HEALTHY,
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def check_readiness(self) -> Dict[str, Any]:
        results = {}
        overall = HealthStatus.HEALTHY
        for name, probe in self._probes.items():
            res = await probe()
            results[name] = res
            if res.get("status") == HealthStatus.UNHEALTHY:
                overall = HealthStatus.UNHEALTHY
        return {"status": overall, "components": results}
```

### 2. Alert Manager with Fingerprint Rate-Limiting

```python
class AlertManager:
    def __init__(self, cooldown_seconds: int = 300):
        self.cooldown = cooldown_seconds
        self._last_dispatched: Dict[str, float] = {}
        self.channels: Dict[str, Any] = {}

    def is_throttled(self, alert) -> bool:
        if alert.severity == "CRITICAL":
            return False  # Never throttle critical incidents
        fingerprint = f"{alert.service}:{alert.component}:{alert.title}"
        now = time.time()
        last_time = self._last_dispatched.get(fingerprint, 0.0)
        if now - last_time < self.cooldown:
            return True
        self._last_dispatched[fingerprint] = now
        return False
```

## Common Pitfalls & Solutions

1. **FastAPI Route Discovery & `_IncludedRouter`**:
   - When inspecting mounted routes via `app.routes`, be aware that included routers can yield `_IncludedRouter` or `Mount` instances which lack a direct `.path` attribute. Use `TestClient(app)` to probe endpoints rather than iterating `app.routes` directly.
2. **Event Loop Starvation in Health Probes**:
   - Synchronous network probes (e.g. standard `smtplib.SMTP` or raw socket connect) will block the asynchronous event loop. Always wrap blocking I/O using `asyncio.to_thread(sync_func, *args)`.
3. **Alert Storms During Service Cascades**:
   - Without deterministic fingerprint hashing, an outage in a central database will fire hundreds of alerts per minute across dependent microservices. Enforce local caching of fingerprints with cooldown windows.
4. **ContextVar Leaks Across Reused Asyncio Tasks & Connection Pools**:
   - In persistent worker loops or middleware, failing to clear or reset `contextvars` can cause subsequent unrelated requests to inherit stale `trace_id` or `span_id`. Always wrap entrypoints in `try...finally: clear_context()`.
5. **Permission Failures on Standard System Backup Directories**:
   - Hardcoding standard Unix paths like `/var/backups` causes silent backup job failures in non-root containers or developer environments. Always implement a write-test probe with fallback to `$HUB_ROOT/data/backups` or `/tmp/backups/<service>`.
6. **Rate Limiter Outage during Redis Partitions**:
   - Rate limiting exclusively dependent on Redis crashes the entire gateway if Redis drops. Implement a local sliding window in-memory fallback queue with threading locks to maintain rate limiting without failing requests open to DDoS.
7. **Test Verification Timing & Verification Script Timeouts**:
   - In large repositories (>1,700 tests), executing comprehensive verification runners (`scripts/verify_all.sh` or full `pytest`) can exceed default harness timeouts (e.g. 180s) resulting in exit code 124. When invoking repository-wide pre-commit or quality gates, specify generous execution timeouts (`timeout: 300` or higher) or run focused slice suites (`pytest tests/production/`) during development before running the full gate.
8. **Health Endpoint Status Format Polymorphism**:
   - Load tests or monitoring scrapers expecting `{"status": "healthy"}` will fail when backend routes return `{"status": "ok"}`. Standardize integration tests and probes to accept `response.json().get("status") in ("ok", "healthy")` or enforce a schema-validated enum in the test fixtures.

## Verification Checklist

- [ ] `GET /health/live` returns HTTP 200 without network dependency checks.
- [ ] `GET /health/ready` returns HTTP 200 on healthy dependencies and 503 on critical failures.
- [ ] `GET /metrics` outputs valid Prometheus exposition text matching `CONTENT_TYPE_LATEST`.
- [ ] Alert deduplication tests confirm suppression of repeated identical alerts within cooldown window.
- [ ] Critical severity alerts bypass rate-limiting and dispatch immediately.
- [ ] Unit tests pass in isolated venv without active external internet or live SMTP credentials (using mocks/dry-run).
- [ ] Structured log outputs emit valid JSON containing `timestamp`, `level`, `service`, `trace_id`, and `span_id`.
- [ ] HTTP `X-Trace-ID` is extracted or generated and echoed back in response headers.
- [ ] WebSocket handshake and messages inject `trace_id` for end-to-end event correlation.

## Supporting References

- `references/alert_channels_and_metrics.md`: Configuration environment variables, Prometheus scraping configs, and Slack Block Kit JSON schemas.
- `references/structured_logging_and_tracing.md`: JSON log schemas, ContextVars distributed tracing patterns, HTTP/WebSocket propagation recipes, and ELK/Loki pipeline configs.
- `references/backup_and_disaster_recovery_runbooks.md`: Database backup rotation with checksums, automated deployment rollbacks, and DR RTO/RPO SLAs.
