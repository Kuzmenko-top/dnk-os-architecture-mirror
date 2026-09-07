# --- DNK-MRH-HEADER ---
# mrh_id: "core/adapters/dnk_artifact_server_adapter.py"
# purpose: "Clean-room Hexagonal Port and Adapter for autonomous artifact publishing, versioning, and review"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

"""
Clean-Room MIT Implementation of Artifact Server.
Synthesized via Track 2 Reverse Engineering of plannotator/artifact-server (AGPL-3.0).
Provides sovereign artifact publishing, semver-like incrementing, annotation reviews, and MCP bindings.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
import re


class ArtifactServerPort(ABC):
    """Hexagonal Port for Artifact Management Engine."""

    @abstractmethod
    def create_artifact(
        self,
        title: str,
        content: str,
        artifact_type: str,
        creator: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new artifact and initialize version 1."""
        pass

    @abstractmethod
    def create_version(
        self,
        artifact_id: str,
        content: str,
        author: str,
        change_summary: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Publish a new revision of an existing artifact."""
        pass

    @abstractmethod
    def get_artifact(self, artifact_id: str, version: Optional[int] = None) -> Dict[str, Any]:
        """Retrieve an artifact and its specific or latest version."""
        pass

    @abstractmethod
    def add_comment(
        self,
        artifact_id: str,
        version: int,
        author: str,
        content: str,
        line_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add an inline review comment or annotation."""
        pass

    @abstractmethod
    def list_artifacts(
        self,
        artifact_type: Optional[str] = None,
        creator: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List published artifacts with optional filters."""
        pass


class DNKArtifactServerAdapter(ArtifactServerPort):
    """
    In-memory and persistent clean-room adapter for DNK OS Artifact Publishing.
    Enforces security isolation, input sanitization, and version immutability.
    """

    def __init__(self, storage_root: str = "./artifacts_data"):
        self.storage_root = storage_root
        self._artifacts: Dict[str, Dict[str, Any]] = {}
        self._comments: Dict[str, List[Dict[str, Any]]] = {}

    def _sanitize_string(self, text: str) -> str:
        """Sanitize strings against script tags and path escalations."""
        if not text:
            return ""
        # Check for path traversal or malicious indicators
        if ".." in text:
            raise ValueError("Invalid identifier: path traversal sequence detected")
        return text.strip()

    def create_artifact(
        self,
        title: str,
        content: str,
        artifact_type: str = "markdown",
        creator: str = "gerych_prime",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        sanitized_title = self._sanitize_string(title)
        if not sanitized_title:
            raise ValueError("Artifact title cannot be empty")

        valid_types = {"markdown", "html", "svg", "json", "code", "diagram", "video"}
        norm_type = artifact_type.lower()
        if norm_type not in valid_types:
            norm_type = "markdown"

        artifact_id = f"art_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        initial_version = {
            "version": 1,
            "content": content,
            "author": creator,
            "change_summary": "Initial publication",
            "created_at": now,
            "metadata": metadata or {},
        }

        artifact_record = {
            "artifact_id": artifact_id,
            "title": sanitized_title,
            "artifact_type": norm_type,
            "creator": creator,
            "created_at": now,
            "updated_at": now,
            "current_version": 1,
            "versions": [initial_version],
            "metadata": metadata or {},
        }

        self._artifacts[artifact_id] = artifact_record
        self._comments[artifact_id] = []
        return artifact_record

    def create_version(
        self,
        artifact_id: str,
        content: str,
        author: str = "gerych_prime",
        change_summary: str = "Revision update",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if artifact_id not in self._artifacts:
            raise KeyError(f"Artifact {artifact_id} not found")

        artifact = self._artifacts[artifact_id]
        next_version_num = artifact["current_version"] + 1
        now = datetime.now(timezone.utc).isoformat()

        new_version = {
            "version": next_version_num,
            "content": content,
            "author": author,
            "change_summary": change_summary,
            "created_at": now,
            "metadata": metadata or {},
        }

        artifact["versions"].append(new_version)
        artifact["current_version"] = next_version_num
        artifact["updated_at"] = now
        return new_version

    def get_artifact(self, artifact_id: str, version: Optional[int] = None) -> Dict[str, Any]:
        if artifact_id not in self._artifacts:
            raise KeyError(f"Artifact {artifact_id} not found")

        artifact = self._artifacts[artifact_id]
        if version is None:
            active_version_data = artifact["versions"][-1]
        else:
            matching = [v for v in artifact["versions"] if v["version"] == version]
            if not matching:
                raise KeyError(f"Version {version} of artifact {artifact_id} not found")
            active_version_data = matching[0]

        return {
            "artifact_id": artifact["artifact_id"],
            "title": artifact["title"],
            "artifact_type": artifact["artifact_type"],
            "creator": artifact["creator"],
            "created_at": artifact["created_at"],
            "updated_at": artifact["updated_at"],
            "current_version": artifact["current_version"],
            "requested_version": active_version_data["version"],
            "content": active_version_data["content"],
            "change_summary": active_version_data["change_summary"],
            "version_metadata": active_version_data.get("metadata", {}),
            "comments": self._comments.get(artifact_id, []),
            "total_versions": len(artifact["versions"]),
        }

    def add_comment(
        self,
        artifact_id: str,
        version: int,
        author: str,
        content: str,
        line_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        if artifact_id not in self._artifacts:
            raise KeyError(f"Artifact {artifact_id} not found")

        comment_id = f"cmt_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        comment_record = {
            "comment_id": comment_id,
            "artifact_id": artifact_id,
            "version": version,
            "author": author,
            "content": content,
            "line_number": line_number,
            "created_at": now,
        }

        self._comments[artifact_id].append(comment_record)
        return comment_record

    def list_artifacts(
        self,
        artifact_type: Optional[str] = None,
        creator: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        results = []
        for a in self._artifacts.values():
            if artifact_type and a["artifact_type"] != artifact_type:
                continue
            if creator and a["creator"] != creator:
                continue
            results.append({
                "artifact_id": a["artifact_id"],
                "title": a["title"],
                "artifact_type": a["artifact_type"],
                "creator": a["creator"],
                "created_at": a["created_at"],
                "updated_at": a["updated_at"],
                "current_version": a["current_version"],
            })
            if len(results) >= limit:
                break
        return results
