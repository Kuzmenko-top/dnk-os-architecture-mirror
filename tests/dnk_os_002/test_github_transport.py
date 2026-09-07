# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_os_002_test_github_transport"
# purpose: "Unit tests for GitHub transport abstraction and timeout handling"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import pytest
import urllib.error
import socket
from unittest.mock import patch, MagicMock

from apps.api.services.github_transport import (
    HttpGitHubTransport,
    MockGitHubTransport,
    GITHUB_API_HOST
)


def test_github_api_host_constant():
    assert GITHUB_API_HOST == "api.github.com"


def test_mock_transport():
    mock_t = MockGitHubTransport()
    mock_t.set_response("repos/org/repo/pulls/1", {"number": 1}, 200)

    data, status, err = mock_t.get("repos/org/repo/pulls/1")
    assert status == 200
    assert data == {"number": 1}
    assert err is None

    data_404, status_404, err_404 = mock_t.get("nonexistent")
    assert status_404 == 404
    assert err_404 == "not_found"


def test_http_transport_timeout_error():
    transport = HttpGitHubTransport(timeout=0.001)
    with patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
        data, status, err = transport.get("repos/Kuzmenko-top/DNK_OS_MVP/pulls/1")
        assert status == 408
        assert err == "timeout"
        assert data is None


def test_http_transport_unauthorized_error():
    transport = HttpGitHubTransport()
    http_err = urllib.error.HTTPError(
        url="https://api.github.com/test",
        code=401,
        msg="Unauthorized",
        hdrs=MagicMock(),
        fp=None
    )
    with patch("urllib.request.urlopen", side_effect=http_err):
        data, status, err = transport.get("repos/Kuzmenko-top/DNK_OS_MVP/pulls/1")
        assert status == 401
        assert err == "unauthorized"
        assert data is None
