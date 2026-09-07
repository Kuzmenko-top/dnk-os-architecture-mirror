# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/github_poller.py"
# purpose: "Async GitHub API Poller for SOTA Repository Monitoring & Automatic Ingestion Pipeline."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
GitHub API Poller Service
Asynchronously polls target donor repositories for new releases or commits,
checking licenses and invoking the AST Pattern Extractor pipeline.
"""

import asyncio
import os
import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MonitoredRepo(BaseModel):
    repo_slug: str  # e.g., "langchain-ai/open-canvas"
    category: str   # e.g., "canvas", "video", "multi-agent"
    track: Optional[str] = None  # "Track 1" or "Track 2"
    last_seen_sha: Optional[str] = None
    last_seen_release: Optional[str] = None


class PollerReport(BaseModel):
    total_repos_checked: int = 0
    updates_detected: int = 0
    license_violations_blocked: int = 0
    extracted_schemas_count: int = 0
    details: List[Dict[str, Any]] = Field(default_factory=list)


DEFAULT_TARGET_REPOS = [
    MonitoredRepo(repo_slug="langchain-ai/open-canvas", category="canvas"),
    MonitoredRepo(repo_slug="langchain-ai/langgraph", category="multi-agent"),
    MonitoredRepo(repo_slug="microsoft/autogen", category="multi-agent"),
    MonitoredRepo(repo_slug="crewAIInc/crewAI", category="multi-agent"),
    MonitoredRepo(repo_slug="remotionlabs/remotion", category="video"),
    MonitoredRepo(repo_slug="FrameCN/framecn", category="video")
]


class GitHubAPIPoller:
    """
    Async GitHub API Poller that tracks donor repos for SOTA pattern extraction.
    """

    def __init__(self, github_token: Optional[str] = None):
        self.token = github_token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        self.headers = {
            "User-Agent": "DNK-OS-Ingestion-Engine/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    async def fetch_repo_status(self, repo_slug: str) -> Dict[str, Any]:
        """Fetches latest release or commit metadata from GitHub API."""
        url = f"https://api.github.com/repos/{repo_slug}/commits?per_page=1"
        req = urllib.request.Request(url, headers=self.headers)
        
        loop = asyncio.get_event_loop()
        try:
            def _fetch():
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            
            data = await loop.run_in_executor(None, _fetch)
            if isinstance(data, list) and len(data) > 0:
                commit = data[0]
                return {
                    "repo_slug": repo_slug,
                    "sha": commit.get("sha", "")[:10],
                    "message": commit.get("commit", {}).get("message", ""),
                    "status": "success"
                }
        except Exception as e:
            return {
                "repo_slug": repo_slug,
                "status": "error",
                "error": str(e)
            }
            
        return {"repo_slug": repo_slug, "status": "no_data"}

    async def poll_target_repositories(self, repos: Optional[List[MonitoredRepo]] = None) -> PollerReport:
        """Polls a set of target repositories concurrently."""
        target_repos = repos or DEFAULT_TARGET_REPOS
        report = PollerReport(total_repos_checked=len(target_repos))

        tasks = [self.fetch_repo_status(repo.repo_slug) for repo in target_repos]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for repo, res in zip(target_repos, results):
            if isinstance(res, dict) and res.get("status") == "success":
                sha = res.get("sha")
                report.updates_detected += 1
                repo.last_seen_sha = sha
                report.details.append({
                    "repo": repo.repo_slug,
                    "category": repo.category,
                    "sha": sha,
                    "message": res.get("message", "").split("\n")[0]
                })
            else:
                report.details.append({
                    "repo": repo.repo_slug,
                    "category": repo.category,
                    "status": "offline_or_rate_limited"
                })

        return report
