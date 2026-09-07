#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/run.sh"
# purpose: "Unified execution wrapper ensuring .venv python, correct PYTHONPATH, and isolation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$HUB_ROOT/.venv/bin/activate" ]; then
    source "$HUB_ROOT/.venv/bin/activate"
fi

export PYTHONPATH="$HUB_ROOT:$HUB_ROOT/services:${PYTHONPATH:-}"
export SECURITY_RATE_LIMIT="${SECURITY_RATE_LIMIT:-100000}"

if [ $# -eq 0 ]; then
    echo "Usage: ./scripts/run.sh <command> [args...]"
    echo "Examples:"
    echo "  ./scripts/run.sh python3 -m apps.api.main"
    echo "  ./scripts/run.sh pytest tests/shopify/ -q"
    exit 1
fi

exec "$@"
