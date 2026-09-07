#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/architecture_and_cycle_guard.py"
# purpose: "Autonomous Architecture Isolation, Cycle Defense, and Modularity Guard for DNK OS"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

HUB_ROOT = Path(__file__).resolve().parent.parent.parent


def check_layer_isolation() -> Tuple[bool, List[str]]:
    """Verify that apps/web has zero direct imports from visual_shell."""
    errors = []
    web_dir = HUB_ROOT / "apps" / "web"
    if not web_dir.exists():
        return True, []

    leak_pattern = re.compile(
        r"""(?:import|export)\s+.*?from\s+['"][^'"]*visual_shell[^'"]*['"]|require\(['"][^'"]*visual_shell[^'"]*['"]\)"""
    )

    for path in web_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in [".ts", ".tsx", ".js", ".jsx"]:
            continue
        if "node_modules" in path.parts or ".next" in path.parts:
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        for line_no, line in enumerate(content.splitlines(), start=1):
            if leak_pattern.search(line):
                rel_path = path.relative_to(HUB_ROOT)
                errors.append(f"Layer Isolation Leak in {rel_path}:{line_no} -> {line.strip()}")

    return len(errors) == 0, errors


def find_import_cycles_in_dir(directory: Path, allowed_extensions: Tuple[str, ...] = (".ts", ".tsx", ".js", ".jsx")) -> List[List[str]]:
    """Builds a local directed dependency graph and detects cycles via DFS."""
    if not directory.exists() or not directory.is_dir():
        return []

    # Map file stem/name to actual file path
    files: Dict[str, Path] = {}
    for f in directory.iterdir():
        if f.is_file() and f.suffix in allowed_extensions:
            files[f.stem] = f
            files[f.name] = f

    graph: Dict[str, Set[str]] = defaultdict(set)
    import_regex = re.compile(r"""(?:import|export)\s+(?:.*?from\s+)?['"]\./([^'"]+)['"]""")

    for stem, path in files.items():
        if stem != path.stem:
            continue  # avoid duplicate entries
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        for line in content.splitlines():
            matches = import_regex.findall(line)
            for target in matches:
                # remove possible extension in import, e.g. ./types.js -> types
                clean_target = target.replace(".js", "").replace(".ts", "").replace(".jsx", "").replace(".tsx", "")
                if clean_target in files:
                    graph[stem].add(clean_target)

    # Detect cycles via DFS with path tracking
    cycles = []
    visited: Set[str] = set()
    rec_stack: List[str] = []

    def dfs(node: str):
        visited.add(node)
        rec_stack.append(node)

        for neighbor in sorted(list(graph.get(node, set()))):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                # Cycle found!
                cycle_start_idx = rec_stack.index(neighbor)
                cycle_path = rec_stack[cycle_start_idx:] + [neighbor]
                cycles.append(cycle_path)

        rec_stack.pop()

    for node in sorted(list(graph.keys())):
        if node not in visited:
            dfs(node)

    return cycles


def check_provider_import_cycles() -> Tuple[bool, List[str]]:
    """Verify visual_shell web providers are free of circular dependency cycles."""
    providers_dir = (
        HUB_ROOT
        / "visual_shell"
        / "open_design"
        / "apps"
        / "web"
        / "src"
        / "providers"
    )
    if not providers_dir.exists():
        return True, []

    types_file = providers_dir / "types.ts"
    errors = []
    if not types_file.is_file():
        errors.append("providers/types.ts is missing! Cycle mitigation SSOT missing.")

    cycles = find_import_cycles_in_dir(providers_dir)
    for c in cycles:
        cycle_str = " -> ".join(c)
        errors.append(f"Circular dependency cycle: {cycle_str}")

    return len(errors) == 0, errors


def check_updater_import_cycles() -> Tuple[bool, List[str]]:
    """Verify desktop updater subsystem is free of circular dependencies."""
    updater_dir = (
        HUB_ROOT
        / "visual_shell"
        / "open_design"
        / "apps"
        / "desktop"
        / "src"
        / "main"
        / "updater"
    )
    if not updater_dir.exists():
        return True, []

    types_file = updater_dir / "types.ts"
    errors = []
    if not types_file.is_file():
        errors.append("updater/types.ts is missing! Cycle mitigation SSOT missing.")

    cycles = find_import_cycles_in_dir(updater_dir)
    for c in cycles:
        cycle_str = " -> ".join(c)
        errors.append(f"Circular dependency cycle in updater: {cycle_str}")

    # Also verify updater.ts doesn't create cycles with its children
    payload_file = updater_dir / "payload.ts"
    if payload_file.is_file():
        content = payload_file.read_text(encoding="utf-8")
        if 'from "../updater.js"' in content or "from '../updater'" in content:
            errors.append("payload.ts imports parent updater.ts! Circular reference.")

    scheduler_file = updater_dir / "scheduler.ts"
    if scheduler_file.is_file():
        content = scheduler_file.read_text(encoding="utf-8")
        if 'from "../updater.js"' in content or "from '../updater'" in content:
            errors.append("scheduler.ts imports parent updater.ts! Circular reference.")

    return len(errors) == 0, errors


def check_project_view_modularity() -> Tuple[bool, List[str]]:
    """Verify that consumers import from project-view modular package rather than God Component."""
    errors = []
    components_dir = (
        HUB_ROOT
        / "visual_shell"
        / "open_design"
        / "apps"
        / "web"
        / "src"
        / "components"
    )
    use_chat = components_dir / "workspace" / "useConversationChat.ts"
    if use_chat.is_file():
        content = use_chat.read_text(encoding="utf-8")
        if "from '../ProjectView'" in content:
            errors.append(
                "useConversationChat.ts coupled directly to God Component ProjectView instead of ../project-view!"
            )

    return len(errors) == 0, errors


def run_all_checks() -> bool:
    print("========================================================")
    print("🛡️  DNK OS ARCHITECTURE & IMPORT CYCLES GUARD")
    print("========================================================")

    all_passed = True
    all_errors: List[str] = []

    # 1. Layer Isolation
    iso_ok, iso_errs = check_layer_isolation()
    if iso_ok:
        print("✅ [Layer Isolation] apps/web -> visual_shell: 0 leaks.")
    else:
        print(f"❌ [Layer Isolation] {len(iso_errs)} violations detected:")
        for err in iso_errs:
            print(f"   • {err}")
        all_passed = False
        all_errors.extend(iso_errs)

    # 2. Provider Cycles
    prov_ok, prov_errs = check_provider_import_cycles()
    if prov_ok:
        print("✅ [Import Cycles] visual_shell web providers: Cycle-free (0 cycles detected).")
    else:
        print(f"❌ [Import Cycles] Provider cycle violations detected:")
        for err in prov_errs:
            print(f"   • {err}")
        all_passed = False
        all_errors.extend(prov_errs)

    # 3. Desktop Updater Cycles
    upd_ok, upd_errs = check_updater_import_cycles()
    if upd_ok:
        print("✅ [Import Cycles] visual_shell desktop updater: Cycle-free (0 cycles detected).")
    else:
        print(f"❌ [Import Cycles] Updater cycle violations detected:")
        for err in upd_errs:
            print(f"   • {err}")
        all_passed = False
        all_errors.extend(upd_errs)

    # 4. ProjectView Modularity
    pv_ok, pv_errs = check_project_view_modularity()
    if pv_ok:
        print("✅ [Modularity] ProjectView God Component decoupled into project-view/ package.")
    else:
        print(f"❌ [Modularity] ProjectView decoupling violations detected:")
        for err in pv_errs:
            print(f"   • {err}")
        all_passed = False
        all_errors.extend(pv_errs)

    print("========================================================")
    if all_passed:
        print("🎉 ALL ARCHITECTURAL INVARIANTS & CYCLE CHECKS PASSED ✅")
        return True
    else:
        print(f"❌ ARCHITECTURAL DEFECTS DETECTED ({len(all_errors)} issues).")
        return False


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
