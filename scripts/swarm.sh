#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/swarm.sh"
# purpose: "Root CLI entrypoint for launching and orchestrating DNK OS Swarm agents."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/system/gerych_swarm.sh" "$@"
