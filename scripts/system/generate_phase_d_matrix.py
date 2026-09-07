# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_generate_phase_d_matrix"
# purpose: "Mathematically normalize file sets A, B, C, D and generate PHASE_D_FILE_MATRIX.csv with 5-Tier categorization."
# canonical_source: true
# alters_files: ["docs/verification/reports/PHASE_D_FILE_MATRIX.csv"]
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

import os
import csv
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
                size = os.path.getsize(full_path)
                with open(full_path, 'rb') as fp:
                    while chunk := fp.read(65536):
                        h.update(chunk)
                files[rel_path] = (h.hexdigest(), size)
            except Exception:
                pass
    return files

def classify_tier_for_modified(path):
    p = path.lower()
    
    # Tier 0: Critical Core
    tier_0_indicators = [
        'run_agent.py', 'agent.py', 'cli.py', 'hermes_cli/main.py',
        'hermes_constants.py', 'toolsets.py', 'agent/loop', 'agent/dispatch',
        'tools/delegate', 'session', 'state.db', 'approval', 'mcp/lifecycle',
        'providers/', 'process_guard', 'config.py', 'hermes_cli/'
    ]
    if any(k in p for k in tier_0_indicators):
        return 'Tier 0: Core Runtime'
        
    # Tier 1: Security & Boundaries
    tier_1_indicators = [
        'redact', 'security', 'permission', 'sandbox', 'boundary',
        'shopify', 'guard', 'secret', 'auth', 'policy'
    ]
    if any(k in p for k in tier_1_indicators):
        return 'Tier 1: Security & Control'
        
    # Tier 2: Orchestration
    tier_2_indicators = [
        'peer', 'steer', 'continuity', 'cron', 'orchestrat', 'subagent',
        'event', 'message_bus', 'task', 'workflow'
    ]
    if any(k in p for k in tier_2_indicators):
        return 'Tier 2: Orchestration'
        
    # Tier 3: Providers & MCP
    tier_3_indicators = [
        'mcp', 'provider', 'model', 'gateway', 'plugin', 'cost',
        'anthropic', 'openai', 'gemini', 'openrouter', 'vertex'
    ]
    if any(k in p for k in tier_3_indicators):
        return 'Tier 3: Providers & MCP'
        
    # Tier 4: Desktop, UX, Optional Skills
    return 'Tier 4: Desktop, UX & Skills'

def classify_dnk_exclusive(path):
    p = path.lower()
    if 'acp_adapter' in p or 'acp' in p:
        return 'ACP Adapter (Integration Boundary)'
    if any(k in p for k in ['mrh', 'verify_all', 'check_single']):
        return 'MRH Utilities (Verification Layer)'
    if 'tools/custom_' in p or (path.startswith('tools/') and 'tool' in p):
        return 'Custom Tools Package'
    if any(k in p for k in ['video', 'spatial', 'canvas', 'dna']):
        return 'DNK Control Plane & Domain Specs'
    if any(k in p for k in ['adapter', 'proxy', 'bridge']):
        return 'DNK Model Adapters'
    if any(k in p for k in ['log', 'tmp', 'cache', '.lock', 'dump', 'history']):
        return 'Caches / Generated Files'
    if any(k in p for k in ['test', 'script', 'inspect', 'measure', 'setup']):
        return 'Local Maintenance Scripts'
    return 'DNK Architectural Artifacts'

def main():
    prod_dir = os.path.abspath("core/hermes_agent")
    staging_dir = os.path.abspath("core/hermes_agent_staging")
    
    prod_files = get_file_hashes(prod_dir)
    staging_files = get_file_hashes(staging_dir)
    
    prod_keys = set(prod_files.keys())
    staging_keys = set(staging_files.keys())
    
    # Mathematical Sets
    A_keys = staging_keys - prod_keys      # Upstream Only
    B_keys = prod_keys - staging_keys      # DNK Fork Only
    common_keys = prod_keys & staging_keys
    
    C_keys = set()                         # Common Identical
    D_keys = set()                         # Common Modified (Different Content)
    
    for k in common_keys:
        if prod_files[k][0] == staging_files[k][0]:
            C_keys.add(k)
        else:
            D_keys.add(k)
            
    # Verification of disjoint sets
    total_universe = A_keys | B_keys | C_keys | D_keys
    len_A = len(A_keys)
    len_B = len(B_keys)
    len_C = len(C_keys)
    len_D = len(D_keys)
    len_total = len(total_universe)
    
    print(f"=== Mathematical Set Normalization ===")
    print(f"Set A (Upstream Only):            {len_A}")
    print(f"Set B (DNK Fork Only):            {len_B}")
    print(f"Set C (Identical Common):         {len_C}")
    print(f"Set D (Modified Common):          {len_D}")
    print(f"--------------------------------------")
    print(f"Sum (|A| + |B| + |C| + |D|):      {len_A + len_B + len_C + len_D}")
    print(f"Total Unique Files (Universe):    {len_total}")
    print(f"Disjoint Set Verification:        {'VERIFIED (EXACT MATCH)' if len_A + len_B + len_C + len_D == len_total else 'FAILED'}")
    print(f"Total Staging Upstream (|A∪C∪D|): {len(staging_keys)} (Expected: {len_A + len_C + len_D})")
    print(f"Total Prod Fork (|B∪C∪D|):        {len(prod_keys)} (Expected: {len_B + len_C + len_D})")
    
    # Tier breakdown for D
    tier_counts = {
        'Tier 0: Core Runtime': 0,
        'Tier 1: Security & Control': 0,
        'Tier 2: Orchestration': 0,
        'Tier 3: Providers & MCP': 0,
        'Tier 4: Desktop, UX & Skills': 0
    }
    
    csv_rows = []
    
    for path in sorted(total_universe):
        in_prod = path in prod_keys
        in_staging = path in staging_keys
        
        prod_hash = prod_files[path][0] if in_prod else ""
        prod_size = prod_files[path][1] if in_prod else 0
        staging_hash = staging_files[path][0] if in_staging else ""
        staging_size = staging_files[path][1] if in_staging else 0
        
        if path in A_keys:
            subset = "A_upstream_only"
            tier = "Tier 4: Upstream Feature"
            action = "Evaluate for Assimilation Backlog"
            classification = "New upstream feature/skill/skin"
        elif path in B_keys:
            subset = "B_dnk_only"
            tier = "DNK Extension Component"
            classification = classify_dnk_exclusive(path)
            action = "Keep in DNK Layer / Adapt to Extension Point"
        elif path in C_keys:
            subset = "C_identical"
            tier = "Common Baseline"
            classification = "Identical upstream & fork file"
            action = "No action required (100% matched)"
        else: # D_keys
            subset = "D_modified"
            tier = classify_tier_for_modified(path)
            tier_counts[tier] += 1
            classification = "Modified in v0.21.0 vs local fork"
            if 'Tier 0' in tier:
                action = "MANDATORY Deep 3-way merge & regression audit"
            elif 'Tier 1' in tier:
                action = "Enforce DNK zero-regression security rule"
            elif 'Tier 2' in tier:
                action = "Bridge to DNK TaskDNA / Contracts"
            elif 'Tier 3' in tier:
                action = "Verify read-only sandbox isolation"
            else:
                action = "Defer to Assimilation Backlog"
                
        csv_rows.append([
            subset, path, tier, classification, action,
            prod_size, prod_hash[:12] if prod_hash else "",
            staging_size, staging_hash[:12] if staging_hash else ""
        ])
        
    # Write CSV Matrix
    out_csv = "docs/verification/reports/PHASE_D_FILE_MATRIX.csv"
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "subset", "file_path", "tier", "classification", "recommended_action",
            "prod_size_bytes", "prod_sha256_short",
            "staging_size_bytes", "staging_sha256_short"
        ])
        writer.writerows(csv_rows)
        
    print(f"\nCSV Matrix written: {out_csv} ({len(csv_rows)} rows)")
    print("\n=== Tier Breakdown for Set D (Modified Files) ===")
    for t, c in tier_counts.items():
        print(f"  {t}: {c} files")
        
    # Save JSON summary for subsequent reports
    summary_data = {
        "mathematical_reconciliation": {
            "set_A_upstream_only": len_A,
            "set_B_dnk_only": len_B,
            "set_C_identical": len_C,
            "set_D_modified": len_D,
            "total_universe": len_total,
            "formula_verified": len_A + len_B + len_C + len_D == len_total,
            "staging_upstream_total": len(staging_keys),
            "prod_fork_total": len(prod_keys)
        },
        "set_D_tier_breakdown": tier_counts
    }
    
    with open("docs/verification/evidence/phase_d_set_reconciliation.json", "w") as jf:
        json.dump(summary_data, jf, indent=2)
    print("\nSaved evidence: docs/verification/evidence/phase_d_set_reconciliation.json")

if __name__ == "__main__":
    main()
