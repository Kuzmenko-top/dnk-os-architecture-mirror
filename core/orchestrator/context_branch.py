# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/context_branch.py"
# purpose: "Context branch and commit data structures with task isolation utilities for Git-like context management."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContextOperation(str):
    COMMIT = "commit"
    BRANCH = "branch"
    MERGE = "merge"
    DISCARD = "discard"
    CHECKOUT = "checkout"


@dataclass
class ContextBranch:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "main"
    parent_branch: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Branch stats
    total_tokens: int = 0
    message_count: int = 0
    last_activity: datetime = field(default_factory=datetime.now)

    def add_message(self, message: Dict[str, Any]) -> None:
        self.messages.append(message)
        self.message_count += 1
        content = message.get("content", "")
        words = len(content.split())
        chars = len(content)
        # Approximate tokens: if words > 1 use words * 1.3, else for dense single-token blocks use chars
        tokens = max(words * 1.3, chars * 1.0) if (words <= 1 and chars > 10) else (words * 1.3)
        self.total_tokens += int(round(tokens))
        self.last_activity = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "parent_branch": self.parent_branch,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at),
            "messages": self.messages,
            "metadata": self.metadata,
            "total_tokens": self.total_tokens,
            "message_count": self.message_count,
            "last_activity": self.last_activity.isoformat() if isinstance(self.last_activity, datetime) else str(self.last_activity),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextBranch":
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                created_at = datetime.now()
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()

        last_activity = data.get("last_activity")
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity)
            except Exception:
                last_activity = datetime.now()
        elif not isinstance(last_activity, datetime):
            last_activity = datetime.now()

        return cls(
            id=data["id"],
            name=data.get("name", "main"),
            parent_branch=data.get("parent_branch"),
            created_at=created_at,
            messages=data.get("messages", []),
            metadata=data.get("metadata", {}),
            total_tokens=int(data.get("total_tokens", 0)),
            message_count=int(data.get("message_count", len(data.get("messages", [])))),
            last_activity=last_activity,
        )


@dataclass
class ContextCommit:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    branch_id: str = ""
    message: str = ""
    summary: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    parent_commit: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "branch_id": self.branch_id,
            "message": self.message,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at),
            "parent_commit": self.parent_commit,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextCommit":
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                created_at = datetime.now()
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()

        return cls(
            id=data["id"],
            branch_id=data.get("branch_id", ""),
            message=data.get("message", ""),
            summary=data.get("summary", ""),
            created_at=created_at,
            parent_commit=data.get("parent_commit"),
            metadata=data.get("metadata", {}),
        )


def isolate_context_for_task(task_id: str, context_controller: Any) -> str:
    """
    Create isolated context branch for task.

    Example:
    branch_id = isolate_context_for_task("refactor-123", gcc)
    -> "branch-abc123"

    Usage:
    1. Checkout branch
    2. Execute task (40k tokens accumulated)
    3. If success: merge_branch(branch_id, success=True)
    4. If failure: discard_branch(branch_id)
    """
    branch_name = f"task-{task_id}"
    branch_id = context_controller.create_branch(branch_name)
    context_controller.checkout(branch_id)
    return branch_id
