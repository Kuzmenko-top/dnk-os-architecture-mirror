# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/check_path_hygiene.py"
# purpose: "Audit Python files for hardcoded absolute paths in production code."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import glob


def audit_relative_paths(root_dir: str = ".") -> int:
    violations = 0
    target_dirs = ["apps", "core", "services"]
    
    for tdir in target_dirs:
        python_files = glob.glob(os.path.join(root_dir, tdir, "**", "*.py"), recursive=True)
        for file_path in python_files:
            if ".venv" in file_path or "node_modules" in file_path or "build" in file_path:
                continue
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    for idx, line in enumerate(lines):
                        line_str = line.strip()
                        if line_str.startswith("#") or "mrh_id" in line_str or "HUB_ROOT" in line_str or "username" in line_str:
                            continue
                        if "/Users/" in line_str and "<username>" not in line_str and "developer" not in line_str:
                            violations += 1
                            print(f"⚠️ Hardcoded user absolute path in {file_path}:{idx+1}: {line_str}")
            except Exception:
                pass

    return violations


if __name__ == "__main__":
    v = audit_relative_paths()
    print(f"Total path hygiene violations: {v}")
