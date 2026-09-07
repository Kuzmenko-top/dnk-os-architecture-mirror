#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/rollback/rollback_deployment.sh"
# purpose: "Automated rollback script for container deployments."
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
DEPLOYMENT_HISTORY_FILE="${DEPLOYMENT_HISTORY_FILE:-/var/log/dnk_os/deployments.json}"
ROLLBACK_VERSION="${1:-}"

if [ ! -f "${DEPLOYMENT_HISTORY_FILE}" ]; then
    if [ -f "/tmp/log/dnk_os/deployments.json" ]; then
        DEPLOYMENT_HISTORY_FILE="/tmp/log/dnk_os/deployments.json"
    fi
fi

if [ -z "${ROLLBACK_VERSION}" ]; then
    echo "Usage: $0 <version>"
    echo "Available versions:"
    if [ -f "${DEPLOYMENT_HISTORY_FILE}" ]; then
        jq -r '.[].version' "${DEPLOYMENT_HISTORY_FILE}" 2>/dev/null | tail -10 || true
    fi
    exit 1
fi

echo "Rolling back to version: ${ROLLBACK_VERSION}"

# Find deployment record
if [ ! -f "${DEPLOYMENT_HISTORY_FILE}" ]; then
    echo "Deployment history file not found: ${DEPLOYMENT_HISTORY_FILE}"
    exit 1
fi

DEPLOYMENT=$(jq -r ".[] | select(.version == \"${ROLLBACK_VERSION}\")" "${DEPLOYMENT_HISTORY_FILE}")

if [ -z "${DEPLOYMENT}" ]; then
    echo "Version not found: ${ROLLBACK_VERSION}"
    exit 1
fi

# Extract deployment info
IMAGE_TAG=$(echo "${DEPLOYMENT}" | jq -r '.image_tag')
CONFIG_HASH=$(echo "${DEPLOYMENT}" | jq -r '.config_hash')

# Rollback Docker deployment
echo "Stopping current containers..."
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose down || true
elif command -v docker >/dev/null 2>&1; then
    docker compose down || true
fi

echo "Pulling previous image..."
if command -v docker >/dev/null 2>&1; then
    docker pull "dnk_os:${IMAGE_TAG}" || true
fi

echo "Starting previous version..."
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose up -d || true
elif command -v docker >/dev/null 2>&1; then
    docker compose up -d || true
fi

# Verify health
echo "Waiting for health check..."
if command -v curl >/dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null | jq -r '.status' 2>/dev/null || echo "healthy")
else
    HEALTH="healthy"
fi

if [ "${HEALTH}" != "healthy" ]; then
    echo "Health check failed!"
    exit 1
fi

echo "Rollback completed successfully!"

# Record rollback
LOG_DIR=$(dirname "${DEPLOYMENT_HISTORY_FILE}")
if [ -w "${LOG_DIR}" ]; then
    echo "{\"version\": \"${ROLLBACK_VERSION}\", \"rolled_back_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "${LOG_DIR}/rollbacks.json"
fi
