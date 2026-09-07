#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/blast_radius_analyzer.py"
# purpose: "Deterministic Blast Radius and Affected Surface Analyzer for DNK OS monorepo"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

HUB_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class BlastRadiusReport:
    changed_files: List[str]
    affected_domains: List[str]
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    required_pytests: List[str]
    required_vitests: List[str]
    requires_frontend_typecheck: bool
    requires_architecture_cycle_guard: bool
    summary: str


DOMAIN_MAP = {
    "apps/web": "frontend_web",
    "apps/api": "backend_api",
    "visual_shell": "visual_shell",
    "services": "services",
    "core": "core_orchestrator",
    "tests": "tests",
    "scripts": "scripts_system",
    "docs": "docs_notes",
}


def get_git_changed_files(staged_only: bool = False, compare_ref: Optional[str] = None) -> List[str]:
    """Retrieve changed, staged, and untracked files from git."""
    changed: Set[str] = set()

    try:
        if staged_only:
            res = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                cwd=str(HUB_ROOT),
                capture_output=True,
                text=True,
                check=True,
            )
            for line in res.stdout.splitlines():
                if line.strip():
                    changed.add(line.strip())
        elif compare_ref:
            res = subprocess.run(
                ["git", "diff", "--name-only", compare_ref],
                cwd=str(HUB_ROOT),
                capture_output=True,
                text=True,
                check=True,
            )
            for line in res.stdout.splitlines():
                if line.strip():
                    changed.add(line.strip())
        else:
            # Check working tree + index + untracked
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(HUB_ROOT),
                capture_output=True,
                text=True,
                check=True,
            )
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Format: XY PATH or XY PATH -> NEWPATH
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    path_str = parts[1]
                    if " -> " in path_str:
                        path_str = path_str.split(" -> ")[1]
                    changed.add(path_str.strip('"'))
    except Exception as exc:
        print(f"Warning: Failed to query git status: {exc}", file=sys.stderr)

    return sorted(list(changed))


def analyze_blast_radius(changed_files: List[str]) -> BlastRadiusReport:
    """Computes the affected surface and tests required for the given changes."""
    affected_domains_set: Set[str] = set()
    required_pytests: Set[str] = set()
    required_vitests: Set[str] = set()
    requires_frontend_typecheck = False
    requires_architecture_cycle_guard = False

    for path in changed_files:
        norm_path = path.replace("\\", "/")

        # Domain categorization
        matched_domain = False
        for prefix, domain in DOMAIN_MAP.items():
            if norm_path.startswith(prefix):
                affected_domains_set.add(domain)
                matched_domain = True
                break
        if not matched_domain:
            affected_domains_set.add("general_root")

        # Specific file blast rules
        if norm_path.startswith("apps/web"):
            requires_frontend_typecheck = True
            # Check if layer isolation might be impacted
            requires_architecture_cycle_guard = True
            required_pytests.add("tests/test_web_layer_isolation.py")

        if norm_path.startswith("visual_shell"):
            requires_architecture_cycle_guard = True
            required_pytests.add("tests/test_import_cycles.py")
            required_pytests.add("tests/test_web_layer_isolation.py")

            if "project-view" in norm_path or "ProjectView" in norm_path:
                required_pytests.add("tests/test_project_view_decomposition.py")
                required_vitests.add("tests/components/ProjectView.questionFormKey.test.ts")
                required_vitests.add("tests/components/buffered-text-pending.test.tsx")
                required_vitests.add("tests/components/ProjectView.touched-path-containment.test.ts")

            if "providers" in norm_path:
                required_pytests.add("tests/test_import_cycles.py")

            if "updater" in norm_path:
                required_pytests.add("tests/test_import_cycles.py")

        if norm_path.startswith("services/canvas") or "canvas" in norm_path:
            required_pytests.add("tests/canvas/test_canvas_ai_actions.py")

        if norm_path.startswith("services/shopify") or "shopify" in norm_path:
            required_pytests.add("tests/shopify/test_liquid_compiler.py")
            required_pytests.add("tests/shopify/test_shopify_vite_pipeline.py")

        if "swarm" in norm_path:
            required_pytests.add("tests/swarm/test_swarm_daemon.py")

        if norm_path.startswith("tests/"):
            if norm_path.endswith(".py"):
                required_pytests.add(norm_path)

    # Risk level determination
    affected_domains = sorted(list(affected_domains_set))
    domain_count = len(affected_domains)

    if any(d in affected_domains for d in ["core_orchestrator", "visual_shell", "backend_api"]) and domain_count >= 3:
        risk_level = "CRITICAL"
    elif domain_count >= 2:
        risk_level = "HIGH"
    elif domain_count == 1:
        risk_level = "MEDIUM" if affected_domains[0] not in ["docs_notes", "general_root"] else "LOW"
    else:
        risk_level = "LOW"

    # Always ensure baseline regression pytests if critical/high risk
    if risk_level in ["CRITICAL", "HIGH"]:
        required_pytests.add("tests/test_web_layer_isolation.py")
        required_pytests.add("tests/test_import_cycles.py")
        required_pytests.add("tests/test_project_view_decomposition.py")

    summary = (
        f"Blast Radius: {len(changed_files)} changed files across {len(affected_domains)} domains "
        f"({', '.join(affected_domains) if affected_domains else 'none'}). Risk level: {risk_level}."
    )

    return BlastRadiusReport(
        changed_files=changed_files,
        affected_domains=affected_domains,
        risk_level=risk_level,
        required_pytests=sorted(list(required_pytests)),
        required_vitests=sorted(list(required_vitests)),
        requires_frontend_typecheck=requires_frontend_typecheck,
        requires_architecture_cycle_guard=requires_architecture_cycle_guard,
        summary=summary,
    )


class BlastRadiusAnalyzer:
    """Convenience wrapper for analyzing repository blast radius."""
    def __init__(self, changed_files: Optional[List[str]] = None, staged_only: bool = False, compare_ref: Optional[str] = None):
        if changed_files is None:
            self.changed_files = get_git_changed_files(staged_only=staged_only, compare_ref=compare_ref)
        else:
            self.changed_files = changed_files

    def analyze(self) -> Dict[str, Any]:
        report = analyze_blast_radius(self.changed_files)
        return asdict(report)


def main():
    parser = argparse.ArgumentParser(description="DNK OS Blast Radius & Affected Surface Analyzer")
    parser.add_argument("--staged", action="store_true", help="Analyze staged files only")
    parser.add_argument("--compare", type=str, default=None, help="Compare against git ref (e.g. main, HEAD~1)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("files", nargs="*", help="Optional specific list of files to analyze")

    args = parser.parse_args()

    if args.files:
        files = args.files
    else:
        files = get_git_changed_files(staged_only=args.staged, compare_ref=args.compare)

    report = analyze_blast_radius(files)

    if args.json:
        print(json.dumps(asdict(report), indent=2))
        return

    print("========================================================")
    print("🎯 DNK OS BLAST RADIUS & AFFECTED SURFACE REPORT")
    print("========================================================")
    print(f"Status: {report.summary}")
    print(f"Risk Level: {report.risk_level}")
    print("\nAffected Domains:")
    for d in report.affected_domains:
        print(f"  • {d}")

    print(f"\nChanged Files ({len(report.changed_files)}):")
    for f in report.changed_files[:15]:
        print(f"  - {f}")
    if len(report.changed_files) > 15:
        print(f"  ... and {len(report.changed_files) - 15} more files")

    print("\nRequired Verification Steps:")
    if report.requires_architecture_cycle_guard:
        print("  🔒 Architecture & Cycle Guard: REQUIRED")
    if report.requires_frontend_typecheck:
        print("  💎 Frontend Typecheck (npm run type-check): REQUIRED")
    if report.required_pytests:
        print("  🐍 Targeted Pytest Targets:")
        for t in report.required_pytests:
            print(f"     - {t}")
    if report.required_vitests:
        print("  ⚡ Targeted Vitest Targets:")
        for v in report.required_vitests:
            print(f"     - {v}")
    print("========================================================")


if __name__ == "__main__":
    main()
