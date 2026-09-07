# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_github_poller.py"
# purpose: "Unit and Integration Tests for GitHub API Poller Service."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.github_poller import (
    GitHubAPIPoller,
    MonitoredRepo,
    DEFAULT_TARGET_REPOS
)


@pytest.mark.asyncio
async def test_github_poller_initialization():
    poller = GitHubAPIPoller(github_token="fake_test_token")
    assert poller.headers["Authorization"] == "token fake_test_token"
    assert "User-Agent" in poller.headers


@pytest.mark.asyncio
async def test_github_poller_target_repos():
    poller = GitHubAPIPoller()
    test_repos = [
        MonitoredRepo(repo_slug="langchain-ai/open-canvas", category="canvas"),
        MonitoredRepo(repo_slug="remotionlabs/remotion", category="video")
    ]
    report = await poller.poll_target_repositories(test_repos)
    assert report.total_repos_checked == 2
    assert len(report.details) == 2
