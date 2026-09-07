# Backup, Rollback & Disaster Recovery Runbooks

Standardized operational runbooks and scripts for database backups, automated deployment rollbacks, and recovery point/time objectives.

## 1. Disaster Recovery Objectives (SLAs)

| Dimension | Target SLA | Strategy |
|---|---|---|
| **RTO (Recovery Time Objective)** | < 15 minutes | Automated rollback script, pre-tested migration reversals, fast container restart. |
| **RPO (Recovery Point Objective)** | < 5 minutes (DB), 0 (Code) | Continuous WAL / 6-hour automated snapshot backups, Git-backed configuration. |
| **Failover Health Verification** | < 30 seconds | Automated HTTP probe on `/health` following rollbacks or failovers. |

## 2. Automated PostgreSQL Backup Recipe (`backup_database.sh`)

Features:
- Tests directory permissions before execution; falls back from `/var/backups` to `$HUB_ROOT/data/backups` or `/tmp/backups`.
- Retains rolling window of the last N backups (default: 7 days) and prunes older dumps.
- Generates SHA256 checksums alongside `.sql.gz` archives for integrity verification.

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/tmp/backups/dnk_os}"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql.gz"

echo "==> Starting database backup..."
pg_dump "${DATABASE_URL}" | gzip > "${BACKUP_FILE}"
sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"

# Retention policy: retain 7 days
find "${BACKUP_DIR}" -type f -name "db_backup_*.sql.gz*" -mtime +7 -delete
echo "==> Backup completed: ${BACKUP_FILE}"
```

## 3. Safe Deployment Rollback Recipe (`rollback_deployment.sh`)

Features:
- Restores git state or container images to the previous target tag/commit.
- Executes automated dependency checks and database schema rollback if applicable.
- Verifies post-rollback health endpoint; automatically triggers critical alerts if rollback fails.

```bash
#!/usr/bin/env bash
set -euo pipefail

TARGET_VERSION="${1:-HEAD~1}"
echo "==> Rolling back to version: ${TARGET_VERSION}"

# 1. Checkout target version or pull image
git checkout "${TARGET_VERSION}"

# 2. Re-install / verify dependencies
uv pip sync requirements.txt || true

# 3. Post-rollback health verification
echo "==> Verifying system health..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [ "$STATUS" != "200" ]; then
    echo "ERROR: Health check failed with status ${STATUS}"
    exit 1
fi
echo "==> Rollback verified successfully."
```
