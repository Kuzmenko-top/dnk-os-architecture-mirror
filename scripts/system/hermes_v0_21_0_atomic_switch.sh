#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/hermes_v0_21_0_atomic_switch.sh"
# purpose: "Atomic launcher and runtime switch to Hermes Agent v0.21.0."
# canonical_source: true
# alters_files: ["~/.local/bin/hermes"]
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
echo "⚡ Hermes v0.21.0 Promotion — Atomic Runtime Switch"
echo "=========================================================="

LAUNCHER_BIN="${HOME}/.local/bin/hermes"
STAGING_BIN="${HUB_ROOT}/core/hermes_agent_staging/.venv/bin/hermes"

if [ ! -x "${STAGING_BIN}" ]; then
  echo "❌ Error: Candidate binary ${STAGING_BIN} does not exist or is not executable!"
  exit 1
fi

echo "🛑 [1/3] Checking and stopping background hermes processes..."
# Terminate lingering headless background daemons if any (excluding current session tree and interactive ttys)
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
sleep 1

echo "🔄 [2/3] Performing atomic launcher switch..."
mkdir -p "$(dirname "${LAUNCHER_BIN}")"

# Create atomic symlink via temporary link
ln -sfn "${STAGING_BIN}" "${LAUNCHER_BIN}.tmp"
mv -f "${LAUNCHER_BIN}.tmp" "${LAUNCHER_BIN}"

echo "🔍 [3/3] Verifying active launcher version..."
NEW_VERSION="$("${LAUNCHER_BIN}" --version)"
echo "Active Version: ${NEW_VERSION}"

case "${NEW_VERSION}" in
  *"0.21.0"*)
    echo "=========================================================="
    echo "🎉 Atomic switch successful! Active version is v0.21.0."
    echo "=========================================================="
    ;;
  *)
    echo "❌ Warning: Active version string '${NEW_VERSION}' does not contain '0.21.0'!"
    exit 1
    ;;
esac
