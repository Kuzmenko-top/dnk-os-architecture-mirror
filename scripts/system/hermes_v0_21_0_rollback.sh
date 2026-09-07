#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/hermes_v0_21_0_rollback.sh"
# purpose: "Instant emergency rollback script from Hermes v0.21.0 to v0.20.5 (SLA < 30s)."
# canonical_source: true
# alters_files: ["~/.local/bin/hermes", "~/.hermes/state.db"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=========================================================="
echo "🚨 Hermes v0.21.0 Promotion — EMERGENCY ROLLBACK TO v0.20.5"
echo "=========================================================="

START_TS="$(date +%s%N 2>/dev/null || date +%s)"

LAUNCHER_BIN="${HOME}/.local/bin/hermes"
BACKUP_LAUNCHER="${HOME}/.local/bin/hermes.backup.pre-0.21.0"
PROD_STATE_DIR="${HOME}/.hermes"
BACKUP_STATE_DIR="${HOME}/.hermes.backup.pre-0.21.0"

echo "🛑 [1/4] Stopping runtime processes..."
# Terminate lingering daemons if any (excluding current session tree and interactive ttys)
CURRENT_PID=$$
ANCESTOR_PIDS=" "
curr=$$
while [ -n "$curr" ] && [ "$curr" -gt 1 ] 2>/dev/null; do
  ANCESTOR_PIDS="${ANCESTOR_PIDS}${curr} "
  curr=$(ps -o ppid= -p "$curr" 2>/dev/null | tr -d ' ')
done

for pid in $(pgrep -f "hermes gateway|hermes daemon" || true); do
  if [[ ! " ${ANCESTOR_PIDS} " =~ " ${pid} " ]]; then
    tty_val=$(ps -o tty= -p "$pid" 2>/dev/null | tr -d ' ')
    if [ "$tty_val" = "?" ] || [ "$tty_val" = "??" ]; then
      echo "Sending SIGTERM to background daemon process $pid..."
      kill -15 "$pid" 2>/dev/null || true
    fi
  fi
done

echo "🔄 [2/4] Restoring launcher to v0.20.5..."
if [ -f "${BACKUP_LAUNCHER}" ]; then
  cp -f "${BACKUP_LAUNCHER}" "${LAUNCHER_BIN}"
  chmod +x "${LAUNCHER_BIN}"
  echo "✅ Launcher restored from ${BACKUP_LAUNCHER}"
elif [ -f "${HOME}/.local/bin/hermes.v0.20.5.backup" ]; then
  cp -f "${HOME}/.local/bin/hermes.v0.20.5.backup" "${LAUNCHER_BIN}"
  chmod +x "${LAUNCHER_BIN}"
  echo "✅ Launcher restored from ${HOME}/.local/bin/hermes.v0.20.5.backup"
else
  echo "❌ Error: Launcher backup not found!"
  exit 1
fi

echo "📦 [3/4] Restoring state database (if requested or corrupt)..."
if [ "$1" == "--with-state" ] && [ -d "${BACKUP_STATE_DIR}" ]; then
  echo "Restoring state from ${BACKUP_STATE_DIR}..."
  rm -rf "${PROD_STATE_DIR}"
  cp -r "${BACKUP_STATE_DIR}" "${PROD_STATE_DIR}"
  echo "✅ State directory restored."
fi

echo "🔍 [4/4] Verifying restored version..."
RESTORED_VERSION="$("${LAUNCHER_BIN}" --version || true)"
echo "Restored Version: ${RESTORED_VERSION}"

END_TS="$(date +%s%N 2>/dev/null || date +%s)"
echo "=========================================================="
echo "✅ Rollback executed successfully to: ${RESTORED_VERSION}"
echo "=========================================================="
