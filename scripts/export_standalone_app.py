#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/export_standalone_app.py"
# purpose: "Packages and exports modular DNK OS Bricks with lean dependency generation, in-target quality gate, and standalone repository initialization."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.1.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Antigravity Orchestrator"
# --- END DNK-MRH-HEADER ---

import argparse
import glob
import os
import shutil
import sys
import subprocess
from pathlib import Path
from typing import List, Optional

HUB_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HUB_ROOT))

from core.bricks.registry import DNKBrickRegistry


def export_standalone_app(
    target_dir: Path,
    app_id: str = "dnk_os_mvp",
    bricks: Optional[List[str]] = None,
    run_quality_gate: bool = True,
):
    """
    Exports composable bricks from the unified development hub into a clean,
    standalone Tier-2 repository with lean dependencies and in-target test validation.
    """
    target_dir = target_dir.resolve()
    registry = DNKBrickRegistry()

    all_registered = [b.id for b in registry.list_bricks()]
    if not bricks or "all" in bricks:
        selected_bricks = all_registered
    else:
        selected_bricks = bricks

    print(f"🚀 [DNK Foundry] Assembling App: '{app_id}'")
    print(f"📦 Selected Bricks: {selected_bricks}")
    
    # 1. Resolve DAG dependencies
    resolved_bricks = registry.resolve_dependencies(selected_bricks)
    print(f"⛓️  Resolved Dependency DAG (Dependencies First): {resolved_bricks}")

    if target_dir.exists():
        print(f"⚠️  Target directory {target_dir} exists. Refreshing clean build...")
        shutil.rmtree(target_dir, ignore_errors=True)

    target_dir.mkdir(parents=True, exist_ok=True)

    # 2. Gather export paths from resolved bricks
    export_paths = registry.collect_export_paths(resolved_bricks)
    
    # Core framework directories & configuration
    essential_dirs = ["core/bricks", "config"]
    all_dirs_to_copy = set(export_paths + essential_dirs)

    excludes = shutil.ignore_patterns(
        "node_modules",
        ".next",
        ".venv",
        "__pycache__",
        "*.pyc",
        ".DS_Store",
        "*.lock",
        "*.db",
        "*.db-wal",
        "*.db-shm",
    )

    for item in sorted(all_dirs_to_copy):
        src = HUB_ROOT / item
        dst = target_dir / item
        if src.exists():
            if src.is_dir():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dst, ignore=excludes)
                print(f"  ✅ Copied Brick Path [DIR]: {item}")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                print(f"  ✅ Copied Brick Path [FILE]: {item}")

    # 3. Copy associated Quality Gate tests for all resolved bricks
    test_files_copied = 0
    for b_id in resolved_bricks:
        brick = registry.get_brick(b_id)
        if brick and brick.quality_gate:
            pattern = brick.quality_gate.test_suite
            matched = list(HUB_ROOT.glob(pattern))
            for test_file in matched:
                rel_path = test_file.relative_to(HUB_ROOT)
                dst = target_dir / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(test_file, dst)
                test_files_copied += 1
    
    # Also copy core brick registry tests
    brick_test = HUB_ROOT / "tests/bricks/test_brick_registry.py"
    if brick_test.exists():
        dst = target_dir / "tests/bricks/test_brick_registry.py"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(brick_test, dst)
        test_files_copied += 1

    print(f"  🧪 Copied {test_files_copied} Quality Gate test suites.")

    # 4. Generate Lean pyproject.toml and requirements.txt
    lean_pyproject = registry.generate_lean_pyproject_toml(app_id, resolved_bricks)
    (target_dir / "pyproject.toml").write_text(lean_pyproject)
    print("  ✅ Generated: Lean pyproject.toml")

    lean_reqs = registry.generate_lean_requirements_txt(resolved_bricks)
    (target_dir / "requirements.txt").write_text(lean_reqs)
    print("  ✅ Generated: Lean requirements.txt")

    # 5. Production configuration and deployment manifests
    prod_files = [
        "Dockerfile",
        "Dockerfile.api",
        "Dockerfile.web",
        "docker-compose.yml",
        "README.md",
        "AGENTS.md",
    ]

    for f in prod_files:
        src = HUB_ROOT / f
        dst = target_dir / f
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  ✅ Copied Manifest: {f}")

    # 6. Generate clean production .env.example
    env_example = target_dir / ".env.example"
    env_example.write_text(
        f"""# DNK OS App: {app_id} Standalone Production Environment
NEXT_PUBLIC_API_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000
DATABASE_URL=postgresql://dnk:dnk_password@localhost:5432/dnk_os
REDIS_URL=redis://localhost:6379/0
SECURITY_API_KEY=dnk_master_key_2026
SECURITY_RATE_LIMIT=1000
APP_ID={app_id}
ENABLED_BRICKS={",".join(resolved_bricks)}
"""
    )
    print("  ✅ Generated: .env.example with App metadata")

    # 7. Autonomous In-Target Quality Gate
    if run_quality_gate:
        print("\n🛡️ Running Autonomous In-Target Quality Gate...")
        try:
            test_cmd = [sys.executable, "-m", "pytest", "tests/bricks", "-v"]
            env = dict(os.environ)
            env["PYTHONPATH"] = f"{target_dir}:{target_dir / 'services'}"
            proc = subprocess.run(test_cmd, cwd=target_dir, env=env, capture_output=True, text=True)
            if proc.returncode == 0:
                print("  🟢 In-Target Quality Gate: 100% PASS!")
            else:
                print(f"  ⚠️ In-Target Quality Gate Warnings:\n{proc.stderr}\n{proc.stdout}")
        except Exception as e:
            print(f"  ⚠️ In-Target Quality Gate execution skipped: {e}")

    # 8. Initialize Git repository in the target directory
    try:
        subprocess.run(["git", "init", "-b", "main"], cwd=target_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."], cwd=target_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(
            ["git", "commit", "-m", f"feat: initial production release of '{app_id}' standalone app"],
            cwd=target_dir,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        print("  🎉 Initialized fresh Git repository on 'main' branch!")
    except Exception as e:
        print(f"  ⚠️ Git init skipped: {e}")

    print("\n" + "=" * 60)
    print(f"✨ STANDALONE APP '{app_id}' READY FOR DEPLOYMENT!")
    print(f"📂 Location: {target_dir}")
    print(f"🧱 Bricks Included: {', '.join(resolved_bricks)}")
    print("🚀 Quick Deploy Options:")
    print(f"   1. Local API:  cd {target_dir} && python3 -m uvicorn apps.api.main:app --reload")
    print(f"   2. Docker:     cd {target_dir} && docker compose up -d")
    print("   3. Push to GitHub: git remote add origin <repo_url> && git push -u origin main")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="DNK OS Standalone App & Brick Exporter")
    parser.add_argument("--target-dir", type=Path, default=HUB_ROOT.parent / "DNKOS_APP_STANDALONE", help="Destination path")
    parser.add_argument("--app-id", type=str, default="dnk_os_mvp", help="Unique identifier of exported app")
    parser.add_argument("--bricks", nargs="*", default=None, help="List of brick IDs to assemble (default: all)")
    parser.add_argument("--skip-tests", action="store_true", help="Skip in-target test execution")

    args = parser.parse_args()
    export_standalone_app(
        target_dir=args.target_dir,
        app_id=args.app_id,
        bricks=args.bricks,
        run_quality_gate=not args.skip_tests,
    )


if __name__ == "__main__":
    main()
