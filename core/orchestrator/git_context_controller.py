# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/git_context_controller.py"
# purpose: "Git-like Context Controller for branch creation, switching, committing, merging, and discarding speculative LLM contexts."
# canonical_source: true
# alters_files: ["cache/context_branches/branches.json", "cache/context_branches/commits.json"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.orchestrator.context_branch import (
    ContextBranch,
    ContextCommit,
    ContextOperation,
    isolate_context_for_task,
)

__all__ = [
    "GitContextController",
    "ContextBranch",
    "ContextCommit",
    "ContextOperation",
    "isolate_context_for_task",
]


class GitContextController:
    """
    Git-like Context Controller managing isolated context timelines (branches).
    Allows creating speculative exploration branches, adding messages, committing,
    merging back to main upon success, or discarding failed experiments to eliminate context bloat.
    """

    def __init__(self, storage_path: str = "cache/context_branches") -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.branches: Dict[str, ContextBranch] = {}
        self.commits: Dict[str, ContextCommit] = {}
        self.current_branch: str = "main"

        self._load()

        if "main" not in self.branches:
            self.branches["main"] = ContextBranch(id="main", name="main")
            self._save()

    def _load(self) -> None:
        """Loads branches and commits from disk cache if present."""
        branches_file = self.storage_path / "branches.json"
        if branches_file.exists():
            try:
                data = json.loads(branches_file.read_text(encoding="utf-8"))
                for b_dict in data:
                    branch = ContextBranch.from_dict(b_dict)
                    self.branches[branch.id] = branch
            except Exception:
                pass

        commits_file = self.storage_path / "commits.json"
        if commits_file.exists():
            try:
                data = json.loads(commits_file.read_text(encoding="utf-8"))
                for c_dict in data:
                    commit = ContextCommit.from_dict(c_dict)
                    self.commits[commit.id] = commit
            except Exception:
                pass

    def _save(self) -> None:
        """Persists branches and commits to disk cache."""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            branches_file = self.storage_path / "branches.json"
            branches_data = [b.to_dict() for b in self.branches.values()]
            branches_file.write_text(json.dumps(branches_data, indent=2), encoding="utf-8")

            commits_file = self.storage_path / "commits.json"
            commits_data = [c.to_dict() for c in self.commits.values()]
            commits_file.write_text(json.dumps(commits_data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def create_branch(
        self,
        name: str,
        from_branch: Optional[str] = None,
        copy_parent_messages: bool = False,
        checkout: bool = True,
    ) -> str:
        """
        Creates a new context branch.

        Args:
            name: Human-readable branch name (e.g. 'experiment-1')
            from_branch: Optional parent branch ID to branch off from (defaults to current_branch)
            copy_parent_messages: Whether to copy parent messages or start with fresh context (default: False)
            checkout: Automatically switch to the newly created branch (default: True)

        Returns:
            Unique branch ID prefixed with 'branch-'
        """
        branch_id = f"branch-{uuid.uuid4()}"
        parent = from_branch or self.current_branch

        if parent not in self.branches:
            raise ValueError(f"Parent branch not found: {parent}")

        parent_branch = self.branches[parent]
        msgs = [dict(m) for m in parent_branch.messages] if copy_parent_messages else []
        tokens = parent_branch.total_tokens if copy_parent_messages else 0

        new_branch = ContextBranch(
            id=branch_id,
            name=name,
            parent_branch=parent,
            messages=msgs,
            total_tokens=tokens,
            message_count=len(msgs),
        )
        self.branches[branch_id] = new_branch

        if checkout:
            self.current_branch = branch_id

        self._save()
        return branch_id

    def checkout(self, branch_id: str) -> bool:
        """
        Switches active context branch.

        Args:
            branch_id: Target branch identifier

        Returns:
            True if checkout succeeded, False otherwise
        """
        if branch_id not in self.branches:
            return False
        self.current_branch = branch_id
        return True

    def add_message(self, message: Dict[str, Any], branch_id: Optional[str] = None) -> None:
        """
        Appends a message to the target branch (or current branch).

        Args:
            message: Message payload dict
            branch_id: Optional target branch ID
        """
        target = branch_id or self.current_branch
        if target not in self.branches:
            raise ValueError(f"Branch not found: {target}")

        self.branches[target].add_message(message)
        self._save()

    def commit_branch(self, branch_id: str, message: str) -> str:
        """
        Records a context commit snapshot for the given branch.

        Args:
            branch_id: Branch identifier
            message: Commit message describing context milestone

        Returns:
            Unique commit ID prefixed with 'commit-'
        """
        if branch_id not in self.branches:
            raise ValueError(f"Branch not found: {branch_id}")

        commit_id = f"commit-{uuid.uuid4()}"
        branch = self.branches[branch_id]
        summary = self._summarize_branch(branch)
        parent_commit = self._get_latest_commit(branch_id)

        commit = ContextCommit(
            id=commit_id,
            branch_id=branch_id,
            message=message,
            summary=summary,
            parent_commit=parent_commit,
            metadata={"total_tokens": branch.total_tokens, "message_count": branch.message_count},
        )
        self.commits[commit_id] = commit
        self._save()
        return commit_id

    def merge_branch(self, branch_id: str, success: bool) -> Optional[str]:
        """
        Merges branch into main. If success is True, squashes branch into a compact summary
        and commits to main. If False, discards the branch completely.

        Args:
            branch_id: Branch identifier
            success: Whether the experimental branch was successful

        Returns:
            Commit ID on main if merged successfully, None if discarded
        """
        if branch_id not in self.branches:
            raise ValueError(f"Branch not found: {branch_id}")

        branch = self.branches[branch_id]

        if success:
            summary = self._summarize_branch(branch)
            if "main" not in self.branches:
                self.branches["main"] = ContextBranch(id="main", name="main")

            main_branch = self.branches["main"]
            main_branch.add_message({
                "role": "system",
                "content": f"[MERGED] {branch.name}: {summary}",
                "metadata": {
                    "merged_from": branch_id,
                    "merged_at": datetime.now().isoformat(),
                },
            })

            commit_id = self.commit_branch("main", f"Merged {branch.name}")
            if self.current_branch == branch_id:
                self.current_branch = "main"
            self._save()
            return commit_id
        else:
            del self.branches[branch_id]
            if self.current_branch == branch_id:
                self.current_branch = "main"
            self._save()
            return None

    def discard_branch(self, branch_id: str) -> bool:
        """
        Discards a failed or unneeded context branch without affecting other branches.

        Args:
            branch_id: Branch identifier

        Returns:
            True if branch was found and discarded, False otherwise
        """
        if branch_id not in self.branches:
            return False

        del self.branches[branch_id]
        if self.current_branch == branch_id:
            self.current_branch = "main"

        self._save()
        return True

    def get_branch_stats(self, branch_id: str) -> Dict[str, Any]:
        """
        Retrieves telemetry and stats for a branch.

        Args:
            branch_id: Branch identifier

        Returns:
            Stats dict including id, name, total_tokens, message_count, timestamps
        """
        if branch_id not in self.branches:
            raise ValueError(f"Branch not found: {branch_id}")

        b = self.branches[branch_id]
        return {
            "id": b.id,
            "name": b.name,
            "total_tokens": b.total_tokens,
            "message_count": b.message_count,
            "created_at": b.created_at.isoformat() if isinstance(b.created_at, datetime) else str(b.created_at),
            "last_activity": b.last_activity.isoformat() if isinstance(b.last_activity, datetime) else str(b.last_activity),
        }

    def list_branches(self) -> List[Dict[str, Any]]:
        """Lists all existing branches and their stats."""
        return [self.get_branch_stats(b.id) for b in self.branches.values()]

    def _summarize_branch(self, branch: ContextBranch, max_tokens: int = 500) -> str:
        """Generates a compact summary of branch messages for merging."""
        messages = branch.messages[-20:]
        summary_lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:120].replace("\n", " ")
            summary_lines.append(f"{role}: {content}...")

        summary = " | ".join(summary_lines) if summary_lines else f"Branch {branch.name} execution completed."
        words = summary.split()
        max_words = int(max_tokens * 0.7)
        if len(words) > max_words:
            summary = " ".join(words[:max_words]) + "..."
        return summary

    def _get_latest_commit(self, branch_id: str) -> Optional[str]:
        """Finds the most recent commit on a branch."""
        branch_commits = [c for c in self.commits.values() if c.branch_id == branch_id]
        if not branch_commits:
            return None
        latest = max(branch_commits, key=lambda c: c.created_at)
        return latest.id
