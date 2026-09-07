#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_zero_waste_runner"
# purpose: "Canonical Zero-Waste Mentor Orchestrator: Decomposes goals into atomic slices and coordinates Gerych execution with 100% fidelity."
# canonical_source: true
# alters_files: [".dnk_active_slices.json"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import os
import sys

# Auto-reexec in .venv if running with system python
_hub_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_venv_py = os.path.join(_hub_root, ".venv", "bin", "python3")
if os.path.exists(_venv_py) and sys.executable != _venv_py:
    os.execv(_venv_py, [_venv_py] + sys.argv)

import json
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List

HUB_ROOT = Path(_hub_root)
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

from core.orchestrator.zero_waste_slicer import ZeroWasteSlicer, TaskSlice


def print_banner(text: str, color: str = "\033[92m"):
    reset = "\033[0m"
    print(f"\n{color}{'=' * 75}\n{text}\n{'=' * 75}{reset}")


def run_command(cmd: str, cwd: Path) -> tuple[int, str]:
    """Runs a shell command and streams/returns stdout+stderr."""
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=dict(os.environ, PYTHONPATH=f"{HUB_ROOT}:{HUB_ROOT}/services")
    )
    output_lines = []
    if proc.stdout:
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            output_lines.append(line)
    proc.wait()
    return proc.returncode, "".join(output_lines)


def display_plan(slices: List[TaskSlice]):
    print_banner("🧬 DNK OS ZERO-WASTE ATOMIC EXECUTION DAG", "\033[96m")
    status_icons = {
        "completed": "✅",
        "in_progress": "⏳",
        "awaiting_verification": "🧪",
        "pending": "⏸️ ",
        "failed": "❌",
        "blocked": "🛑",
        "budget_exceeded": "⚠️ "
    }

    print(f"{'#':<4} {'Status':<6} {'ID':<14} {'Title':<35} {'Target Files'}")
    print("-" * 75)
    for s in slices:
        icon = status_icons.get(s.status, "❓")
        files_preview = ", ".join(s.target_files[:2]) or "general"
        if len(s.target_files) > 2:
            files_preview += f" (+{len(s.target_files)-2})"
        print(f"{s.index:<4} {icon:<6} {s.id:<14} {s.title[:33]:<35} {files_preview}")
    print("-" * 75)


def execute_slice(slicer: ZeroWasteSlicer, slice_item: TaskSlice, total_count: int) -> bool:
    print_banner(f"🚀 EXECUTING ATOMIC SLICE [{slice_item.index}/{total_count}]: {slice_item.title}", "\033[93m")

    # 1. Update status to in_progress
    slicer.update_slice_status(slice_item.id, "in_progress")

    # 2. Generate focused prompt
    prompt = slicer.generate_slice_prompt(slice_item, total_count)
    prompt_file = Path(f"/tmp/dnk_slice_{slice_item.id}.prompt")
    with open(prompt_file, "w", encoding="utf-8") as pf:
        pf.write(prompt)

    # 3. Invoke Gerych in atomic mode
    budget = slice_item.budget.max_tool_calls
    gerych_cmd = f"DNK_ATOMIC_SLICE=1 HERMES_MAX_ITERATIONS=35 bash scripts/system/gerych.sh -z \"$(cat '{prompt_file}')\""
    print(f"📡 Dispatching to Gerych (budget: {budget} tools)...")
    exit_code, output = run_command(gerych_cmd, HUB_ROOT)

    # Check for explicit BLOCKED report from agent
    if "status: BLOCKED" in output or "status: 'BLOCKED'" in output or 'status: "BLOCKED"' in output:
        slicer.update_slice_status(
            slice_item.id,
            "blocked",
            summary="Execution blocked by agent due to architectural conflict or missing precondition."
        )
        print_banner(f"🛑 SLICE {slice_item.id} REPORTED BLOCKED!", "\033[91m")
        return False

    # Check for budget exhaustion
    if "Iteration budget exhausted" in output or "status: BUDGET_EXCEEDED" in output:
        slicer.update_slice_status(
            slice_item.id,
            "budget_exceeded",
            summary=f"Exhausted tool call budget ({budget} tools)."
        )
        print_banner(f"⚠️ SLICE {slice_item.id} BUDGET EXCEEDED!", "\033[91m")
        return False

    # 4. Run automated verification for this slice
    slicer.update_slice_status(slice_item.id, "awaiting_verification")
    verif_cmd = slice_item.verification_cmd or "bash scripts/verify_all.sh"
    print(f"\n🔍 Running slice quality gate: `{verif_cmd}`...")
    v_code, v_out = run_command(verif_cmd, HUB_ROOT)

    if v_code == 0:
        slicer.update_slice_status(
            slice_item.id,
            "completed",
            summary=f"Successfully verified with `{verif_cmd}`"
        )
        print_banner(f"✅ SLICE {slice_item.id} COMPLETED & 100% VERIFIED!", "\033[92m")
        return True
    else:
        slicer.update_slice_status(
            slice_item.id,
            "failed",
            summary=f"Verification failed on `{verif_cmd}`"
        )
        print_banner(f"❌ SLICE {slice_item.id} VERIFICATION FAILED!", "\033[91m")
        print("💡 Hint: Query `dnk_query_error_solutions` to resolve error before re-running.")
        return False


def main():
    parser = argparse.ArgumentParser(description="DNK OS Zero-Waste Mentor Task Runner")
    parser.add_argument("--goal", "-g", type=str, help="High-level goal or markdown specification to decompose")
    parser.add_argument("--file", "-f", type=str, help="Markdown file containing goal or specification")
    parser.add_argument("--status", "-s", action="store_true", help="Show current plan status")
    parser.add_argument("--step", action="store_true", help="Execute only the next pending atomic slice")
    parser.add_argument("--auto", "-a", action="store_true", help="Execute all pending slices sequentially")
    parser.add_argument("--reset", action="store_true", help="Clear active slice plan")

    args = parser.parse_args()
    slicer = ZeroWasteSlicer(workspace_root=HUB_ROOT)

    if args.reset:
        plan_file = HUB_ROOT / ZeroWasteSlicer.DEFAULT_PLAN_FILE
        if plan_file.exists():
            plan_file.unlink()
        print("🧹 Active slice plan cleared.")
        return

    # Handle decomposition
    goal_text = ""
    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as fp:
            goal_text = fp.read()
    elif args.goal:
        goal_text = args.goal

    if goal_text:
        slices = slicer.decompose(goal_text)
        slicer.save_plan(slices)
        display_plan(slices)
        if not args.auto and not args.step:
            print("\n💡 Plan saved to `.dnk_active_slices.json`. Run with `--step` or `--auto`.")
            return

    # Load existing plan if not just created
    if not goal_text:
        slices = slicer.load_plan()
        if not slices:
            print("ℹ️ No active slice plan found. Provide `--goal '<text>'` or `--file <path>` to decompose a new task.")
            return


    if args.status:
        display_plan(slices)
        return

    if args.step:
        next_slice = slicer.get_next_pending_slice()
        if not next_slice:
            print("🎉 All slices in the active plan are completed!")
            display_plan(slices)
            return
        execute_slice(slicer, next_slice, len(slices))
        return

    if args.auto:
        print(f"⚡ Starting autonomous execution of {len(slices)} slices...")
        while True:
            next_slice = slicer.get_next_pending_slice()
            if not next_slice:
                print_banner("🎉 ALL ZERO-WASTE ATOMIC SLICES COMPLETED & 100% VERIFIED!", "\033[92m")
                display_plan(slicer.load_plan())
                break

            success = execute_slice(slicer, next_slice, len(slices))
            if not success:
                print(f"⛔ Stopping auto-runner due to failure on slice {next_slice.id}.")
                sys.exit(1)
        return

    # Default: display plan
    display_plan(slices)


if __name__ == "__main__":
    main()
