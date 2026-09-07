# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_detailed_tier_audit"
# purpose: "Perform in-depth code-level audit of Tier 0, Tier 1, Tier 2 components between core/hermes_agent and staging."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

import os
import difflib
import json

CRITICAL_COMPONENTS = [
    ("run_agent.py", "Tier 0: Agent Loop & CLI Runner"),
    ("tools/delegate_tool.py", "Tier 0: Delegation & Subagent Dispatch"),
    ("tools/approval.py", "Tier 0: Approval Engine"),
    ("tools/write_approval.py", "Tier 1: Write Approval & Path Guard"),
    ("hermes_state.py", "Tier 0: State DB & Session Persistence"),
    ("hermes_state_schema.py", "Tier 0: SQLite Schema & Migrations"),
    ("hermes_constants.py", "Tier 0: Runtime Constants & Defaults"),
    ("toolsets.py", "Tier 0: Tool Dispatch & Registration"),
    ("agent/redact.py", "Tier 1: Secret Redaction & Token Masking"),
    ("tools/process_registry.py", "Tier 0: Background Process Guard"),
    ("cron/scheduler.py", "Tier 2: Cron Lifecycle & Continuity"),
    ("cron/lifecycle_guard.py", "Tier 2: Cron State Guard"),
    ("hermes_cli/main.py", "Tier 0: Launcher Integration"),
    ("hermes_cli/config.py", "Tier 0: Config Loading & Env Parsing")
]

def analyze_diff(rel_path):
    p_prod = os.path.join("core/hermes_agent", rel_path)
    p_staging = os.path.join("core/hermes_agent_staging", rel_path)
    
    exists_prod = os.path.exists(p_prod)
    exists_staging = os.path.exists(p_staging)
    
    if not exists_prod or not exists_staging:
        return {
            "status": "missing_in_one",
            "exists_prod": exists_prod,
            "exists_staging": exists_staging,
            "diff_lines": 0
        }
        
    with open(p_prod, 'r', encoding='utf-8', errors='ignore') as f1:
        lines1 = f1.readlines()
    with open(p_staging, 'r', encoding='utf-8', errors='ignore') as f2:
        lines2 = f2.readlines()
        
    diff = list(difflib.unified_diff(lines1, lines2, fromfile=f"prod/{rel_path}", tofile=f"staging/{rel_path}"))
    
    # Analyze changes
    added = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
    removed = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))
    
    # Check for specific behaviors
    content1 = "".join(lines1)
    content2 = "".join(lines2)
    
    return {
        "status": "identical" if len(diff) == 0 else "modified",
        "exists_prod": True,
        "exists_staging": True,
        "lines_prod": len(lines1),
        "lines_staging": len(lines2),
        "diff_lines": len(diff),
        "lines_added": added,
        "lines_removed": removed,
        "diff_preview": "".join(diff[:40]) if diff else ""
    }

def main():
    results = {}
    print("=== Deep Audit of Critical Tier 0 & Tier 1 Components ===")
    for rel_path, tier_desc in CRITICAL_COMPONENTS:
        res = analyze_diff(rel_path)
        results[rel_path] = {
            "tier": tier_desc,
            "analysis": res
        }
        print(f"\n[{tier_desc}] -> {rel_path}")
        print(f"  Status: {res['status']} | Lines: Prod={res.get('lines_prod', 0)}, Staging={res.get('lines_staging', 0)} | Added: {res.get('lines_added', 0)}, Removed: {res.get('lines_removed', 0)}")
        if res.get("diff_preview"):
            print("  --- Diff Preview (First lines) ---")
            for dl in res["diff_preview"].splitlines()[:10]:
                print("   ", dl)

    with open("docs/verification/evidence/tier0_tier1_audit.json", "w") as fp:
        json.dump(results, fp, indent=2)
    print("\nSaved detailed audit to docs/verification/evidence/tier0_tier1_audit.json")

if __name__ == "__main__":
    main()
