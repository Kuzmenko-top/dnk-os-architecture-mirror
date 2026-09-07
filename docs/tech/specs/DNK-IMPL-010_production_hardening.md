# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_specs_dnk_impl_010_production_hardening"
# purpose: "Technical specification and configuration details for production hardening of DNK OS MVP"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

# DNK-IMPL-010: Production Hardening

This document outlines the system configuration, policies, and automation scripts used to harden the **DNK OS MVP** application for secure, stable, and highly-scalable production deployments.

---

## 1. Monitoring & Metrics

The system monitoring is based on Prometheus scraping.

### Scraped Metrics:
- **API Metrics:**
  - `http_requests_total` — Total count of HTTP requests by method, endpoint, and status.
  - `http_request_duration_seconds` — Histogram of request latencies.
  - `active_agents_count` — Live gauge indicating active running agents in memory.
  - `tasks_in_queue_count` — Gauge representing queued tasks awaiting worker execution.
- **DB Metrics:**
  - `db_connections_active` — Count of active database connections in postgres.
- **RAG Metrics:**
  - `rag_queries_total` — Cumulative count of RAG retrieval queries.
  - `rag_query_duration_seconds` — Latency of vector database query executions.

### Grafana Dashboard:
The dashboard template is located at `monitoring/grafana/dashboards/dnk_os_production.json` and provides layout panels for **System Overview**, **Agentic Execution Stats**, and **Latency Trends**.

---

## 2. Advanced Alerts

Defined inside `monitoring/alerts.yml`:
- `HighErrorRate` — Triggers when HTTP 500 status rate exceeds 5% within 5m.
- `HighResponseTime` — Triggers when p95 request latency exceeds 2 seconds.
- `HighMemoryUsage` — Triggers when node memory usage exceeds 90% for 5m.
- `DBConnectionsExhausted` — Triggers when active database connection pool size exceeds 80.
- `RAGHighLatency` — Triggers when RAG vector lookup duration exceeds 5s for 5m.

---

## 3. Scaling & High Availability

Horizontal scaling configuration is declared in `docker-compose.prod.yml`:
- **API Replication:** Configured with `replicas: 3` and automatic failover restart policies.
- **Frontend Replication:** Configured with `replicas: 2`.
- **DB Volume Persistence:** PostgreSQL and Redis utilize persistent production-grade Docker volumes (`pgdata_prod` and `redisdata_prod`).
- **Network Isolation:** All containers communicate within a secure, dedicated `dnk_prod_network` bridge network.

---

## 4. Backups and Recovery

Automation scripts are written to govern disaster recovery.

- **Backup Script (`scripts/backup.sh`):**
  - Triggers a PostgreSQL `pg_dump` to save the active dataset.
  - Runs a Redis `BGSAVE` and copies the raw `.rdb` state file.
  - Saves both compressed dumps to `/backups/` locally with clean timestamp identifiers.
- **Restore Script (`scripts/restore.sh`):**
  - Automates PostgreSQL and Redis state recovery by parsing the latest timestamped backups inside the target backup directory.

---

## 5. Security Hardening

Custom security rules are configured in `core/config/security_config.py` and mounted in `apps/api/middleware/security.py`:
- **Rate Limiting:** Enforces `SECURITY_RATE_LIMIT` (default 100 req/min) per client IP using an active sliding window in-memory cache.
- **CORS White-listing:** Restricts incoming requests to domains specified in `SECURITY_CORS_ORIGINS`.
- **API Key Authentication:** Validates headers on protected administrative endpoints to block unauthorized access, requiring headers to match the secret `SECURITY_API_KEY`.
- **Symmetric Obfuscation Ciphers:** Fully custom, crash-safe base64 byte-XOR encryption (`encrypt_data`/`decrypt_data`) is provided to obfuscate and secure sensitive parameters.

---

## 6. Centralized Logging

Structured logging stack is defined in `logging/docker-compose.logging.yml`:
- Loki and Promtail are deployed to capture and centralize JSON-structured docker container outputs.
- Promtail automatically aggregates and rotates local system logs.

---

## 7. Verification Tests

All implementations are fully tested in `tests/verification/test_production_hardening.py`:
1. `test_monitoring_metrics` — Asserts Prometheus target scrapers are present.
2. `test_alerts` — Asserts alert thresholds are configured correctly.
3. `test_scaling` — Validates horizontal replicas scaling parameters.
4. `test_backup` — Runs `backup.sh` over a safe temporary directory to verify `.sql` and `.rdb` files are cleanly created.
5. `test_restore` — Runs `restore.sh` to verify full database recovery.
6. `test_security_middleware` — Tests blocked and authorized rate limit, API Key, and CORS states, and validates XOR crypto algorithms.
7. `test_logging` — Asserts Loki and Promtail logging services are declared.
