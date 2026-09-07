# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_os_002_test_github_adapter"
# purpose: "Unit tests for GitHub Read-Only Adapter (DNK-OS-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import time
import pytest
from apps.api.services.github_transport import MockGitHubTransport, GITHUB_API_HOST
from apps.api.services.github_adapter import GitHubAdapter, ALLOWED_REPOSITORIES


def test_allowed_repository_invariant():
    adapter = GitHubAdapter()
    res = adapter.get_pull_request("malicious/unauthorized-repo", 1)
    assert res.error_code == "forbidden_repo"
    assert res.data is None
    assert res.data_source == "live"


def test_disallowed_host_invariant():
    assert GITHUB_API_HOST == "api.github.com"


def test_security_fail_closed_on_401_403():
    mock_t = MockGitHubTransport()
    mock_t.set_response("repos/Kuzmenko-top/DNK_OS_MVP/pulls/13", None, 403, "unauthorized")
    adapter = GitHubAdapter(transport=mock_t)

    res = adapter.get_pull_request("Kuzmenko-top/DNK_OS_MVP", 13, allow_fixture_fallback=True)
    assert res.error_code == "unauthorized"
    assert res.data is None
    assert res.data_source == "live"
    assert res.stale is False


def test_cache_hit_within_ttl():
    mock_t = MockGitHubTransport()
    fake_raw = {
        "number": 13,
        "title": "feat(dnk-os): implement Visual Workspace MVP TaskDNA shell (#13)",
        "state": "closed",
        "merged": True,
        "merged_at": "2026-08-23T12:00:00Z",
        "head": {"sha": "f620f85fd4709465bb17e27991d57288421c797f"},
        "base": {"ref": "main"},
        "mergeable": True
    }
    mock_t.set_response("repos/Kuzmenko-top/DNK_OS_MVP/pulls/13", fake_raw, 200, None)
    adapter = GitHubAdapter(transport=mock_t, cache_ttl=60)

    res1 = adapter.get_pull_request("Kuzmenko-top/DNK_OS_MVP", 13)
    assert res1.data is not None
    assert res1.data_source == "live"
    assert res1.stale is False

    # Second call within TTL hits in-memory cache
    res2 = adapter.get_pull_request("Kuzmenko-top/DNK_OS_MVP", 13)
    assert res2.data is not None
    assert res2.data_source == "cache"
    assert res2.stale is False


def test_timeout_falls_back_to_stale_cache():
    mock_t = MockGitHubTransport()
    fake_raw = {
        "number": 13,
        "title": "feat: test",
        "state": "closed",
        "merged": True,
        "head": {"sha": "abcdef123456"},
        "base": {"ref": "main"},
        "mergeable": True
    }
    mock_t.set_response("repos/Kuzmenko-top/DNK_OS_MVP/pulls/13", fake_raw, 200, None)
    adapter = GitHubAdapter(transport=mock_t, cache_ttl=60)

    res1 = adapter.get_pull_request("Kuzmenko-top/DNK_OS_MVP", 13)
    assert res1.data is not None
    assert res1.data_source == "live"

    # Force cache expiration
    cache_key = "pr:Kuzmenko-top/DNK_OS_MVP:13"
    cached_data, fetched_at, _ = adapter._cache[cache_key]
    adapter._cache[cache_key] = (cached_data, fetched_at, time.time() - 10)

    # Change transport response to timeout
    mock_t.set_response("repos/Kuzmenko-top/DNK_OS_MVP/pulls/13", None, 408, "timeout")

    res2 = adapter.get_pull_request("Kuzmenko-top/DNK_OS_MVP", 13)
    assert res2.data is not None
    assert res2.data_source == "cache"
    assert res2.stale is True
    assert res2.error_code == "timeout"


def test_rate_limit_falls_back_to_fixture_if_permitted():
    mock_t = MockGitHubTransport()
    mock_t.set_response("repos/Kuzmenko-top/DNK_OS_MVP/pulls/13", None, 429, "rate_limit")
    adapter = GitHubAdapter(transport=mock_t)

    res = adapter.get_pull_request("Kuzmenko-top/DNK_OS_MVP", 13, allow_fixture_fallback=True)
    assert res.data is not None
    assert res.data_source == "fixture"
    assert res.error_code == "rate_limit"


def test_check_runs_and_changed_files_contracts():
    mock_t = MockGitHubTransport()
    mock_t.set_response("repos/Kuzmenko-top/DNK_OS_MVP/commits/sha123/check-runs", {
        "total_count": 1,
        "check_runs": [
            {"name": "pytest", "status": "completed", "conclusion": "success"}
        ]
    }, 200)

    mock_t.set_response("repos/Kuzmenko-top/DNK_OS_MVP/pulls/13/files", [
        {"filename": "apps/api/main.py", "status": "modified", "additions": 5, "deletions": 0, "changes": 5}
    ], 200)

    adapter = GitHubAdapter(transport=mock_t)

    checks_res = adapter.get_check_runs("Kuzmenko-top/DNK_OS_MVP", "sha123")
    assert checks_res.data is not None
    assert checks_res.data_source == "live"
    assert checks_res.data["overall_status"] == "SUCCESS"
    assert len(checks_res.data["check_runs"]) == 1

    files_res = adapter.get_changed_files("Kuzmenko-top/DNK_OS_MVP", 13)
    assert files_res.data is not None
    assert files_res.data_source == "live"
    assert files_res.data["file_count"] == 1
    assert files_res.data["files"][0]["filename"] == "apps/api/main.py"
