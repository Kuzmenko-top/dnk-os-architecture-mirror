#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/gerych.sh"
# purpose: "Canonical launcher for Gerych Autonomous Orchestrator."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.3.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEM_GERYCH="${SCRIPT_DIR}/system/gerych.sh"

if [ "$1" = "--swarm" ]; then
    shift
    exec bash "${SCRIPT_DIR}/system/gerych_swarm.sh" "$@"
fi

if [ -f "$SYSTEM_GERYCH" ]; then
    exec bash "$SYSTEM_GERYCH" "$@"
else
    echo "❌ Error: Gerych runner not found at $SYSTEM_GERYCH"
    exit 1
fi
