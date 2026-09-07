# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_process_guard"
# purpose: "Process Hygiene Watchdog: reaps zombie/orphaned processes, audits open ports, and provides singleton lock management for Gerych agents."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

import argparse
import fcntl
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

LOCK_DIR = Path("/tmp/dnk_agent_locks")


def ensure_lock_dir():
    LOCK_DIR.mkdir(parents=True, exist_ok=True)


def get_lock_file(agent_name: str) -> Path:
    ensure_lock_dir()
    clean_name = "".join(c for c in agent_name if c.isalnum() or c in ("-", "_"))
    return LOCK_DIR / f"{clean_name}.pid"


def check_and_acquire_lock(agent_name: str, force: bool = False) -> bool:
    """Acquire single-instance execution lock for the given agent."""
    lock_file = get_lock_file(agent_name)
    current_pid = os.getpid()

    if lock_file.exists():
        try:
            stored_pid = int(lock_file.read_text().strip())
            if stored_pid != current_pid:
                # Check if process is still alive
                try:
                    os.kill(stored_pid, 0)
                    # Process is alive!
                    if force:
                        print(f"⚠️  Terminating existing active instance of {agent_name} (PID {stored_pid})...")
                        try:
                            os.kill(stored_pid, signal.SIGTERM)
                            time.sleep(0.5)
                        except Exception:
                            pass
                    else:
                        print(f"⚠️  [Process Guard] Instance of agent '{agent_name}' is already running with PID {stored_pid}.")
                        print("   To connect or restart, use '--force' or terminate the previous session.")
                        return False
                except OSError:
                    # Stale PID file, process no longer exists
                    pass
        except Exception:
            pass

    try:
        lock_file.write_text(str(current_pid))
        return True
    except Exception as e:
        print(f"⚠️  Could not write lockfile {lock_file}: {e}")
        return True


def release_lock(agent_name: str):
    """Release single-instance execution lock."""
    lock_file = get_lock_file(agent_name)
    try:
        if lock_file.exists():
            stored_pid = int(lock_file.read_text().strip())
            if stored_pid == os.getpid():
                lock_file.unlink(missing_ok=True)
    except Exception:
        pass


def audit_and_reap_processes():
    print("========================================================")
    print("🧹 DNK OS Process Hygiene & Resource Watchdog")
    print("========================================================")

    current_pid = os.getpid()
    reaped = 0

    try:
        # Check for hanging bash swarm or defunct python scripts older than 30m
        ps_output = subprocess.check_output(["ps", "-eo", "pid,etime,command"], text=True)
        lines = ps_output.strip().splitlines()

        for line in lines[1:]:
            parts = line.strip().split(maxsplit=2)
            if len(parts) < 3:
                continue
            pid_str, etime, cmd = parts[0], parts[1], parts[2]
            try:
                pid = int(pid_str)
            except ValueError:
                continue

            if pid == current_pid or pid == os.getppid():
                continue

            # Identify stale swarm or defunct test runner processes
            is_stale_target = (
                ("gerych_swarm.sh" in cmd or "auto_precommit_guard" in cmd)
                and ("-" in etime or ":" in etime and int(etime.split(":")[-2]) >= 20)
            )

            if is_stale_target:
                print(f"⚠️  Reaping stale process PID {pid} ({etime}): {cmd[:60]}...")
                try:
                    os.kill(pid, signal.SIGTERM)
                    reaped += 1
                except ProcessLookupError:
                    pass
                except PermissionError:
                    pass

    except Exception as e:
        print(f"⚠️  Process inspection notice: {e}")

    print(f"✅ Process Hygiene Audit Complete: {reaped} stale processes reaped.")
    print("========================================================")
    return 0


def main():
    parser = argparse.ArgumentParser(description="DNK OS Process Guard & Lock Manager")
    parser.add_argument("--audit", action="store_true", help="Audit and reap stale processes")
    parser.add_argument("--check-lock", type=str, help="Check and acquire lock for agent name")
    parser.add_argument("--release-lock", type=str, help="Release lock for agent name")
    parser.add_argument("--force", action="store_true", help="Force terminate existing instance if locked")

    args = parser.parse_args()

    if args.check_lock:
        success = check_and_acquire_lock(args.check_lock, force=args.force)
        sys.exit(0 if success else 1)
    elif args.release_lock:
        release_lock(args.release_lock)
        sys.exit(0)
    else:
        sys.exit(audit_and_reap_processes())


if __name__ == "__main__":
    main()
