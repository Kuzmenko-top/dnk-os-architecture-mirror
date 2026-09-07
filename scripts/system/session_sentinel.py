#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/session_sentinel.py"
# purpose: "CLI & Parallel Daemon Launcher for Session Sentinel (Shadow Observer & Self-Healing Loop)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import os
import sys
import time
import signal
import argparse
from typing import Optional
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
venv_python = HUB_ROOT / ".venv" / "bin" / "python3"
if venv_python.exists() and sys.executable != str(venv_python):
    os.execv(str(venv_python), [str(venv_python)] + sys.argv)

sys.path.insert(0, str(HUB_ROOT))
sys.path.insert(0, str(HUB_ROOT / "services"))

from core.orchestrator.session_sentinel import SessionSentinel



def is_pid_alive(pid: int) -> bool:
    """Checks if a process ID is currently running on the system."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def run_watch_daemon(
    sentinel: SessionSentinel,
    target_pid: Optional[int],
    poll_interval: float = 2.0,
    stderr_file: Optional[Path] = None,
    auto_dispatch: bool = False,
    max_recursion_depth: int = 2
):
    """
    Runs sentinel in background, tracking the running process.
    When the process terminates, executes post-task distillation and generates self-healing tasks.
    """
    print(f"👁️  Session Sentinel engaged. Monitoring agent [{sentinel.agent_name}]" + (f" on PID {target_pid}..." if target_pid else "..."))

    stop_requested = False

    def handle_signal(sig, frame):
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    if hasattr(signal, "SIGUSR1"):
        signal.signal(signal.SIGUSR1, handle_signal)

    last_msg_id = 0
    poll_counter = 0

    while not stop_requested:
        if target_pid and not is_pid_alive(target_pid):
            print(f"🏁 Watched process {target_pid} terminated. Triggering post-session audit...")
            break

        # Periodic In-Flight Trajectory Check (Soup Watchdog pattern)
        poll_counter += 1
        if poll_counter % 3 == 0:
            try:
                new_msg_id, alerts = sentinel.poll_in_flight(last_seen_msg_id=last_msg_id)
                last_msg_id = new_msg_id
                if alerts:
                    print(f"⚠️  [In-Flight Alert] Detected {len(alerts)} anomalies during active execution!")
                    for a in alerts:
                        print(f"   • [{a.category.value}] {a.title}")
            except Exception:
                pass

        time.sleep(poll_interval)

    # Gather stderr logs if available
    stderr_text = None
    if stderr_file and stderr_file.exists():
        try:
            stderr_text = stderr_file.read_text(encoding="utf-8")
        except Exception:
            pass

    # Run post-task pipeline
    res = sentinel.run_post_task_pipeline(
        stderr_logs=stderr_text,
        auto_dispatch=auto_dispatch,
        max_recursion_depth=max_recursion_depth
    )
    if res:
        print("\n========================================================")
        print(f"🛡️  SESSION SENTINEL: POST-TASK AUDIT COMPLETE")
        print("========================================================")
        print(f"🆔 Session: {res.session_id} | Task: {res.task_id or 'N/A'}")
        print(f"⏱️  Duration: {res.duration_sec}s | Tools: {res.total_tool_calls} calls")
        print(f"📈 Efficiency Score: {res.efficiency_pct}%")
        print(f"⚠️  Anomalies Detected: {len(res.anomalies)}")
        for a in res.anomalies:
            print(f"   • [{a.severity.value}] {a.title}")
        if res.self_heal_task_path:
            print(f"🏥 Self-Healing Task Generated: {res.self_heal_task_path}")
        if res.canvas_node_id:
            print(f"🧬 DAG Canvas Node Created: {res.canvas_node_id} (Assigned: dnk_dev_fullstack)")
        if res.dispatched_agent:
            print(f"🚀 Auto-Dispatched to Swarm: {res.dispatched_agent} (Status: {res.dispatch_status})")
        print("========================================================\n")
    else:
        print("ℹ️  No session data recorded to audit.")


def main():
    parser = argparse.ArgumentParser(description="DNK OS Session Sentinel (Shadow Observer & Self-Healing Loop)")
    parser.add_argument("--watch", action="store_true", help="Run as background sentinel daemon watching PID")
    parser.add_argument("--pid", type=int, help="Target process PID to watch")
    parser.add_argument("--agent", "-a", type=str, default="gerych_prime", help="Agent name (default: gerych_prime)")
    parser.add_argument("--session", "-s", type=str, help="Specific session ID to audit")
    parser.add_argument("--audit-latest", action="store_true", help="Audit the most recent session from state.db")
    parser.add_argument("--reconcile-orphaned", action="store_true", help="Reconcile orphaned unclosed sessions whose host process has died")
    parser.add_argument("--stderr-file", type=str, help="Path to stderr log file to inspect")
    parser.add_argument("--dry-run", action="store_true", help="Analyze and print results without persisting tasks/canvas")
    parser.add_argument("--auto-dispatch", action="store_true", help="Automatically dispatch self-healing task to swarm worker (dnk_dev_fullstack)")
    parser.add_argument("--max-recursion-depth", type=int, default=2, help="Maximum recursion depth for autonomous self-healing chain (default: 2)")

    args = parser.parse_args()
    sentinel = SessionSentinel(agent_name=args.agent, hub_root=HUB_ROOT)

    auto_dispatch = args.auto_dispatch or os.environ.get("DNK_SENTINEL_AUTO_DISPATCH", "").lower() in ("1", "true", "yes")
    max_recursion_depth = args.max_recursion_depth

    stderr_path = Path(args.stderr_file) if args.stderr_file else None

    if args.watch:
        run_watch_daemon(
            sentinel,
            target_pid=args.pid,
            stderr_file=stderr_path,
            auto_dispatch=auto_dispatch,
            max_recursion_depth=max_recursion_depth
        )
    elif args.reconcile_orphaned:
        reconciled = sentinel.reconcile_orphaned_sessions()
        print(f"🔄 Reconciled {len(reconciled)} orphaned sessions.")
        for r in reconciled:
            print(f"   • Session {r.session_id}: {len(r.anomalies)} anomalies, efficiency {r.efficiency_pct:.1f}%")
        return
    elif args.audit_latest or args.session:
        session_data = sentinel.fetch_session_data(args.session)
        if not session_data:
            print(f"ℹ️ No matching session found in {sentinel.get_agent_db()}.")
            return

        stderr_text = stderr_path.read_text(encoding="utf-8") if (stderr_path and stderr_path.exists()) else None

        if args.dry_run:
            res = sentinel.analyze_trajectory(session_data, stderr_text)
            print(f"🔍 [Dry-Run] Session: {res.session_id}")
            print(f"⚠️  Anomalies: {len(res.anomalies)}")
            for a in res.anomalies:
                print(f"   • [{a.category.value}] {a.title}")
        else:
            res = sentinel.run_post_task_pipeline(
                session_id=args.session,
                stderr_logs=stderr_text,
                auto_dispatch=auto_dispatch,
                max_recursion_depth=max_recursion_depth
            )
            if res:
                print(f"✅ Audit complete for session {res.session_id}. Efficiency: {res.efficiency_pct}%")
                if res.self_heal_task_path:
                    print(f"🏥 Self-Healing Task Created: {res.self_heal_task_path}")
                if res.canvas_node_id:
                    print(f"🧬 Canvas Node Created: {res.canvas_node_id}")
                if res.dispatched_agent:
                    print(f"🚀 Auto-Dispatched to Swarm: {res.dispatched_agent} (Status: {res.dispatch_status})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
