# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_compare_dependencies"
# purpose: "Compare dependencies between production and staging venvs."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

import subprocess
import json
import os

def get_pkgs(py_path):
    out = subprocess.check_output(f"uv pip list --format=json --python '{py_path}'", shell=True, text=True)
    items = json.loads(out)
    return {item['name']: item['version'] for item in items}

def compare():
    prod_py = os.path.abspath("core/hermes_agent/.venv/bin/python")
    staging_py = os.path.abspath("core/hermes_agent_staging/.venv/bin/python")
    
    prod_pkgs = get_pkgs(prod_py)
    staging_pkgs = get_pkgs(staging_py)
    
    prod_names = set(prod_pkgs.keys())
    staging_names = set(staging_pkgs.keys())
    
    only_in_prod = sorted(list(prod_names - staging_names))
    only_in_staging = sorted(list(staging_names - prod_names))
    
    version_diff = {}
    for name in (prod_names & staging_names):
        if prod_pkgs[name] != staging_pkgs[name]:
            version_diff[name] = {
                "prod": prod_pkgs[name],
                "staging": staging_pkgs[name]
            }
            
    diff_report = {
        "python_version": "3.12.13",
        "uv_version": subprocess.check_output("uv --version", shell=True, text=True).strip(),
        "total_production_packages": len(prod_pkgs),
        "total_staging_packages": len(staging_pkgs),
        "version_differences": version_diff,
        "packages_only_in_staging": only_in_staging,
        "packages_only_in_production": only_in_prod
    }
    
    out_file = "docs/verification/hermes_dependency_diff.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(diff_report, f, indent=2)
        
    print("=== DEPENDENCY DIFF REPORT ===")
    print(json.dumps(diff_report, indent=2))

if __name__ == "__main__":
    compare()
