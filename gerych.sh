#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "gerych.sh"
# purpose: "Root-level alias launcher for Gerych Orchestrator."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.3.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${ROOT_DIR}/scripts/gerych.sh" "$@"
