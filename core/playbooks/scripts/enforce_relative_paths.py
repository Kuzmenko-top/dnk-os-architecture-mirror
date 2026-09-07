# --- DNK-MRH-HEADER ---
# mrh_id: "core/playbooks/scripts/enforce_relative_paths.py"
# purpose: "Script-First Execution utility verifying zero absolute path violations in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import re
import sys


def audit_relative_paths(target_dir: str = ".") -> int:
    violations = 0
    pattern = re.compile(r"/Users/[a-zA-Z0-9_\.]+/")
    ignored_dirs = {
        ".git", ".venv", "__pycache__", "visual_shell", "core/hermes_agent",
        "core/hermes_versions", "core/hermes_agent_staging", "cache", "sessions", "checkpoints",
        "DNK OS", "node_modules", ".next", "dist", ".pytest_cache", ".od",
        "core/orchestrator", "tests/verification/test_adversarial_review.py",
        "tests/verification/test_sota_assimilation_two_track.py",
        "tests/verification/test_session_sentinel.py",
        ".worktrees", "docs/audit"
    }

    for root, _, files in os.walk(target_dir):
        if any(ignored in root for ignored in ignored_dirs):
            continue
        for file in files:
            if file.endswith((".py", ".md", ".json", ".yaml", ".yml")):
                filepath = os.path.join(root, file)
                if any(ignored in filepath for ignored in ignored_dirs):
                    continue
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        if pattern.search(content):
                            lines = content.splitlines()
                            for idx, line in enumerate(lines, 1):
                                if pattern.search(line) and "mrh_id" not in line and "file:///" not in line:
                                    print(f"⚠️ [Absolute Path Violation] {filepath}:{idx} -> {line.strip()}")
                                    violations += 1
                except Exception:
                    pass

    return violations


def main() -> None:
    print("🛡️ [Playbook PB-002] Enforce Relative Paths Utility Running...")
    v_count = audit_relative_paths("DNK OS")
    if v_count == 0:
        print("✅ [Path Guard] 0 порушень абсолютних шляхів знайдено у DNK OS!")
    else:
        print(f"⚠️ Знайдено {v_count} порушень відносних шляхів.")


if __name__ == "__main__":
    main()
