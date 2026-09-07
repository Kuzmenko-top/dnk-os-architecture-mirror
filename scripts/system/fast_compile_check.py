#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/fast_compile_check.py"
# purpose: "Blazing-fast syntax and AST compilation check for all Python files, skipping .venv and node_modules."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import py_compile
import sys
import time
from pathlib import Path

IGNORE_DIRS = {
    ".venv", "venv", "node_modules", ".next", ".git", "__pycache__",
    ".pytest_cache", "dist", "build", ".hermes", "sessions", "terminal-sessions",
    "hermes_agent_staging", "hermes_versions", "backups", "backup", "tmp", ".tmp",
    "orchestrator", "checkpoints", "staging", "pastes", "sandboxes"
}

def check_syntax(root_dir: Path) -> int:
    start_time = time.time()
    errors = 0
    checked_count = 0

    for current_dir, dirs, files in os.walk(root_dir):
        # Filter out ignored directories in-place for high speed
        dirs[:] = [
            d for d in dirs 
            if d not in IGNORE_DIRS 
            and not d.startswith(".") 
            and "backup" not in d.lower()
            and "staging" not in d.lower()
        ]

        for file in files:
            if file.endswith(".py"):
                file_path = Path(current_dir) / file
                checked_count += 1
                try:
                    py_compile.compile(str(file_path), doraise=True)
                except py_compile.PyCompileError as exc:
                    print(f"❌ Syntax error in {file_path}:\n  {exc}")
                    errors += 1
                except Exception as exc:
                    print(f"❌ Failed to parse {file_path}: {exc}")
                    errors += 1

    elapsed = time.time() - start_time
    if errors == 0:
        print(f"✅ Fast Syntax Check passed: {checked_count} Python files compiled in {elapsed:.2f}s (0 errors).")
        return 0
    else:
        print(f"❌ Fast Syntax Check failed: {errors} errors found in {checked_count} files ({elapsed:.2f}s).")
        return 1

if __name__ == "__main__":
    hub_root = Path(__file__).resolve().parent.parent.parent
    sys.exit(check_syntax(hub_root))
