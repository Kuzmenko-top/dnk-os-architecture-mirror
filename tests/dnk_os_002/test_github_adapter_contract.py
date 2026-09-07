# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_os_002_test_github_adapter_contract"
# purpose: "Comprehensive contract and security tests for GitHub Read-Only Adapter (DNK-OS-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import inspect
from apps.api.services.github_adapter import GitHubAdapter
from apps.api.services.github_transport import HttpGitHubTransport
from apps.api.services.github_models import NormalizedPullRequest, NormalizedCheckRun, NormalizedChangedFile


def test_token_read_only_from_server_environment():
    transport = HttpGitHubTransport(token="secret_server_token_123")
    adapter = GitHubAdapter(transport=transport)
    res = adapter.get_pull_request("Kuzmenko-top/DNK_OS_MVP", 13, allow_fixture_fallback=True)
    res_str = str(res.model_dump())
    assert "secret_server_token_123" not in res_str


def test_no_github_write_methods_exist():
    adapter = GitHubAdapter()
    methods = [m for m in dir(adapter) if not m.startswith("_")]
    for method in methods:
        assert not any(write_verb in method.lower() for write_verb in ["post", "put", "delete", "patch", "create", "update", "merge"])


def test_github_request_uses_read_only_get():
    transport = HttpGitHubTransport()
    src = inspect.getsource(transport.get)
    assert 'method="GET"' in src or "method='GET'" in src
    assert "POST" not in src
    assert "DELETE" not in src


def test_normalized_pr_model_schema():
    norm = NormalizedPullRequest(
        number=13,
        title="Test PR",
        state="MERGED",
        head_sha="f620f85fd4709465bb17e27991d57288421c797f",
        base_branch="main",
        checks_status="SUCCESS",
        mergeable=True
    )
    d = norm.model_dump()
    assert d["number"] == 13
    assert d["state"] == "MERGED"
    assert d["head_sha"] == "f620f85fd4709465bb17e27991d57288421c797f"


def test_normalized_check_run_and_changed_file_schema():
    cr = NormalizedCheckRun(
        name="pytest",
        status="completed",
        conclusion="success"
    )
    assert cr.model_dump()["name"] == "pytest"

    cf = NormalizedChangedFile(
        filename="apps/api/main.py",
        status="modified",
        additions=5,
        deletions=1,
        changes=6
    )
    assert cf.model_dump()["filename"] == "apps/api/main.py"
