# --- DNK-MRH-HEADER ---
# mrh_id: "docs_monitoring_alerting"
# purpose: "Production Monitoring, Prometheus Metrics & Alerting Engine Specification"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

# 📊 DNK OS Monitoring & Alerting Subsystem

## 1. Overview & Architecture

The DNK OS Monitoring & Alerting subsystem provides zero-overhead, real-time observability across all microservices, API nodes, and autonomous Swarm workers.

```
                      +-----------------------------+
                      |   Kubernetes / Ingress      |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                     |                     |
        GET /health/live      GET /health/ready      GET /metrics
               |                     |                     |
               v                     v                     v
      +-----------------+   +-----------------+   +-----------------+
      | Liveness Probe  |   | Readiness Probe |   | Prometheus      |
      | (Process Ping)  |   | (DB, Redis, FS) |   | Exposition      |
      +-----------------+   +-----------------+   +--------+--------+
                                                           |
                                                           v
                                                  Prometheus Scraper
                                                           |
                                                           v
                                                  Grafana Dashboards

                      +-----------------------------+
                      |  Incident / Threshold Event |
                      +--------------+--------------+
                                     |
                                     v
                          +--------------------+
                          |   AlertManager     |
                          | (Throttling & Dedup)
                          +----+----------+----+
                               |          |
                      +--------v--+    +--v--------+
                      |   Slack   |    |   Email   |
                      | Webhook   |    |  (SMTP)   |
                      +-----------+    +-----------+
```

---

## 2. Health Endpoints Specification

DNK OS implements Kubernetes and Load Balancer standard probes with granular diagnostic granularity:

| Endpoint | Method | Purpose | HTTP Status |
| :--- | :--- | :--- | :--- |
| `/health/live` | `GET` | **Liveness Probe**: Confirms the FastAPI event loop is running. | `200 OK` |
| `/health/ready` | `GET` | **Readiness Probe**: Verifies DB and cache connections before accepting user traffic. | `200 OK` / `503 Service Unavailable` |
| `/health/detailed` | `GET` | **Diagnostic Health**: Returns deep component diagnostics (Memory, Disk, DB replica health, Redis cluster state). | `200 OK` / `503 Service Unavailable` |

### Sample Response (`GET /health/detailed`)
```json
{
  "status": "healthy",
  "version": "5.0.0",
  "environment": "production",
  "uptime_seconds": 14205.3,
  "timestamp": "2026-09-05T10:15:00.000000+00:00",
  "components": {
    "memory": {
      "name": "memory",
      "status": "healthy",
      "response_time_ms": 0.25,
      "details": {
        "total_mb": 16384.0,
        "available_mb": 9430.5,
        "percent_used": 42.4
      },
      "error": null
    },
    "disk": {
      "name": "disk",
      "status": "healthy",
      "response_time_ms": 0.42,
      "details": {
        "total_gb": 494.38,
        "free_gb": 320.12,
        "percent_used": 35.2
      },
      "error": null
    },
    "database": {
      "name": "database",
      "status": "healthy",
      "response_time_ms": 1.15,
      "details": {
        "master": { "healthy": true, "pool_size": 10 },
        "replicas_active": 2
      },
      "error": null
    },
    "redis": {
      "name": "redis",
      "status": "healthy",
      "response_time_ms": 0.85,
      "details": {
        "connected": true,
        "ping": "pong"
      },
      "error": null
    }
  },
  "system_metrics": {
    "uptime_seconds": 14205.3,
    "cpu_percent": 14.5,
    "memory_percent": 42.4
  }
}
```

---

## 3. Prometheus Metrics Catalog

The endpoint `GET /metrics` exposes metrics compliant with Prometheus Text Exposition Format (`text/plain; version=0.0.4; charset=utf-8`).

### Core Metrics Reference

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `dnk_http_requests_total` | Counter | `method`, `endpoint`, `status_code` | Cumulative total of HTTP requests handled. |
| `dnk_http_request_duration_seconds` | Histogram | `method`, `endpoint` | Request execution latency distribution. |
| `dnk_system_cpu_usage_ratio` | Gauge | None | Host CPU utilization ratio ($0.0$ to $1.0$). |
| `dnk_system_memory_usage_bytes` | Gauge | None | Host RAM used in bytes. |
| `dnk_swarm_active_tasks_total` | Gauge | `agent` | Count of in-flight Swarm worker tasks. |
| `dnk_swarm_completed_tasks_total` | Counter | `agent`, `status` | Swarm tasks completed by status. |
| `dnk_active_websocket_connections` | Gauge | `workspace_id` | Number of real-time client WebSockets. |
| `dnk_alerts_dispatched_total` | Counter | `severity`, `channel`, `status` | Alert dispatch volume across notification channels. |

---

## 4. Multi-Channel Alerting Subsystem

The Alerting Engine (`apps/api/monitoring/alerts.py`) delivers notifications with built-in deduplication, rate-limiting, and channel routing.

### Channels
1. **Slack Webhook Channel**:
   - Formats alerts as Slack Block Kit cards with color indicators matching severity.
   - Includes service metadata, error message, and direct links to incident runbooks.
   - Configured via `SLACK_WEBHOOK_URL` or `DNK_SLACK_WEBHOOK`.
2. **Email (SMTP) Channel**:
   - Sends multipart HTML and plain-text emails.
   - Configured via `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, and `ALERT_EMAIL_TO`.

### Deduplication & Throttling
- Alerts are hashed by `{service}:{component}:{severity}:{title}` to compute a unique fingerprint.
- Duplicate alerts within the cooldown window (default: 300 seconds) are suppressed.
- **CRITICAL alerts bypass throttling** to ensure zero delay during severe production incidents.

---

## 5. Severity Levels & SLA Response Matrix

| Severity | Color Code | Notification Channels | Escalation SLA | Behavior |
| :--- | :--- | :--- | :--- | :--- |
| `INFO` | `#36A64F` (Green) | Logs, Metrics | N/A | Recorded for audit trails and trends. |
| `WARNING` | `#ECAA38` (Amber) | Slack, Metrics | 4 Hours | Throttled (300s window), self-healing triggered. |
| `ERROR` | `#E01E5A` (Red) | Slack, Email, Metrics | 30 Minutes | Throttled (300s window), on-call engineer alerted. |
| `CRITICAL` | `#7B001C` (Dark Red) | Slack, Email, PagerDuty | **Immediate (< 5m)** | **Never throttled**, high-priority dispatch. |

---

## 6. Environment Configuration

Add the following environment variables to your deployment (`.env` or Helm values):

```bash
# Slack Incoming Webhook
SLACK_WEBHOOK_URL="https://hooks.slack.com.example/services/REDACTED_MOCK_WEBHOOK"

# SMTP Email Configuration
SMTP_HOST="smtp.mailgun.org"
SMTP_PORT="587"
SMTP_USER="postmaster@dnk-os.com"
SMTP_PASSWORD="secret-smtp-password"
SMTP_FROM="alerts@dnk-os.com"
ALERT_EMAIL_TO="devops@dnk-os.com"

# Monitoring Tuning
DNK_MONITORING_COOLDOWN_SECONDS="300"
DNK_ENV="production"
```

---

## 7. Incident Response Runbooks

1. **Database Degradation (`ComponentHealth.database == degraded`)**:
   - Check replica connectivity: inspect `db_manager.check_health()`.
   - Verify connection pool exhaustion in `dnk_database_connection_pool_active`.
   - Execute auto-healing connection reset if pool is saturated.
2. **Memory Spike (`dnk_system_memory_usage_bytes > 90%`)**:
   - Inspect top memory-consuming workers via Swarm status: `dnk_swarm_status()`.
   - Recycle worker child processes or scale horizontally.
3. **High HTTP Error Rate (`dnk_http_requests_total{status_code=~"5.."} > 1%`)**:
   - Inspect API logs in `apps/api/` for unhandled tracebacks.
   - Query self-healing distillation: `dnk_query_error_solutions(error_text)`.
