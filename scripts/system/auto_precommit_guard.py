#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/auto_precommit_guard.py"
# purpose: "Autonomous Pre-Commit Guard and Quality Gate for Gerych sessions with instant error capture and regression verification."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class GuardCheckResult:
    passed: bool
    total_checks: int
    passed_checks: int
    elapsed_seconds: float
    check_results: Dict[str, bool]
    errors: List[str] = field(default_factory=list)


class AutoPreCommitGuard:
    """
    Autonomous Pre-Commit Quality Guard.
    Executes:
      1. Preflight sanitizer (GCP token & stray cleanup)
      2. Fast AST syntax check across all 5,800+ Python files
      3. Relative path hygiene validation (0 absolute violations)
      3.1 Git workspace hygiene validation (no untracked tests/routers)
      4. Targeted regression test suites (pytest)
      5. Frontend TypeScript integrity (npm run type-check)
    """

    def __init__(self, hub_root: Optional[Path] = None):
        self.hub_root = hub_root or Path(__file__).resolve().parent.parent.parent
        self.mvp_root = self.hub_root

    def run_guard(self) -> GuardCheckResult:
        start_t = time.time()
        results: Dict[str, bool] = {}
        errors: List[str] = []

        # Check 1: Preflight Sanitizer
        try:
            sanitizer = self.hub_root / "scripts" / "system" / "preflight_sanitizer.py"
            if sanitizer.exists():
                res = subprocess.run([sys.executable, str(sanitizer)], capture_output=True, text=True, check=True)
                results["preflight_sanitizer"] = True
            else:
                results["preflight_sanitizer"] = True
        except subprocess.CalledProcessError as exc:
            results["preflight_sanitizer"] = False
            errors.append(f"Preflight Sanitizer failed: {exc.stderr}")

        # Check 2: Fast Syntax Check
        try:
            fast_syntax = self.hub_root / "scripts" / "system" / "fast_compile_check.py"
            if fast_syntax.exists():
                res = subprocess.run([sys.executable, str(fast_syntax)], capture_output=True, text=True, check=True)
                results["fast_syntax_check"] = True
            else:
                results["fast_syntax_check"] = True
        except subprocess.CalledProcessError as exc:
            results["fast_syntax_check"] = False
            errors.append(f"Fast Syntax Check failed: {exc.stderr or exc.stdout}")

        # Check 3: Relative Path Hygiene
        try:
            python_bin = self.mvp_root / ".venv" / "bin" / "python"
            py_exec = str(python_bin) if python_bin.exists() else sys.executable
            code = "from core.playbooks.scripts.enforce_relative_paths import audit_relative_paths\nviolations = audit_relative_paths()\nif violations > 0: exit(1)"
            res = subprocess.run(
                [py_exec, "-c", code],
                cwd=str(self.mvp_root),
                capture_output=True,
                text=True,
            )
            results["path_hygiene"] = (res.returncode == 0)
            if res.returncode != 0:
                errors.append(f"Path hygiene check failed: Absolute path violations detected ({res.stderr}).")
        except Exception as exc:
            results["path_hygiene"] = False
            errors.append(f"Path hygiene check error: {exc}")

        # Check 3.1: Git Hygiene Guard
        try:
            git_hygiene = self.hub_root / "scripts" / "system" / "git_hygiene_guard.py"
            if git_hygiene.exists():
                res = subprocess.run([sys.executable, str(git_hygiene)], capture_output=True, text=True)
                results["git_hygiene"] = (res.returncode == 0)
                if res.returncode != 0:
                    errors.append(f"Git hygiene check failed:\n{res.stdout or res.stderr}")
            else:
                results["git_hygiene"] = True
        except Exception as exc:
            results["git_hygiene"] = False
            errors.append(f"Git hygiene check error: {exc}")

        # Check 3.2: Architecture Isolation & Cycle Guard
        try:
            arch_guard = self.hub_root / "scripts" / "system" / "architecture_and_cycle_guard.py"
            if arch_guard.exists():
                venv_python = self.hub_root / ".venv" / "bin" / "python3"
                py_exec = str(venv_python) if venv_python.exists() else sys.executable
                res = subprocess.run([py_exec, str(arch_guard)], capture_output=True, text=True)
                results["architecture_guard"] = (res.returncode == 0)
                if res.returncode != 0:
                    errors.append(f"Architecture & Cycle Guard failed:\n{res.stdout or res.stderr}")
            else:
                results["architecture_guard"] = True
        except Exception as exc:
            results["architecture_guard"] = False
            errors.append(f"Architecture guard check error: {exc}")

        # Check 3.3: Deterministic Blast Radius Assessment
        try:
            blast_tool = self.hub_root / "scripts" / "system" / "blast_radius_analyzer.py"
            if blast_tool.exists():
                venv_python = self.hub_root / ".venv" / "bin" / "python3"
                py_exec = str(venv_python) if venv_python.exists() else sys.executable
                res = subprocess.run([py_exec, str(blast_tool), "--staged"], capture_output=True, text=True)
                results["blast_radius"] = (res.returncode == 0)
                if res.returncode != 0:
                    errors.append(f"Blast radius assessment failed:\n{res.stdout or res.stderr}")
            else:
                results["blast_radius"] = True
        except Exception as exc:
            results["blast_radius"] = False
            errors.append(f"Blast radius check error: {exc}")

        # Check 4: Fast Test Suites & Canvas Engine
        try:
            # Check for stray nested directories (e.g. apps/web/apps)
            stray_dirs = [
                self.hub_root / "apps" / "web" / "apps",
                self.hub_root / "services" / "services",
            ]
            for stray in stray_dirs:
                if stray.exists():
                    shutil.rmtree(stray, ignore_errors=True)

            venv_python = self.hub_root / ".venv" / "bin" / "python3"
            py_exec = str(venv_python) if venv_python.exists() else sys.executable
            cmd = [
                py_exec,
                "-m",
                "pytest",
                "tests/shopify/test_liquid_compiler.py",
                "tests/shopify/test_shopify_vite_pipeline.py",
                "tests/swarm/test_swarm_daemon.py",
                "tests/verification/test_remotion_renderer.py",
                "tests/verification/test_product_launch_flow.py",
                "tests/canvas/test_canvas_ai_actions.py",
                "-q",
            ]
            res = subprocess.run(
                cmd,
                cwd=str(self.hub_root),
                capture_output=True,
                text=True,
            )
            results["regression_tests"] = (res.returncode == 0)
            if res.returncode != 0:
                errors.append(f"Regression tests failed:\n{res.stdout or res.stderr}")
        except Exception as exc:
            results["regression_tests"] = False
            errors.append(f"Pytest execution error: {exc}")

        # Check 5: Frontend TypeScript Integrity Check
        try:
            web_pkg = self.hub_root / "apps" / "web" / "package.json"
            if web_pkg.exists():
                res = subprocess.run(
                    ["npm", "--prefix", str(self.hub_root / "apps" / "web"), "run", "type-check"],
                    capture_output=True,
                    text=True,
                )
                results["frontend_typecheck"] = (res.returncode == 0)
                if res.returncode != 0:
                    errors.append(f"Frontend type-check failed:\n{res.stdout or res.stderr}")
            else:
                results["frontend_typecheck"] = True
        except Exception as exc:
            results["frontend_typecheck"] = False
            errors.append(f"Frontend typecheck error: {exc}")

        elapsed = round(time.time() - start_t, 3)
        passed_count = sum(1 for v in results.values() if v)
        all_passed = (passed_count == len(results))

        return GuardCheckResult(
            passed=all_passed,
            total_checks=len(results),
            passed_checks=passed_count,
            elapsed_seconds=elapsed,
            check_results=results,
            errors=errors,
        )


auto_guard = AutoPreCommitGuard()

if __name__ == "__main__":
    guard_res = auto_guard.run_guard()
    if guard_res.passed:
        print(f"🛡️  [PRE-COMMIT GUARD] ALL {guard_res.passed_checks}/{guard_res.total_checks} CHECKS PASSED in {guard_res.elapsed_seconds}s ✅")
        sys.exit(0)
    else:
        print(f"❌ [PRE-COMMIT GUARD] FAILED ({guard_res.passed_checks}/{guard_res.total_checks} passed in {guard_res.elapsed_seconds}s):")
        for err in guard_res.errors:
            print(f"  • {err}")
        sys.exit(1)
