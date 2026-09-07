# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_inspect_hermes_baseline"
# purpose: "Inspect and record local baseline of core/hermes_agent for Phase C."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

import os
import json
import subprocess

def list_files(root_dir):
    rel_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # exclude venv, git, pycache
        if '.venv' in dirpath or '__pycache__' in dirpath or '.git' in dirpath:
            continue
        for f in filenames:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root_dir)
            rel_files.append(rel)
    return sorted(rel_files)

if __name__ == "__main__":
    hermes_dir = os.path.abspath("core/hermes_agent")
    files = list_files(hermes_dir)
    print(f"Total tracked files in core/hermes_agent (excl venv/pycache): {len(files)}")
    print("Sample files:", json.dumps(files[:25], indent=2))
