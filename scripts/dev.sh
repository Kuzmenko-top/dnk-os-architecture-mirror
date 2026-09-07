#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/dev.sh"
# purpose: "DNK OS MVP Single-Click Launcher for Backend and Frontend."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# DNK OS MVP Single-Click Launcher
echo "🚀 Starting DNK OS MVP Core & Visual Shell..."

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$ROOT_DIR"

# 1. Start FastAPI Backend in background
echo "🧠 Starting FastAPI Backend (port 8000)..."
PYTHONPATH="$ROOT_DIR:$ROOT_DIR/services" "$ROOT_DIR/.venv/bin/python3" -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 2. Start Visual Shell Frontend
echo "🎨 Starting Visual Shell Frontend..."
if [ -d "$ROOT_DIR/apps/web" ]; then
  cd "$ROOT_DIR/apps/web"
  npm run dev &
  FRONTEND_PID=$!
elif [ -d "$ROOT_DIR/visual_shell/open_design/apps/web" ]; then
  cd "$ROOT_DIR/visual_shell/open_design/apps/web"
  pnpm exec next dev &
  FRONTEND_PID=$!
elif [ -d "$ROOT_DIR/visual_shell/web_ui" ]; then
  cd "$ROOT_DIR/visual_shell/web_ui"
  npm run dev &
  FRONTEND_PID=$!
fi

echo "✅ DNK OS MVP running!"
echo "🌐 API: http://localhost:8000/docs"
echo "Press Ctrl+C to stop all services."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM EXIT
wait
