# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_audit_workspace_and_skills"
# purpose: "Comprehensive workspace, skills, and swarm capacity audit script."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import os
import subprocess
from core.orchestrator.swarm_health import SwarmHealthEngine
try:
    from core.scones_memory import SCONESMemoryEngine
    scones_available = True
except Exception:
    scones_available = False

def run_audit():
    print("================================================================================")
    print("🔍 DNK OS & GERYCH PRIME: FULL WORKSPACE & SKILLS CAPACITY AUDIT (100% CHECK)")
    print("================================================================================")

    # 1. Swarm Health
    engine = SwarmHealthEngine()
    report = engine.get_health_status("ws-alpha-001")
    print("\n[1] 🤖 SWARM HEALTH & 14 SPECIALIZED AGENTS:")
    print(f"  • Overall Status: {report['overall_status'].upper()}")
    print(f"  • Status Reasons: {', '.join(report['status_reasons'])}")
    print(f"  • Registered Swarm Workers: {report['active_workers']['total_agents']}/14")
    print(f"  • Total Spend USD: ${report['accounting']['total_cost_usd']:.4f} (Limit: ${report['accounting']['spend_limit_usd']:.2f})")
    print(f"  • Sentinel Alerts: {report['sentinel'].get('active_alerts_count', 0)} (Critical: {report['sentinel'].get('critical_count', 0)}, Warning: {report['sentinel'].get('warning_count', 0)})")
    print(f"  • Pending Self-Heal Plans: {report['sentinel'].get('pending_self_heal_tasks', 0)}")
    print(f"  • Canvas Bridge: {report['canvas_bridge'].get('nodes_count', 0)} nodes, {report['canvas_bridge'].get('edges_count', 0)} edges")

    # 2. Skills
    skills_dir = "core/orchestrator/agents/gerych_prime/skills"
    all_skills = []
    pruned_skills = []
    category_map = {}
    for root, dirs, files in os.walk(skills_dir):
        if "SKILL.md" in files:
            rel = os.path.relpath(root, skills_dir)
            all_skills.append(rel)
            cat = rel.split("/")[0] if "/" in rel else "root"
            category_map[cat] = category_map.get(cat, 0) + 1
            skill_path = os.path.join(root, "SKILL.md")
            try:
                with open(skill_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "[SKILL_PRUNED]" in content:
                        pruned_skills.append(rel)
            except Exception as e:
                pass

    print("\n[2] 🧠 GERYCH PROCEDURAL SKILLS INVENTORY:")
    print(f"  • Total Skills Installed: {len(all_skills)}")
    print(f"  • Skill Categories: {len(category_map)} categories")
    for cat, count in sorted(category_map.items()):
        print(f"    - {cat}: {count} skill(s)")
    print(f"  • Pruned Skills on Disk: {len(pruned_skills)} ({pruned_skills if pruned_skills else 'None - 100% Intact'})")

    # 3. SCONES & Error Distillation
    mem_count = 0
    if scones_available:
        try:
            scones = SCONESMemoryEngine()
            memories = scones.get_memories("ws-alpha-001")
            mem_count = len(memories)
        except Exception:
            pass
    print("\n[3] 🧬 SCONES COGNITIVE MEMORY & SELF-HEALING:")
    print(f"  • Active SCONES Memories: {mem_count} indexed entries")
    distill_file = "core/self_healing/error_solutions.json"
    dist_count = 0
    if os.path.exists(distill_file):
        try:
            with open(distill_file, "r") as f:
                dist_count = len(json.load(f))
        except Exception:
            pass
    print(f"  • Distilled Error Solutions: {dist_count} solved patterns")

    # 4. Pytest & Code Verification
    print("\n[4] 🧪 TEST SUITES VERIFICATION:")
    p = subprocess.run(["./.venv/bin/pytest", "tests/verification/", "-q", "--disable-warnings"], capture_output=True, text=True)
    summary_line = p.stdout.strip().splitlines()[-1] if p.stdout else p.stderr
    print(f"  • Verification Tests: {summary_line}")

    # 5. Frontend TS Check
    print("\n[5] 💻 FRONTEND TYPE SAFETY & BUILD:")
    p_tsc = subprocess.run(["./apps/web/node_modules/.bin/tsc", "-p", "apps/web/tsconfig.json", "--noEmit"], capture_output=True, text=True)
    print(f"  • Apps Web TypeScript: {'100% CLEAN (0 errors)' if p_tsc.returncode == 0 else f'ERRORS: {p_tsc.stdout}'}")

    # 6. Git Hygiene & Branch Status
    print("\n[6] 🌿 GIT WORKSPACE HYGIENE:")
    p_branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    branch = p_branch.stdout.strip()
    p_status = subprocess.run(["git", "status", "-s"], capture_output=True, text=True)
    modified = [line for line in p_status.stdout.splitlines() if line.strip().startswith("M")]
    untracked = [line for line in p_status.stdout.splitlines() if line.strip().startswith("??")]
    print(f"  • Current Branch: {branch}")
    print(f"  • Modified Tracked Files: {len(modified)}")
    print(f"  • Untracked Files: {len(untracked)}")

    print("\n================================================================================")

if __name__ == "__main__":
    run_audit()
