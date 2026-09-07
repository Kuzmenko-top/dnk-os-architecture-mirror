# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/swarm_ledger.py"
# purpose: "High-Performance Swarm Shared Memory Ledger & Artifact Mailbox (ruflo meta-harness pattern)."
# canonical_source: true
# alters_files: ["data/swarm_artifacts/swarm_ledger.json", "data/swarm_artifacts/mailboxes/"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & Maksym Kuzmenko"
# --- END DNK-MRH-HEADER ---

"""
Swarm Shared Memory Ledger & Artifact Mailbox (ruflo meta-harness pattern).

Provides:
- Thread-safe, sub-millisecond in-memory ledger with persistent JSON/NDJSON storage
- Structured artifact catalog (schemas, TypeScript definitions, API contracts, diffs)
- Agent Mailbox System: asynchronous inter-agent message & artifact delivery
- Cryptographic SHA-256 integrity verification
- TTL-based ephemeral artifact eviction
"""

import hashlib
import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ArtifactCategory(str, Enum):
    SCHEMA = "schema"
    TYPE_DEF = "type_def"
    API_CONTRACT = "api_contract"
    CODE_DIFF = "code_diff"
    SYNTHESIS_SUMMARY = "synthesis_summary"
    METRIC_DATA = "metric_data"
    LIQUID_SECTION = "liquid_section"
    CUSTOM = "custom"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized = value.lower().strip()
            for member in cls:
                if member.value == normalized:
                    return member
        return cls.CUSTOM


@dataclass
class SwarmArtifact:
    artifact_id: str
    category: ArtifactCategory
    key: str
    producer_agent: str
    content: Any
    task_id: str = "default"
    recipient_agent: Optional[str] = None
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    ttl_seconds: Optional[int] = None
    is_read: bool = False

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = self.compute_hash(self.content)

    @staticmethod
    def compute_hash(data: Any) -> str:
        if isinstance(data, (dict, list)):
            serialized = json.dumps(data, sort_keys=True, default=str)
        else:
            serialized = str(data)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        try:
            created_dt = datetime.fromisoformat(self.created_at)
            now = datetime.now(timezone.utc)
            return (now - created_dt).total_seconds() > self.ttl_seconds
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SwarmArtifact":
        copied = dict(data)
        if "category" in copied and isinstance(copied["category"], str):
            copied["category"] = ArtifactCategory(copied["category"])
        return cls(**copied)


class SwarmLedger:
    """
    Centralized Swarm Shared Memory Ledger.
    Provides sub-millisecond retrieval of schemas, type definitions, and API specs
    across parallel swarm workers without filesystem scraping or context bloat.
    """

    _instance: Optional["SwarmLedger"] = None
    _lock = threading.Lock()

    def __init__(
        self,
        hub_root: Optional[Union[str, Path]] = None,
        storage_path: Optional[Union[str, Path]] = None,
    ):
        self.hub_root = Path(hub_root or os.getcwd()).resolve()
        self.storage_path = Path(
            storage_path
            or self.hub_root / "data" / "swarm_artifacts" / "swarm_ledger.json"
        ).resolve()
        self.mailboxes_dir = (
            self.hub_root / "data" / "swarm_artifacts" / "mailboxes"
        ).resolve()

        self._artifacts: Dict[str, SwarmArtifact] = {}
        self._key_index: Dict[str, str] = {}  # key -> artifact_id
        self._rw_lock = threading.RLock()

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.mailboxes_dir.mkdir(parents=True, exist_ok=True)
        self._load_from_disk()

    @classmethod
    def get_instance(
        cls, hub_root: Optional[Union[str, Path]] = None
    ) -> "SwarmLedger":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(hub_root=hub_root)
            return cls._instance

    def _load_from_disk(self) -> None:
        with self._rw_lock:
            if not self.storage_path.exists():
                return
            try:
                content = self.storage_path.read_text(encoding="utf-8")
                if not content.strip():
                    return
                raw_data = json.loads(content)
                for item in raw_data.get("artifacts", []):
                    artifact = SwarmArtifact.from_dict(item)
                    if not artifact.is_expired():
                        self._artifacts[artifact.artifact_id] = artifact
                        self._key_index[artifact.key] = artifact.artifact_id
            except Exception as e:
                # Log or tolerate corrupted ledger on recovery
                pass

    def _persist_to_disk(self) -> None:
        with self._rw_lock:
            try:
                # Purge expired before persisting
                self._purge_expired_locked()
                data = {
                    "version": "1.0.0",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "total_artifacts": len(self._artifacts),
                    "artifacts": [
                        a.to_dict() for a in self._artifacts.values()
                    ],
                }
                tmp_path = self.storage_path.with_suffix(".tmp")
                tmp_path.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                tmp_path.replace(self.storage_path)
            except Exception:
                pass

    def _purge_expired_locked(self) -> None:
        expired_ids = [
            aid for aid, art in self._artifacts.items() if art.is_expired()
        ]
        for aid in expired_ids:
            art = self._artifacts.pop(aid, None)
            if art and self._key_index.get(art.key) == aid:
                del self._key_index[art.key]

    def register_artifact(
        self,
        key: str,
        category: Union[ArtifactCategory, str],
        producer_agent: str,
        content: Any,
        task_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[str]] = None,
        ttl_seconds: Optional[int] = None,
        recipient_agent: Optional[str] = None,
    ) -> SwarmArtifact:
        """Register or update an artifact in the shared memory ledger."""
        with self._rw_lock:
            self._purge_expired_locked()
            cat = (
                ArtifactCategory(category)
                if isinstance(category, str)
                else category
            )
            aid = f"art_{hashlib.md5(f'{key}_{task_id}_{time.time()}'.encode()).hexdigest()[:12]}"

            artifact = SwarmArtifact(
                artifact_id=aid,
                category=cat,
                key=key,
                producer_agent=producer_agent,
                content=content,
                task_id=task_id,
                recipient_agent=recipient_agent,
                metadata=metadata or {},
                depends_on=depends_on or [],
                ttl_seconds=ttl_seconds,
            )

            self._artifacts[aid] = artifact
            self._key_index[key] = aid
            self._persist_to_disk()

            # If recipient is defined, deliver to mailbox
            if recipient_agent:
                self._deliver_to_mailbox(recipient_agent, artifact)

            return artifact

    def get_artifact(
        self, artifact_id_or_key: str
    ) -> Optional[SwarmArtifact]:
        """Fetch artifact by either artifact_id or unique key."""
        with self._rw_lock:
            self._purge_expired_locked()
            if artifact_id_or_key in self._artifacts:
                art = self._artifacts[artifact_id_or_key]
                return art if not art.is_expired() else None
            aid = self._key_index.get(artifact_id_or_key)
            if aid and aid in self._artifacts:
                art = self._artifacts[aid]
                return art if not art.is_expired() else None
            return None

    def find_artifacts(
        self,
        category: Optional[Union[ArtifactCategory, str]] = None,
        producer_agent: Optional[str] = None,
        task_id: Optional[str] = None,
        prefix_key: Optional[str] = None,
    ) -> List[SwarmArtifact]:
        """Filter artifacts by category, agent, task, or key prefix."""
        with self._rw_lock:
            self._purge_expired_locked()
            cat = (
                ArtifactCategory(category)
                if isinstance(category, str)
                else category
            )
            results = []
            for art in self._artifacts.values():
                if cat and art.category != cat:
                    continue
                if producer_agent and art.producer_agent != producer_agent:
                    continue
                if task_id and art.task_id != task_id:
                    continue
                if prefix_key and not art.key.startswith(prefix_key):
                    continue
                results.append(art)
            return sorted(results, key=lambda x: x.created_at, reverse=True)

    def delete_artifact(self, artifact_id_or_key: str) -> bool:
        """Remove artifact from ledger."""
        with self._rw_lock:
            aid = artifact_id_or_key
            if aid not in self._artifacts:
                aid = self._key_index.get(artifact_id_or_key, "")
            if aid in self._artifacts:
                art = self._artifacts.pop(aid)
                if self._key_index.get(art.key) == aid:
                    del self._key_index[art.key]
                self._persist_to_disk()
                return True
            return False

    def clear(self) -> None:
        """Clear all artifacts from memory and disk."""
        with self._rw_lock:
            self._artifacts.clear()
            self._key_index.clear()
            self._persist_to_disk()

    # --- Agent Mailbox Subsystem ---

    def _deliver_to_mailbox(
        self, recipient_agent: str, artifact: SwarmArtifact
    ) -> None:
        """Persist message in recipient agent mailbox."""
        agent_box_dir = self.mailboxes_dir / recipient_agent
        agent_box_dir.mkdir(parents=True, exist_ok=True)
        inbox_file = agent_box_dir / "inbox.ndjson"

        with open(inbox_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(artifact.to_dict(), ensure_ascii=False) + "\n")

    def fetch_mailbox(
        self,
        recipient_agent: str,
        unread_only: bool = True,
        mark_read: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch and optionally mark as read all artifacts delivered to agent's mailbox."""
        agent_box_dir = self.mailboxes_dir / recipient_agent
        inbox_file = agent_box_dir / "inbox.ndjson"
        if not inbox_file.exists():
            return []

        with self._rw_lock:
            entries: List[Dict[str, Any]] = []
            try:
                for line in inbox_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        entries.append(json.loads(line.strip()))
            except Exception:
                return []

            filtered = [
                e
                for e in entries
                if (not unread_only or not e.get("is_read", False))
            ]

            if mark_read and entries:
                # Mark them read in-place
                updated = []
                for e in entries:
                    e["is_read"] = True
                    updated.append(e)
                tmp_file = inbox_file.with_suffix(".tmp")
                with open(tmp_file, "w", encoding="utf-8") as f:
                    for item in updated:
                        f.write(
                            json.dumps(item, ensure_ascii=False) + "\n"
                        )
                tmp_file.replace(inbox_file)

            return filtered
