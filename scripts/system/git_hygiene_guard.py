#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/git_hygiene_guard.py"
# purpose: "Git Hygiene Guard ensuring no untracked tests or API routers exist and router registrations are staged."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


class GitHygieneGuard:
    """
    Validates git workspace hygiene to prevent forgotten test files,
    untracked routers, and unstaged router registration files.
    """

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent.parent

    def get_porcelain_status(self) -> List[Tuple[str, str]]:
        res = subprocess.run(
            ["git", "status", "--porcelain", "-u"],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        entries = []
        for line in res.stdout.splitlines():
            if len(line) >= 4:
                status = line[:2]
                path = line[3:].strip()
                # If path contains quotes or arrow for rename, normalize
                if " -> " in path:
                    path = path.split(" -> ")[1].strip()
                entries.append((status, path))
        return entries

    def run_check(self) -> Tuple[bool, List[str]]:
        entries = self.get_porcelain_status()
        errors: List[str] = []

        untracked_tests_or_routers: List[str] = []
        router_changes: List[str] = []
        main_py_status: str = ""
        routers_init_status: str = ""

        for status, path in entries:
            is_untracked = "?" in status
            norm_path = path.replace("\\", "/")

            if norm_path == "apps/api/main.py":
                main_py_status = status
            elif norm_path == "apps/api/routers/__init__.py":
                routers_init_status = status

            # Check for router changes
            if norm_path.startswith("apps/api/routers/") and norm_path != "apps/api/routers/__init__.py":
                if norm_path.endswith(".py"):
                    router_changes.append(norm_path)

            # Untracked test or router check
            if is_untracked and norm_path.endswith(".py"):
                if (
                    norm_path.startswith("tests/")
                    or norm_path.startswith("core/tests/")
                    or norm_path.startswith("apps/api/routers/")
                ):
                    untracked_tests_or_routers.append(norm_path)

        if untracked_tests_or_routers:
            errors.append("❌ GIT HYGIENE ERROR: Found untracked test/router files! You must git add them:")
            for p in untracked_tests_or_routers:
                errors.append(f"  - {p}")

        # Check router registration integrity
        if router_changes:
            # If router files have modifications or were added, ensure registration files are not unstaged modified
            # Status codes in git porcelain:
            # ' M' = modified in work tree, unstaged
            # '??' = untracked
            if main_py_status in (" M", "??"):
                errors.append(
                    f"❌ GIT HYGIENE ERROR: apps/api/main.py has unstaged changes ({main_py_status}) while router updates exist! Stage it with git add."
                )
            if routers_init_status in (" M", "??"):
                errors.append(
                    f"❌ GIT HYGIENE ERROR: apps/api/routers/__init__.py has unstaged changes ({routers_init_status}) while router updates exist! Stage it with git add."
                )

        passed = len(errors) == 0
        return passed, errors


def main() -> int:
    guard = GitHygieneGuard()
    passed, errors = guard.run_check()

    if not passed:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("✅ GIT HYGIENE PASSED: No untracked tests or router drift detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
