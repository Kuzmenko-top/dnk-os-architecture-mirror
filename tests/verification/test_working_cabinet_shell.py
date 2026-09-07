# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_working_cabinet_shell.py"
# purpose: "Comprehensive contract and integration verification test suite for DNK-VISUAL-OS-001 Working Cabinet"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-VISUAL-OS-001"]
# status: "Approved"
# version: "2.3.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_working_cabinet_files_structure():
    """Verify that all core Phase 1 Working Cabinet components exist in visual_shell/web_ui."""
    expected_files = [
        "visual_shell/web_ui/lib/apiClient.js",
        "visual_shell/web_ui/lib/workspaceContext.js",
        "visual_shell/web_ui/components/stitch/StitchTopHeader.jsx",
        "visual_shell/web_ui/components/stitch/StitchLeftAgentPanel.jsx",
        "visual_shell/web_ui/components/stitch/StitchNodeInspector.jsx",
        "visual_shell/web_ui/components/gateway/DNKUnifiedGateway.jsx",
        "visual_shell/web_ui/components/TerminalChat.jsx",
        "visual_shell/web_ui/pages/workspace/index.js",
    ]
    for rel_path in expected_files:
        full_path = ROOT / rel_path
        assert full_path.exists(), f"Missing required file: {rel_path}"


def test_single_canonical_workspace_route_no_duplicates():
    """Verify that only pages/workspace/index.js exists and duplicate pages/workspace.js is removed."""
    canonical_route = ROOT / "visual_shell/web_ui/pages/workspace/index.js"
    duplicate_route = ROOT / "visual_shell/web_ui/pages/workspace.js"

    assert canonical_route.exists(), "Canonical route pages/workspace/index.js must exist."
    assert not duplicate_route.exists(), "Duplicate pages/workspace.js must be deleted to prevent route ambiguity."


def test_workspace_identity_and_bearer_auth_headers():
    """Verify that apiClient.js injects X-Workspace-Id, Bearer Auth and strips caller override."""
    api_client_path = ROOT / "visual_shell/web_ui/lib/apiClient.js"
    content = api_client_path.read_text()

    assert "X-Workspace-Id" in content
    assert "Authorization" in content
    assert "authToken" in content
    assert "sanitizeAndInjectWorkspaceHeaders" in content
    assert "isValidWorkspaceUuid" in content
    assert "ZERO_UUID_FORBIDDEN" in content
    assert "00000000-0000-0000-0000-000000000000" in content


def test_workspace_context_exports_fetch_with_context_and_scoped_clear():
    """Verify that WorkspaceProvider exports fetchWithContext, clearScopedData, and handles AbortSignal."""
    ctx_path = ROOT / "visual_shell/web_ui/lib/workspaceContext.js"
    content = ctx_path.read_text()

    assert "fetchWithContext" in content
    assert "clearScopedData" in content
    assert "discoverWorkspaces" in content
    assert "lifecycleAbortRef" in content
    assert "switchTimeoutRef" in content
    assert "authToken" in content


def test_read_only_telemetry_health_check_contract():
    """Verify that health check initial state is 'unknown' and endpoints are separated."""
    ctx_path = ROOT / "visual_shell/web_ui/lib/workspaceContext.js"
    content = ctx_path.read_text()

    assert "dnkApi: 'unknown'" in content
    assert "postgres: 'unknown'" in content
    assert "redis: 'unknown'" in content
    assert "/api/v1/health" in content


def test_no_destructive_browser_alerts():
    """Verify that alert() calls are replaced with disabled deferred UI placeholders."""
    for filepath in ROOT.glob("visual_shell/web_ui/**/*.jsx"):
        content = filepath.read_text()
        assert "alert(" not in content, f"Destructive alert() call found in {filepath}"


def test_mrh_author_headers_present():
    """Verify MRH Author Header is present in all modified/created files."""
    files_to_check = [
        ROOT / "visual_shell/web_ui/lib/apiClient.js",
        ROOT / "visual_shell/web_ui/lib/workspaceContext.js",
        ROOT / "visual_shell/web_ui/pages/workspace/index.js",
        ROOT / "tests/verification/test_working_cabinet_shell.py",
        ROOT / "tests/verification/test_workspace_contracts.py",
    ]
    for filepath in files_to_check:
        content = filepath.read_text()
        assert '# author: "DNK-e.com Maksym"' in content or '// author: "DNK-e.com Maksym"', (
            f"Missing MRH author header in {filepath}"
        )
