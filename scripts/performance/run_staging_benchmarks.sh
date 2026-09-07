#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_performance_run_staging_benchmarks"
# purpose: "Automated execution harness for Staging Performance Validation benchmarks across live Docker containers"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT_DIR}"

echo "=========================================================="
echo "🚀 [DNK OS] Running Slice 12.5.1: Staging Performance Validation"
echo "=========================================================="

# 1. Health check Docker Compose containers
echo "[1/4] Verifying Docker Compose production stack health..."
if ! docker compose -f docker-compose.prod.yml ps > /dev/null 2>&1; then
    echo "❌ ERROR: Docker compose stack is not accessible or not running!" >&2
    exit 1
fi

docker compose -f docker-compose.prod.yml ps

# 2. Setup Staging Environment Flags (TESTING=0, Rate Limiting active)
echo "[2/4] Initializing Staging environment variables..."
unset TESTING
export STAGING_MODE="1"
export STAGING_URL="http://localhost:8000"
export STAGING_WS_URL="ws://localhost:8000"

# 3. Start Continuous Resource Metrics Collector
echo "[3/4] Starting resource telemetry monitor..."
mkdir -p docs/performance
.venv/bin/python3 scripts/performance/collect_metrics.py --interval 5 --output docs/performance/metrics_staging_20260905.csv &
MONITOR_PID=$!

cleanup() {
    if ps -p ${MONITOR_PID} > /dev/null 2>&1; then
        kill -SIGINT ${MONITOR_PID} 2>/dev/null || true
    fi
}
trap cleanup EXIT

# 4. Run Staging Performance Benchmarks
echo "[4/4] Executing real-container staging benchmarks..."
.venv/bin/python3 scripts/performance/staging_benchmark_runner.py

# Final snapshot
.venv/bin/python3 scripts/performance/collect_metrics.py --snapshot --output docs/performance/metrics_staging_20260905.csv

echo "=========================================================="
echo "✅ Staging Performance Validation completed successfully!"
echo "📄 Report: docs/performance/STAGING_RESULTS_20260905.md"
echo "📊 Telemetry: docs/performance/metrics_staging_20260905.csv"
echo "=========================================================="
