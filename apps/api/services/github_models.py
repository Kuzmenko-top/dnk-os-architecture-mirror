# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_github_models"
# purpose: "Pydantic domain models and result contracts for GitHub Read-Only Adapter"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class NormalizedCheckRun(BaseModel):
    """Normalized GitHub Check Run model."""
    name: str
    status: Literal["queued", "in_progress", "completed"]
    conclusion: Optional[Literal["success", "failure", "neutral", "cancelled", "timed_out", "action_required", "stale", "skipped"]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    html_url: Optional[str] = None


class NormalizedChangedFile(BaseModel):
    """Normalized GitHub PR Changed File model."""
    filename: str
    status: Literal["added", "modified", "removed", "renamed", "copied", "changed", "unchanged"]
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: Optional[str] = None


class NormalizedPullRequest(BaseModel):
    """Normalized GitHub Pull Request model."""
    number: int
    title: str
    state: Literal["OPEN", "MERGED", "CLOSED"]
    head_sha: str
    base_branch: str
    checks_status: Literal["SUCCESS", "FAILURE", "PENDING", "NEUTRAL"]
    mergeable: bool = True
    merged_at: Optional[str] = None
    changed_files_count: Optional[int] = None
    checks: List[Dict[str, Any]] = Field(default_factory=list)


class NormalizedBranch(BaseModel):
    """Normalized Git Branch reference model."""
    repository: str
    branch: str
    base_branch: str
    base_sha: str
    head_sha: str
    merge_sha: Optional[str] = None


class GitHubAdapterResult(BaseModel):
    """Explicit container for all GitHub Adapter operations."""
    data: Optional[Any] = None
    data_source: Literal["live", "cache", "fixture"]
    stale: bool = False
    fetched_at: str
    expires_at: str
    error_code: Optional[str] = None
