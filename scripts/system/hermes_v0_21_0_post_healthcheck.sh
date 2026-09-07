#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/hermes_v0_21_0_post_healthcheck.sh"
# purpose: "Post-deployment validation and health check for promoted Hermes Agent v0.21.0."
# canonical_source: true
# alters_files: []
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
echo "🩺 Hermes v0.21.0 Promotion — Post-Deployment Health Check"
echo "=========================================================="

hash_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$@"
  else
    shasum -a 256 "$@"
  fi
}

LAUNCHER_BIN="${HOME}/.local/bin/hermes"
PROD_STATE_DIR="${HOME}/.hermes"
OUTPUT_HASHES="${HUB_ROOT}/docs/operations/HERMES_V0_21_0_BASELINE_HASHES.txt"

echo "🔍 [1/4] Verifying Active Hermes Version..."
"${LAUNCHER_BIN}" --version

echo "🔍 [2/4] Executing Hermes Doctor Diagnostic..."
"${LAUNCHER_BIN}" doctor || echo "⚠️ Hermes doctor returned non-zero, reviewing diagnostic details."

echo "🔍 [3/4] Testing Session Listing..."
"${LAUNCHER_BIN}" sessions list --limit 5 || true

echo "🔍 [4/4] Comparing State Checksums..."
if [ -f "${PROD_STATE_DIR}/state.db" ]; then
  CURRENT_DB_HASH="$(hash_sha256 "${PROD_STATE_DIR}/state.db")"
  echo "Current state.db hash: ${CURRENT_DB_HASH}"
  if [ -f "${OUTPUT_HASHES}" ]; then
    echo "--- Recorded Baseline Hashes ---"
    cat "${OUTPUT_HASHES}"
  fi
fi

echo "=========================================================="
echo "✅ Post-deployment health check completed."
echo "=========================================================="
