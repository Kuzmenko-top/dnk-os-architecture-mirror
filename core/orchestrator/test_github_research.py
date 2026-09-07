#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/test_github_research.py"
# purpose: "Unit tests for GitHub Research, Two-Track licensing, and honest fallbacks."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.1.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from unittest.mock import patch, MagicMock
from core.orchestrator.github_research import (
    LicenseTrack,
    gh_available,
    classify_license,
    extract_github_repos_from_text,
    analyze_github_repo,
)


def test_gh_available_type():
    res = gh_available()
    assert isinstance(res, bool)


def test_classify_license_spdx():
    # Permissive Track 1
    mit = classify_license("MIT")
    assert mit["track"] == LicenseTrack.TRACK_1_DIRECT.value
    assert mit["direct_copy_permitted"] is True

    apache = classify_license("Apache-2.0")
    assert apache["track"] == LicenseTrack.TRACK_1_DIRECT.value
    assert apache["direct_copy_permitted"] is True

    bsd = classify_license("BSD-3-Clause")
    assert bsd["track"] == LicenseTrack.TRACK_1_DIRECT.value
    assert bsd["direct_copy_permitted"] is True

    # Copyleft / Restrictive Track 2
    gpl = classify_license("GPL-3.0")
    assert gpl["track"] == LicenseTrack.TRACK_2_CLEAN_ROOM.value
    assert gpl["direct_copy_permitted"] is False

    agpl = classify_license("AGPL-3.0-only")
    assert agpl["track"] == LicenseTrack.TRACK_2_CLEAN_ROOM.value
    assert agpl["direct_copy_permitted"] is False

    # Unknown
    unknown = classify_license(None)
    assert unknown["track"] == LicenseTrack.TRACK_2_CLEAN_ROOM.value
    assert unknown["direct_copy_permitted"] is False


def test_extract_github_repos():
    text = "Check out https://github.com/langchain-ai/langgraph and also github.com/pallets/flask.git for patterns."
    repos = extract_github_repos_from_text(text)
    assert "langchain-ai/langgraph" in repos
    assert "pallets/flask" in repos
    assert len(repos) == 2


def test_honest_fallback_when_gh_missing():
    with patch("core.orchestrator.github_research.gh_available", return_value=False):
        res = analyze_github_repo("test-owner/test-repo")
        assert res["stars"] == 0
        assert res["last_commit"] == "UNKNOWN"
        assert res["fallback_used"] is True
        assert res["rate_limit_exceeded"] is False


def test_rate_limit_handling():
    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stderr = "HTTP 403: API rate limit exceeded for user"
    mock_proc.stdout = ""

    with patch("core.orchestrator.github_research.gh_available", return_value=True):
        with patch("subprocess.run", return_value=mock_proc):
            res = analyze_github_repo("test-owner/rate-limited-repo")
            assert res["stars"] == 0
            assert res["last_commit"] == "UNKNOWN"
            assert res["fallback_used"] is True
            assert res["rate_limit_exceeded"] is True
