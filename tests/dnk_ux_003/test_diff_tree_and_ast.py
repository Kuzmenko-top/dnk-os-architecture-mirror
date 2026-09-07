# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_ux_003_test_diff_tree_and_ast"
# purpose: "Unit & Integration test suite for DNK-UX-003 Unified Diff Parser, AST Change Extractor, and API Endpoints"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.services.diff_parser import parse_file_patch, build_diff_tree
from apps.api.services.ast_diff import analyze_file_ast_diff, extract_python_symbols
from core.config.security_config import SECURITY_API_KEY


def test_diff_parser_unified_hunks():
    patch = "@@ -1,5 +1,7 @@\n def old_func():\n-    return 1\n+    return 2\n+    return 3\n"
    res = parse_file_patch("apps/api/services/diff_parser.py", patch, status="modified")
    assert res["filename"] == "apps/api/services/diff_parser.py"
    assert res["status"] == "modified"
    assert res["additions"] == 2
    assert res["deletions"] == 1
    assert len(res["hunks"]) == 1

    hunk = res["hunks"][0]
    assert hunk["header"] == "@@ -1,5 +1,7 @@"
    assert len(hunk["lines"]) == 4
    assert hunk["lines"][1]["type"] == "delete"
    assert hunk["lines"][1]["content"] == "    return 1"
    assert hunk["lines"][2]["type"] == "add"
    assert hunk["lines"][2]["content"] == "    return 2"


def test_diff_tree_builder():
    file1 = parse_file_patch("apps/api/services/diff_parser.py", "@@ -0,0 +1,5 @@\n+line1", status="added")
    file2 = parse_file_patch("apps/web/components/PRInspectorTab.tsx", "@@ -1,5 +1,5 @@\n-old\n+new", status="modified")

    tree = build_diff_tree([file1, file2])
    assert tree["name"] == "root"
    assert tree["file_count"] == 2
    assert len(tree["children"]) == 1  # 'apps'

    apps_node = tree["children"][0]
    assert apps_node["name"] == "apps"
    assert apps_node["file_count"] == 2

    child_names = [c["name"] for c in apps_node["children"]]
    assert "api" in child_names
    assert "web" in child_names


def test_ast_diff_python():
    old_code = """# --- DNK-MRH-HEADER ---
# mrh_id: "test"
class Service:
    def run(self):
        pass
"""

    new_code = """# --- DNK-MRH-HEADER ---
# mrh_id: "test"
class Service:
    def run(self):
        print("updated")
    def stop(self):
        pass

def standalone():
    pass
"""

    res = analyze_file_ast_diff("test_service.py", old_code=old_code, new_code=new_code)
    assert res["language"] == "python"
    assert res["added_count"] >= 2  # stop, standalone
    assert res["modified_count"] >= 1  # run

    sym_names = [s["name"] for s in res["symbols"]]
    assert "Service.stop" in sym_names
    assert "standalone" in sym_names


def test_ast_diff_typescript():
    old_code = """export class UIController {
  render() {
    return null;
  }
}"""

    new_code = """export class UIController {
  render() {
    return <div>Updated</div>;
  }
  handleSelect() {
    console.log("selected");
  }
}

export function helper() {}
"""

    res = analyze_file_ast_diff("UIController.tsx", old_code=old_code, new_code=new_code)
    assert res["language"] == "typescript"
    sym_names = [s["name"] for s in res["symbols"]]
    assert "UIController.handleSelect" in sym_names
    assert "helper" in sym_names


def test_api_endpoints_dnk_ux_003(monkeypatch):
    monkeypatch.setenv("FIXTURE_MODE", "true")

    client = TestClient(app)
    headers = {
        "X-API-Key": SECURITY_API_KEY,
        "X-Tenant-ID": "tenant-alpha-001",
        "X-Workspace-ID": "ws-alpha-001"
    }

    # 1. GET /diff
    resp_diff = client.get("/api/github/pr/Kuzmenko-top/DNK_OS_MVP/30/diff?allow_fixture_fallback=true", headers=headers)
    assert resp_diff.status_code == 200
    data = resp_diff.json()["data"]
    assert data["pr_number"] == 30
    assert "tree" in data
    assert "files" in data
    assert len(data["files"]) > 0

    # 2. GET /diff/file
    resp_file = client.get(
        "/api/github/pr/Kuzmenko-top/DNK_OS_MVP/30/diff/file?filename=apps/api/services/diff_parser.py&allow_fixture_fallback=true",
        headers=headers
    )
    assert resp_file.status_code == 200
    file_data = resp_file.json()["data"]
    assert file_data["filename"] == "apps/api/services/diff_parser.py"
    assert "file_diff" in file_data

    # 3. GET /ast-diff
    resp_ast = client.get("/api/github/pr/Kuzmenko-top/DNK_OS_MVP/30/ast-diff?allow_fixture_fallback=true", headers=headers)
    assert resp_ast.status_code == 200
    ast_data = resp_ast.json()["data"]
    assert "ast_diffs" in ast_data
    assert len(ast_data["ast_diffs"]) > 0


def test_api_security_boundary_fail_closed():
    client = TestClient(app)
    # Unauthorized repo call
    resp = client.get("/api/github/pr/unauthorized_owner/unauthorized_repo/30/diff")
    # Should return 401 (missing auth headers) or 200 with error_code='forbidden_repo'
    if resp.status_code == 200:
        assert resp.json()["error_code"] in ["forbidden_repo", "unauthorized"]
    else:
        assert resp.status_code in [401, 403, 429]
