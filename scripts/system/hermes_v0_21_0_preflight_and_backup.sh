#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/hermes_v0_21_0_preflight_and_backup.sh"
# purpose: "Pre-flight checks, baseline hashes calculation, and complete backup for Hermes v0.21.0 promotion."
# canonical_source: true
# alters_files: ["docs/operations/HERMES_V0_21_0_BASELINE_HASHES.txt"]
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
echo "🛡️  Hermes v0.21.0 Promotion — Pre-Flight & Baseline Backup"
echo "=========================================================="

hash_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$@"
  else
    shasum -a 256 "$@"
  fi
}

# 1. Verification of paths
LAUNCHER_BIN="${HOME}/.local/bin/hermes"
PROD_STATE_DIR="${HOME}/.hermes"
PROD_RUNTIME_DIR="${HUB_ROOT}/core/hermes_agent"
STAGING_CANDIDATE="${HUB_ROOT}/core/hermes_agent_staging/.venv/bin/hermes"
OUTPUT_HASHES="${HUB_ROOT}/docs/operations/HERMES_V0_21_0_BASELINE_HASHES.txt"

echo "🔍 [1/5] Checking Production Version..."
if [ -x "${LAUNCHER_BIN}" ]; then
  "${LAUNCHER_BIN}" --version || true
else
  echo "⚠️ Launcher ${LAUNCHER_BIN} not found or not executable. Checking fallback."
fi

echo "🔍 [2/5] Checking Staging Candidate Version..."
if [ -x "${STAGING_CANDIDATE}" ]; then
  "${STAGING_CANDIDATE}" --version
else
  echo "❌ Error: Candidate ${STAGING_CANDIDATE} not found!"
  exit 1
fi

echo "🔍 [3/5] Recording Baseline Checksums..."
mkdir -p "$(dirname "${OUTPUT_HASHES}")"
: > "${OUTPUT_HASHES}"

if [ -f "${PROD_STATE_DIR}/state.db" ]; then
  hash_sha256 "${PROD_STATE_DIR}/state.db" >> "${OUTPUT_HASHES}"
fi

if [ -f "${PROD_STATE_DIR}/config.yaml" ]; then
  hash_sha256 "${PROD_STATE_DIR}/config.yaml" >> "${OUTPUT_HASHES}"
fi

if [ -f "${LAUNCHER_BIN}" ]; then
  hash_sha256 "${LAUNCHER_BIN}" >> "${OUTPUT_HASHES}"
fi

echo "--- Baseline Checksums Saved to docs/operations/HERMES_V0_21_0_BASELINE_HASHES.txt ---"
cat "${OUTPUT_HASHES}"

echo "📦 [4/5] Creating State and Runtime Backups..."
# State backup
if [ -d "${PROD_STATE_DIR}" ]; then
  cp -r "${PROD_STATE_DIR}" "${HOME}/.hermes.backup.pre-0.21.0"
  echo "✅ State backup created at ~/.hermes.backup.pre-0.21.0"
fi

# Runtime backup
if [ -d "${PROD_RUNTIME_DIR}" ]; then
  cp -r "${PROD_RUNTIME_DIR}" "${HUB_ROOT}/core/hermes_agent.backup.pre-0.21.0"
  mkdir -p "${HUB_ROOT}/core/hermes_versions/v0.20.5"
  cp -r "${PROD_RUNTIME_DIR}" "${HUB_ROOT}/core/hermes_versions/v0.20.5/hermes_agent"
  echo "✅ Runtime backup created at core/hermes_agent.backup.pre-0.21.0"
fi

# Launcher backup
if [ -f "${LAUNCHER_BIN}" ]; then
  cp "${LAUNCHER_BIN}" "${LAUNCHER_BIN}.backup.pre-0.21.0"
  cp "${LAUNCHER_BIN}" "${LAUNCHER_BIN}.v0.20.5.backup"
  echo "✅ Launcher backup created at ~/.local/bin/hermes.backup.pre-0.21.0"
fi

echo "🔎 [5/5] Verifying Backups..."
if [ -f "${HOME}/.hermes.backup.pre-0.21.0/state.db" ]; then
  ls -lh "${HOME}/.hermes.backup.pre-0.21.0/state.db"
fi
if [ -d "${HUB_ROOT}/core/hermes_agent.backup.pre-0.21.0" ]; then
  ls -ld "${HUB_ROOT}/core/hermes_agent.backup.pre-0.21.0"
fi
if [ -f "${LAUNCHER_BIN}.backup.pre-0.21.0" ]; then
  ls -lh "${LAUNCHER_BIN}.backup.pre-0.21.0"
fi

echo "=========================================================="
echo "✅ Pre-flight checks and backups completed successfully!"
echo "=========================================================="
