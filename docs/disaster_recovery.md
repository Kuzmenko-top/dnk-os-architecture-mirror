---
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/disaster_recovery.md"
# purpose: "Disaster Recovery Plan, High Availability, RTO/RPO SLAs, and Incident Playbooks for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---
title: "DNK OS Disaster Recovery & Business Continuity Plan"
version: "1.0.0"
rto: "< 5 minutes"
rpo: "< 1 minute"
uptime_sla: "99.9%"
---

# 🛡️ DNK OS Disaster Recovery (DR) & Incident Runbooks

## 1. Executive Summary & SLAs
- **Target Uptime**: 99.9% availability for core API and Swarm services.
- **Recovery Time Objective (RTO)**: < 5 minutes (failover and container redeployment).
- **Recovery Point Objective (RPO)**: < 1 minute (PostgreSQL WAL streaming + continuous replication).

---

## 2. Architecture & Redundancy Overview
- **Compute Tier**: Multi-container Docker / Kubernetes deployment with health probes (`/health`).
- **Database Tier**: PostgreSQL primary-replica setup with automated daily dumps (`scripts/backup/backup_database.sh`) and WAL archiving.
- **Caching & State**: Redis cluster with AOF (Append-Only File) enabled and automated RDB persistence.
- **Monitoring & Alerting**: Prometheus scraping (`monitoring/prometheus_config.yml`), Alertmanager rules (`monitoring/alert_rules.yml`), and dual-channel dispatch via PagerDuty + Slack (`services/alerting_service.py`).

---

## 3. Incident Classification & Severity Levels

| Severity | Definition | Response Time | Channels |
| :--- | :--- | :--- | :--- |
| **P1 - CRITICAL** | Full system outage, database corruption, data loss risk | < 5 min | PagerDuty (Phone/SMS) + Slack #alerts-critical |
| **P2 - HIGH** | Core feature impaired (e.g. checkout, task execution delayed) | < 15 min | Slack #alerts-critical |
| **P3 - MEDIUM** | Performance degradation, high latency, non-blocking errors | < 1 hour | Slack #alerts-warnings |
| **P4 - LOW** | Minor cosmetic issues, background batch latency | < 24 hours | Slack #alerts-info |

---

## 4. Disaster Recovery Runbooks

### 4.1 Database Failure & Restoration
1. **Diagnosis**:
   ```bash
   # Check PostgreSQL service status
   systemctl status postgresql || docker ps -f name=postgres
   # Check connection
   pg_isready -h localhost -p 5432
   ```
2. **Restoration from Backup**:
   ```bash
   # Locate latest verified backup
   BACKUP_DIR="${BACKUP_DIR:-/var/backups/dnk_os}"
   LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/*.sql.gz | head -1)

   # Restore database
   gunzip -c "${LATEST_BACKUP}" | psql -h localhost -U dnk_user -d dnk_os
   ```
3. **Point-in-Time Recovery (PITR)**:
   - Replay WAL segments from the archive directory up to the target timestamp.

---

### 4.2 Redis Failure & Memory Flush
1. **Diagnosis**:
   ```bash
   redis-cli ping
   redis-cli info memory
   ```
2. **Restart & AOF Replay**:
   ```bash
   docker restart dnk_redis
   redis-check-aof --fix /var/lib/redis/appendonly.aof
   ```

---

### 4.3 Container Rollback
If a deployment introduces critical bugs or crashes:
```bash
bash scripts/rollback/rollback_deployment.sh <PREVIOUS_VERSION>
```
The rollback script automatically stops current containers, pulls the previous stable image, launches services, and verifies health via `/health`.

---

### 4.4 DDOS or Brute-Force Attack Mitigation
1. **Rate Limiter Activation**:
   Ensure `scripts/security/rate_limiter.py` is engaged on public endpoints.
2. **IP Blacklisting**:
   Block offending CIDR blocks at the Cloudflare / Nginx reverse proxy layer.

---

## 5. Backup Verification Drills
- Weekly automated drill runs `tests/production/test_backup_restore.py` to ensure backups can be decompressed and ingested without schema errors.
- Retention policy: 30 daily backups, 12 monthly archives in immutable S3 storage (`s3://$AWS_S3_BUCKET/backups/`).
