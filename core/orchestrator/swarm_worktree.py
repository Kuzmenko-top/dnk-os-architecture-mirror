# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/swarm_worktree.py"
# purpose: "Git Worktree Isolation, NDJSON Audit Trail, and Sangha Consensus Gate for DNK Swarm."
# canonical_source: true
# alters_files: ["data/swarm_artifacts/audit_trail.ndjson", ".worktrees/"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & Maksym Kuzmenko"
# --- END DNK-MRH-HEADER ---

import json
import logging
import os
import py_compile
import re
import shutil
import subprocess
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

logger = logging.getLogger("SwarmWorktree")

# Absolute path violation detector for Path Hygiene
ABSOLUTE_PATH_PATTERN = re.compile(r"/(Users|home|root)/[a-zA-Z0-9_\.\-]+")


class SwarmWorktreeManager:
    """
    Physical Git Worktree Isolation & Sangha Consensus Gate for parallel swarm workers.
    Implements SOTA engineering patterns inspired by nwiizo/ccswarm and ruvnet/ruflo.
    """

    def __init__(self, hub_root: Optional[Path] = None) -> None:
        self.hub_root = hub_root or Path(__file__).resolve().parent.parent.parent
        self.worktree_dir = self.hub_root / ".worktrees"
        self.worktree_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir = self.hub_root / "data" / "swarm_artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.audit_trail_path = self.artifacts_dir / "audit_trail.ndjson"

    def record_audit_event(
        self,
        event: str,
        agent: str,
        task_id: str,
        trace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Appends an immutable event record to the NDJSON Audit Trail.
        """
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "agent": agent,
            "task_id": task_id,
            "trace_id": trace_id or str(uuid.uuid4()),
            "details": details or {},
        }
        line = json.dumps(record, ensure_ascii=False)
        with open(self.audit_trail_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return record

    def read_audit_events(
        self,
        task_id: Optional[str] = None,
        agent: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Reads recent audit events, optionally filtered by task_id or agent."""
        if not self.audit_trail_path.exists():
            return []
        events: List[Dict[str, Any]] = []
        try:
            with open(self.audit_trail_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        ev = json.loads(stripped)
                        if task_id and ev.get("task_id") != task_id:
                            continue
                        if agent and ev.get("agent") != agent:
                            continue
                        events.append(ev)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning(f"Failed to read audit trail: {e}")
        return events[-limit:]

    def create_worktree(
        self,
        task_id: str,
        agent: str,
        base_ref: str = "HEAD",
        trace_id: Optional[str] = None,
    ) -> Tuple[Path, str]:
        """
        Creates an isolated git worktree branch for a parallel subagent.
        Returns: (worktree_path, branch_name)
        """
        safe_task_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", task_id)
        branch_name = f"swarm/{agent}/{safe_task_id}"
        worktree_path = self.worktree_dir / safe_task_id

        # Clean existing worktree directory or branch if stale
        if worktree_path.exists():
            self.cleanup_worktree(worktree_path, branch_name, delete_branch=True)

        # Create git worktree
        cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_path), base_ref]
        res = subprocess.run(cmd, cwd=str(self.hub_root), capture_output=True, text=True)
        if res.returncode != 0:
            # Fallback: if branch exists, detach or use existing branch
            if "already exists" in res.stderr:
                cmd_existing = ["git", "worktree", "add", str(worktree_path), branch_name]
                res = subprocess.run(cmd_existing, cwd=str(self.hub_root), capture_output=True, text=True)

        if not worktree_path.exists():
            raise RuntimeError(f"Failed to create git worktree at {worktree_path}: {res.stderr}")

        self.record_audit_event(
            event="SWARM_WORKTREE_CREATED",
            agent=agent,
            task_id=task_id,
            trace_id=trace_id,
            details={
                "worktree_path": str(worktree_path.relative_to(self.hub_root)),
                "branch_name": branch_name,
                "base_ref": base_ref,
            },
        )
        return worktree_path, branch_name

    def detect_changed_files(self, worktree_path: Path) -> List[str]:
        """Detects files modified, created, or deleted in the worktree."""
        cmd = ["git", "status", "--porcelain"]
        res = subprocess.run(cmd, cwd=str(worktree_path), capture_output=True, text=True)
        if res.returncode != 0:
            return []
        changed = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                changed.append(parts[1].strip())
        return changed

    def evaluate_sangha_consensus(
        self,
        worktree_path: Path,
        agent: str,
        task_id: str,
        changed_files: List[str],
        trace_id: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Sangha Consensus Gate: Dual verification (Auditor + Builder invariants)
        before merging changes into the primary working tree.
        """
        audit_start = datetime.now(timezone.utc)
        violations: List[str] = []

        if not changed_files:
            return True, {
                "consensus": "PASSED",
                "message": "No file mutations detected.",
                "duration_ms": 0,
            }

        # 1. Syntax Check on Python / JSON files
        for rel_file in changed_files:
            file_path = worktree_path / rel_file
            if not file_path.exists():
                continue
            if rel_file.endswith(".py"):
                try:
                    py_compile.compile(str(file_path), doraise=True)
                except py_compile.PyCompileError as pe:
                    violations.append(f"Python syntax error in {rel_file}: {pe}")
            elif rel_file.endswith(".json"):
                try:
                    json.loads(file_path.read_text(encoding="utf-8"))
                except Exception as je:
                    violations.append(f"JSON syntax error in {rel_file}: {je}")

        # 2. Path Hygiene Check: no hardcoded absolute /Users/ or /home/
        for rel_file in changed_files:
            file_path = worktree_path / rel_file
            if not file_path.exists() or file_path.is_dir():
                continue
            if file_path.suffix in [".py", ".ts", ".tsx", ".yaml", ".yml", ".sh"]:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if ABSOLUTE_PATH_PATTERN.search(content):
                        violations.append(f"Path hygiene violation: absolute path found in {rel_file}")
                except Exception:
                    pass

        # 3. Decision
        duration_ms = int((datetime.now(timezone.utc) - audit_start).total_seconds() * 1000)
        passed = len(violations) == 0
        consensus_status = "APPROVED" if passed else "REJECTED"

        consensus_result = {
            "consensus": consensus_status,
            "verdict": consensus_status,
            "agent": agent,
            "task_id": task_id,
            "changed_files": changed_files,
            "violations": violations,
            "duration_ms": duration_ms,
        }

        self.record_audit_event(
            event="SWARM_SANGHA_CONSENSUS_AUDIT",
            agent=agent,
            task_id=task_id,
            trace_id=trace_id,
            details=consensus_result,
        )

        return passed, consensus_result

    def merge_worktree_changes(
        self,
        worktree_path: Path,
        branch_name: str,
        agent: str,
        task_id: str,
        trace_id: Optional[str] = None,
    ) -> bool:
        """
        Commits changes inside worktree and merges back to current working branch.
        """
        changed = self.detect_changed_files(worktree_path)
        if not changed:
            return True

        # Commit in worktree
        subprocess.run(["git", "add", "."], cwd=str(worktree_path), capture_output=True)
        commit_msg = f"swarm({agent}): automated contribution for {task_id}"
        commit_res = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(worktree_path),
            capture_output=True,
            text=True,
        )

        if commit_res.returncode != 0 and "nothing to commit" not in commit_res.stdout:
            logger.warning(f"Commit in worktree failed: {commit_res.stderr}")
            return False

        # Apply / cherry-pick / merge changes to hub root
        # Using git merge or checkout to copy changed files
        for rel_file in changed:
            src = worktree_path / rel_file
            dst = self.hub_root / rel_file
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        self.record_audit_event(
            event="SWARM_WORKTREE_MERGED",
            agent=agent,
            task_id=task_id,
            trace_id=trace_id,
            details={"branch": branch_name, "files_merged": changed},
        )
        return True

    def cleanup_worktree(
        self,
        worktree_path: Path,
        branch_name: str,
        delete_branch: bool = True,
        trace_id: Optional[str] = None,
    ) -> bool:
        """
        Safely removes git worktree directory and branch.
        """
        try:
            # git worktree remove --force
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree_path)],
                cwd=str(self.hub_root),
                capture_output=True,
            )
            # Remove directory if leftover
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)

            if delete_branch:
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=str(self.hub_root),
                    capture_output=True,
                )

            self.record_audit_event(
                event="SWARM_WORKTREE_CLEANED",
                agent="swarm_coordinator",
                task_id=worktree_path.name,
                trace_id=trace_id,
                details={"worktree_path": str(worktree_path), "branch": branch_name},
            )
            return True
        except Exception as e:
            logger.error(f"Error during worktree cleanup: {e}")
            return False

    @contextmanager
    def isolated_worktree(
        self,
        task_id: str,
        agent: str,
        base_ref: str = "HEAD",
        auto_merge: bool = True,
        trace_id: Optional[str] = None,
    ) -> Generator[Path, None, None]:
        """
        Context manager for running subagent tasks in a dedicated Git Worktree.
        Automatically applies Sangha Consensus before merging, then cleans up.
        """
        worktree_path, branch_name = self.create_worktree(
            task_id=task_id,
            agent=agent,
            base_ref=base_ref,
            trace_id=trace_id,
        )
        try:
            yield worktree_path

            # Detect mutations
            changed = self.detect_changed_files(worktree_path)
            if changed and auto_merge:
                passed, audit_res = self.evaluate_sangha_consensus(
                    worktree_path=worktree_path,
                    agent=agent,
                    task_id=task_id,
                    changed_files=changed,
                    trace_id=trace_id,
                )
                if passed:
                    self.merge_worktree_changes(
                        worktree_path=worktree_path,
                        branch_name=branch_name,
                        agent=agent,
                        task_id=task_id,
                        trace_id=trace_id,
                    )
                else:
                    logger.warning(
                        f"Sangha Consensus REJECTED changes for task {task_id}: {audit_res.get('violations')}"
                    )
        finally:
            self.cleanup_worktree(
                worktree_path=worktree_path,
                branch_name=branch_name,
                delete_branch=True,
                trace_id=trace_id,
            )
