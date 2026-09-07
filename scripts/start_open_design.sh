#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/start_open_design.sh"
# purpose: "Startup supervisor script for Open Design Daemon (7456) & Web UI (5173)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-01"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

set -euo pipefail

if [ -d "/opt/homebrew/bin" ]; then
  export PATH="/opt/homebrew/bin:$PATH"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."
OPEN_DESIGN_DIR="${ROOT_DIR}/visual_shell/open_design"

echo "========================================================"
echo "🚀 Starting DNK OS Visual Shell (Open Design + Hermes)"
echo "========================================================"

# 1. Kill any stale instances on ports 7456 and 5173
echo "🧹 Checking ports 7456 and 5173..."
lsof -ti :7456 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true

# Global CORS & Port configuration
export OD_PORT=7456
export OD_WEB_PORT=5173
export OD_ALLOWED_ORIGINS="http://localhost:5173,http://127.0.0.1:5173,http://localhost:7456,http://127.0.0.1:7456"

# 2. Start Daemon (Port 7456)
echo "⚙️ Starting Open Design Daemon on port 7456..."
cd "${OPEN_DESIGN_DIR}"
OD_PORT=7456 OD_WEB_PORT=5173 OD_ALLOWED_ORIGINS="http://localhost:5173,http://127.0.0.1:5173,http://localhost:7456,http://127.0.0.1:7456" node apps/daemon/bin/od.mjs --no-open > /tmp/open_design_daemon.log 2>&1 &
DAEMON_PID=$!


# Wait for daemon health
for i in {1..10}; do
  if curl -s http://127.0.0.1:7456/api/health >/dev/null 2>&1; then
    echo "✅ Daemon is ready on http://127.0.0.1:7456 (PID: ${DAEMON_PID})"
    break
  fi
  sleep 0.5
done

# 3. Start Web UI (Port 5173)
echo "🎨 Starting Next.js Web UI on port 5173..."
cd "${OPEN_DESIGN_DIR}/apps/web"
PORT=5173 pnpm exec next dev --turbopack > /tmp/open_design_web.log 2>&1 &
WEB_PID=$!

for i in {1..15}; do
  if curl -s http://127.0.0.1:5173 >/dev/null 2>&1; then
    echo "✅ Web UI is ready on http://localhost:5173 (PID: ${WEB_PID})"
    break
  fi
  sleep 0.5
done

echo "========================================================"
echo "🎉 Visual Shell is LIVE:"
echo "   👉 UI:     http://localhost:5173"
echo "   👉 Daemon: http://127.0.0.1:7456"
echo "========================================================"
