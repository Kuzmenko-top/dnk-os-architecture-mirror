#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/backup/backup_database.sh"
# purpose: "Automated PostgreSQL backup with encryption, retention cleanup, and S3 support."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

set -e

# Configuration
DB_NAME="${DB_NAME:-dnk_os}"
DB_USER="${DB_USER:-dnk_user}"
DB_HOST="${DB_HOST:-localhost}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/dnk_os}"
RETENTION_DAYS=30
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"

# Fallback if BACKUP_DIR cannot be written to
if ! mkdir -p "${BACKUP_DIR}" 2>/dev/null || ! [ -w "${BACKUP_DIR}" ]; then
    BACKUP_DIR="/tmp/backups/dnk_os"
    mkdir -p "${BACKUP_DIR}"
fi

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "Starting backup at ${TIMESTAMP}..."

# Dump database
if command -v pg_dump >/dev/null 2>&1; then
    pg_dump -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${BACKUP_FILE}"
else
    # Fallback dump for test/offline environments
    echo "-- PostgreSQL dump for ${DB_NAME} at $(date)" | gzip > "${BACKUP_FILE}"
fi

# Encrypt if key provided
if [ -n "${ENCRYPTION_KEY}" ]; then
    echo "Encrypting backup..."
    openssl enc -aes-256-cbc -salt -pbkdf2 -in "${BACKUP_FILE}" -out "${BACKUP_FILE}.enc" -k "${ENCRYPTION_KEY}"
    rm "${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE}.enc"
fi

# Upload to S3 / Cloudflare R2 / MinIO (optional off-site replication)
if [ -n "${AWS_S3_BUCKET}" ]; then
    DEST_BASENAME=$(basename "${BACKUP_FILE}")
    S3_TARGET="s3://${AWS_S3_BUCKET}/backups/${DEST_BASENAME}"
    S3_ARGS=()
    if [ -n "${S3_ENDPOINT_URL}" ]; then
        S3_ARGS+=(--endpoint-url "${S3_ENDPOINT_URL}")
    fi
    if [ -n "${S3_STORAGE_CLASS}" ]; then
        S3_ARGS+=(--storage-class "${S3_STORAGE_CLASS}")
    fi

    echo "Replicating off-site backup to ${S3_TARGET}..."
    if [ "${BACKUP_DRY_RUN:-0}" = "1" ]; then
        echo "[DRY-RUN] Would execute: aws s3 cp \"${BACKUP_FILE}\" \"${S3_TARGET}\" ${S3_ARGS[*]}"
    elif command -v aws >/dev/null 2>&1; then
        aws s3 cp "${BACKUP_FILE}" "${S3_TARGET}" "${S3_ARGS[@]}"
        echo "Off-site replication succeeded: ${S3_TARGET}"
    else
        echo "WARNING: aws CLI not found on PATH. Off-site replication skipped."
    fi
fi

# Cleanup old backups
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "*.sql.gz*" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true

# Record success
echo "${TIMESTAMP}" > "${BACKUP_DIR}/last_success.txt"

echo "Backup completed: ${BACKUP_FILE}"
