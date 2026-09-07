# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_generate_patch_inventory"
# purpose: "Analyze and categorize diffs between local fork core/hermes_agent and upstream v0.21.0 in core/hermes_agent_staging."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

import os
import hashlib
import json

def get_file_hashes(root_dir):
    files = {}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude runtime virtualenvs, git directories, caches
        if any(ignored in dirpath for ignored in ['.venv', '__pycache__', '.git', '.pytest_cache', 'node_modules', '.cache']):
            continue
        for f in filenames:
            if f.endswith('.pyc') or f == '.DS_Store':
                continue
            full_path = os.path.join(dirpath, f)
            rel_path = os.path.relpath(full_path, root_dir)
            h = hashlib.sha256()
            try:
                with open(full_path, 'rb') as fp:
                    while chunk := fp.read(65536):
                        h.update(chunk)
                files[rel_path] = h.hexdigest()
            except Exception:
                pass
    return files

def categorize_dnk_file(path):
    p_lower = path.lower()
    if any(k in p_lower for k in ['acp_adapter', 'acp_registry', 'agent_helpers', 'gateway_proxy']):
        return "dnk_specific_adapter"
    if any(k in p_lower for k in ['check_mrh', 'verify_all', 'quality_gate', 'mrh']):
        return "security_and_integrity_check"
    if any(k in p_lower for k in ['dnk', 'video-audit', 'spatial']):
        return "dnk_domain_artifact"
    if any(k in p_lower for k in ['log', 'tmp', 'cache', '.lock']):
        return "cache_or_generated"
    if any(k in p_lower for k in ['token', 'secret', '.env']):
        return "secrets_or_local_config"
    return "local_diagnostic_or_custom"

def run_inventory():
    prod_dir = os.path.abspath("core/hermes_agent")
    staging_dir = os.path.abspath("core/hermes_agent_staging")

    prod_files = get_file_hashes(prod_dir)
    staging_files = get_file_hashes(staging_dir)

    prod_keys = set(prod_files.keys())
    staging_keys = set(staging_files.keys())

    added_in_prod = prod_keys - staging_keys
    added_in_upstream = staging_keys - prod_keys
    common_keys = prod_keys & staging_keys

    identical_common = []
    modified_common = []

    for k in common_keys:
        if prod_files[k] == staging_files[k]:
            identical_common.append(k)
        else:
            modified_common.append(k)

    categorized_added_in_prod = {}
    for f in added_in_prod:
        cat = categorize_dnk_file(f)
        categorized_added_in_prod.setdefault(cat, []).append(f)

    # Classify modified files
    modified_classification = {}
    for f in modified_common:
        if f in ['run_agent.py', 'agent.py', 'cli.py', 'hermes_cli/main.py']:
            modified_classification[f] = "core_loop_or_entrypoint"
        elif 'tool' in f:
            modified_classification[f] = "toolset_or_tool_runtime"
        elif 'config' in f or 'constant' in f:
            modified_classification[f] = "config_or_constants"
        else:
            modified_classification[f] = "upstream_or_local_refactor"

    inventory = {
        "summary": {
            "production_total_files": len(prod_files),
            "staging_upstream_total_files": len(staging_files),
            "identical_files": len(identical_common),
            "modified_in_v0_21_0": len(modified_common),
            "dnk_exclusive_files": len(added_in_prod),
            "upstream_new_files": len(added_in_upstream)
        },
        "dnk_exclusive_categorization": {
            cat: len(files) for cat, files in categorized_added_in_prod.items()
        },
        "dnk_exclusive_samples": {
            cat: files[:10] for cat, files in categorized_added_in_prod.items()
        },
        "modified_common_classification": modified_classification,
        "sample_upstream_new_files": sorted(list(added_in_upstream))[:20]
    }

    out_file = "docs/verification/hermes_patch_inventory.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(inventory, f, indent=2)

    print("=== PATCH INVENTORY SUMMARY ===")
    print(json.dumps(inventory["summary"], indent=2))
    print("\n=== DNK EXCLUSIVE CATEGORIES ===")
    print(json.dumps(inventory["dnk_exclusive_categorization"], indent=2))
    print(f"\nInventory saved to {out_file}")

if __name__ == "__main__":
    run_inventory()
