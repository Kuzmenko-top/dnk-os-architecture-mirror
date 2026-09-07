# --- DNK-MRH-HEADER ---
# mrh_id: "core/playbooks/scripts/run_system_health_audit.py"
# purpose: "Script-First Execution utility auditing total system health across DNK OS services and agents."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import sys


def check_system_health() -> bool:
    required_paths = [
        "AGENTS.md",
        "services/dnk_obsidian_task_forest",
        "core/agent_factory",
        "core/playbooks",
        "docs/tasks",
    ]

    all_ok = True
    for p in required_paths:
        exists = os.path.exists(p)
        status_icon = "✅" if exists else "❌"
        print(f"{status_icon} [Component Check] `{p}` -> {'Exists' if exists else 'MISSING'}")
        if not exists:
            all_ok = False

    return all_ok


def main() -> None:
    print("=================================================================")
    print("🩺 [Playbook PB-003] System Health Audit Utility Running...")
    print("=================================================================")
    ok = check_system_health()
    if ok:
        print("\n🎉 [System Audit] Всі ключові компоненти DNK OS в ідеальному стані!")
    else:
        print("\n⚠️ [System Audit] Знайдено відсутні компоненти.")


if __name__ == "__main__":
    main()
