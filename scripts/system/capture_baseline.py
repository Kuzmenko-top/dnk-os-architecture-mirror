# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_capture_baseline"
# purpose: "Capture full baseline for Phase C: production runtime snapshot and patch inventory."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime

def sha256_file(filepath):
    if not os.path.isfile(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def capture():
    git_sha = run_cmd("git rev-parse HEAD")
    hermes_bin = os.path.expanduser("~/.local/bin/hermes")
    hermes_ver_raw = run_cmd(f"{hermes_bin} --version")
    
    config_path = os.path.expanduser("~/.hermes/config.yaml")
    config_sha = sha256_file(config_path)
    
    state_db_path = os.path.expanduser("~/.hermes/state.db")
    state_db_sha = sha256_file(state_db_path)
    
    sessions_db_path = os.path.expanduser("~/.hermes/sessions.db")
    sessions_db_sha = sha256_file(sessions_db_path)
    
    active_proc = run_cmd("ps -ef | grep 'python3 ./hermes' | grep -v grep | head -n 3")
    
    # Packages in production venv
    venv_py = os.path.abspath("core/hermes_agent/.venv/bin/python")
    pkgs = run_cmd(f"uv pip list --python '{venv_py}'")
    
    baseline = {
        "baseline": {
            "runtime_version": "0.20.5",
            "source_type": "embedded_unmanaged_fork",
            "git_sha": git_sha,
            "state_db_sha256": state_db_sha,
            "config_sha256": config_sha,
            "sessions_db_sha256": sessions_db_sha,
            "active_process": active_proc,
            "captured_at": datetime.utcnow().isoformat() + "Z",
            "paths": {
                "production_runtime_path": os.path.abspath("core/hermes_agent"),
                "production_venv_path": os.path.abspath("core/hermes_agent/.venv"),
                "production_config_path": config_path,
                "production_state_db": state_db_path
            }
        }
    }
    
    out_file = "docs/verification/hermes_production_baseline.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(baseline, f, indent=2)
    print(f"Captured baseline written to {out_file}")
    print(json.dumps(baseline, indent=2))

if __name__ == "__main__":
    capture()
