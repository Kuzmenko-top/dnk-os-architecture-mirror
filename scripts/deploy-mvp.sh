#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_deploy_mvp_sh"
# purpose: "One-click idempotent deployment script for DNK OS Canvas MVP"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-03"
# --- END DNK-MRH-HEADER ---

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."
cd "${ROOT_DIR}"

echo "========================================================"
echo "🚀 Deploying DNK OS Canvas MVP (Day 2 Stack)"
echo "========================================================"

# 1. Clean up any previously running compose instances for true idempotency
echo "🧹 Cleaning up previous MVP compose stack if present..."
docker compose -f docker-compose.mvp.yml down --remove-orphans 2>/dev/null || true

# 2. Check and liberate ports from stale external background processes
echo "🔍 Verifying ports 3000, 8000, 5432, 6379..."
for port in 3000 8000 5432 6379; do
  OCCUPIED_PID=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null || true)
  if [ -n "$OCCUPIED_PID" ]; then
    PROC_NAME=$(ps -p $OCCUPIED_PID -o comm= 2>/dev/null || echo "process")
    if [ "$port" -eq 6379 ] && [[ "$PROC_NAME" =~ redis ]]; then
      echo "⚠️ Local Homebrew redis running on 6379 (PID: $OCCUPIED_PID). Stopping via brew..."
      brew services stop redis 2>/dev/null || kill -9 $OCCUPIED_PID 2>/dev/null || true
      sleep 1
    else
      echo "⚠️ Port $port occupied by $PROC_NAME (PID: $OCCUPIED_PID). Clearing..."
      kill -9 $OCCUPIED_PID 2>/dev/null || true
      sleep 0.5
    fi
  fi
done

# 3. Build Docker images & start services
echo "📦 Building Docker images & starting services..."
docker compose -f docker-compose.mvp.yml up -d --build

# 4. Wait for services to become healthy via polling loop
echo "⏳ Waiting for services to initialize and pass healthchecks..."
MAX_ATTEMPTS=25
READY=0
for i in $(seq 1 $MAX_ATTEMPTS); do
  API_STATUS=$(curl -sf http://localhost:8000/health 2>/dev/null || echo "fail")
  WEB_STATUS=$(curl -sf http://localhost:3000/health 2>/dev/null || echo "fail")

  if [ "$API_STATUS" != "fail" ] && [ "$WEB_STATUS" != "fail" ]; then
    echo "✅ Health check passed on attempt $i/$MAX_ATTEMPTS!"
    READY=1
    break
  fi
  echo "   [Attempt $i/$MAX_ATTEMPTS] Waiting for API & Web health (API: $([ "$API_STATUS" != "fail" ] && echo "OK" || echo "WAIT"), Web: $([ "$WEB_STATUS" != "fail" ] && echo "OK" || echo "WAIT"))..."
  sleep 2
done

if [ $READY -ne 1 ]; then
  echo "❌ Health check timed out after $((MAX_ATTEMPTS * 2))s! Container logs:"
  docker compose -f docker-compose.mvp.yml logs --tail=40
  exit 1
fi

# 5. Show status & access points
echo "========================================================"
echo "🎉 MVP deployed successfully!"
echo "========================================================"
echo "📊 Access points:"
echo "   👉 Web UI:    http://localhost:3000"
echo "   👉 API:       http://localhost:8000"
echo "   👉 API Docs:  http://localhost:8000/docs"
echo "   👉 Postgres:  localhost:5432 (dnk_canvas)"
echo "   👉 Redis:     localhost:6379"
echo "========================================================"
echo "📝 Logs:   docker compose -f docker-compose.mvp.yml logs -f"
echo "🛑 Stop:   docker compose -f docker-compose.mvp.yml down"
echo "========================================================"
