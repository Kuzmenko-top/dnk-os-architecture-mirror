# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_setup_staging_instance"
# purpose: "Create isolated staging instance and config for Hermes v0.21.0 in ~/.hermes_staging."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

import os
import yaml

def setup_staging():
    staging_home = os.path.expanduser("~/.hermes_staging")
    subdirs = ["logs", "sessions", "cache", "memories", "skills", "terminal-sessions"]
    for sd in subdirs:
        os.makedirs(os.path.join(staging_home, sd), exist_ok=True)
        
    staging_config = {
        "_config_version": 2,
        "model": {
            "default": "gemini-3.7-flash",
            "provider": "vertex"
        },
        "providers": {
            "vertex": {
                "project_id": "dnk-dev-01"
            }
        },
        "terminal": {
            "timeout": 60
        },
        "privacy": {
            "telemetry": False
        },
        "cron": {
            "allow_agent_scheduling": True
        },
        "security": {
            "sandbox": "strict"
        },
        "gateway": {
            "port": 9899,
            "auto_start": False
        }
    }
    
    cfg_file = os.path.join(staging_home, "config.yaml")
    with open(cfg_file, "w") as f:
        yaml.dump(staging_config, f, default_flow_style=False)
        
    print(f"Staging home initialized at: {staging_home}")
    print(f"Staging config written to: {cfg_file}")

if __name__ == "__main__":
    setup_staging()
