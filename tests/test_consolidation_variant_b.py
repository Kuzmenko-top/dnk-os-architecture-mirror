# --- DNK-MRH-HEADER ---
# mrh_id: "tests_test_consolidation_variant_b"
# purpose: "Unit tests verifying Option B consolidation: stitch widgets in apps/web, sync scripts, and OpenAPI type generation"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & Antigravity"
# --- END DNK-MRH-HEADER ---

import os
import json
from pathlib import Path


def test_stitch_components_migrated_to_apps_web():
    stitch_dir = Path("apps/web/components/stitch")
    assert stitch_dir.exists(), "apps/web/components/stitch directory must exist"

    expected_components = [
        "StitchSwarmCommandCenter.tsx",
        "StitchKineticTimeline.tsx",
        "StitchSmartInspector.tsx",
        "StitchShopifyPreviewDrawer.tsx",
        "StitchBiAnalystDrawer.tsx",
        "StitchTaskForestDrawer.tsx",
    ]

    for comp in expected_components:
        comp_path = stitch_dir / comp
        assert comp_path.exists(), f"{comp} must exist in apps/web/components/stitch"
        assert comp_path.stat().st_size > 500, f"{comp} must have valid non-empty content"

    barrel = stitch_dir / "index.ts"
    assert barrel.exists(), "index.ts must exist in apps/web/components/stitch"

    barrel_content = barrel.read_text(encoding="utf-8")
    for comp in ["StitchSwarmCommandCenter", "StitchKineticTimeline", "StitchSmartInspector", "StitchShopifyPreviewDrawer", "StitchBiAnalystDrawer", "StitchTaskForestDrawer"]:
        assert comp in barrel_content, f"Barrel must re-export {comp}"


def test_workspace_shell_integrates_swarm_command_center():
    workspace_shell = Path("apps/web/components/workspace/WorkspaceShell.tsx")
    assert workspace_shell.exists(), "WorkspaceShell.tsx must exist"

    content = workspace_shell.read_text(encoding="utf-8")
    assert "StitchSwarmCommandCenter" in content, "WorkspaceShell must import StitchSwarmCommandCenter"
    assert "isSwarmMeshOpen" in content, "WorkspaceShell must have isSwarmMeshOpen state"
    assert "Swarm Mesh" in content, "WorkspaceShell must provide Swarm Mesh trigger button"


def test_api_types_generation_and_contract_sync():
    generated_types = Path("apps/web/types/apiGenerated.ts")
    assert generated_types.exists(), "apps/web/types/apiGenerated.ts must exist"
    assert generated_types.stat().st_size > 1000, "apiGenerated.ts must not be empty"

    protocol = Path("apps/web/types/apiProtocol.ts")
    protocol_content = protocol.read_text(encoding="utf-8")
    assert "apiGenerated" in protocol_content, "apiProtocol.ts must re-export generated API types"


def test_codebase_canvas_sync_tool_and_artifact():
    sync_script = Path("scripts/system/sync_codebase_to_canvas.py")
    assert sync_script.exists(), "sync_codebase_to_canvas.py must exist"

    canvas_file = Path("docs/notes/DNK_HUB_Core_Architecture.canvas")
    assert canvas_file.exists(), "DNK_HUB_Core_Architecture.canvas must exist"

    data = json.loads(canvas_file.read_text(encoding="utf-8"))
    assert "nodes" in data and "edges" in data
    assert len(data["nodes"]) >= 20, "Canvas must contain at least 20 architecture nodes"


def test_visual_shell_deprecation_notice():
    dep_file = Path("visual_shell/DEPRECATED.md")
    assert dep_file.exists(), "visual_shell/DEPRECATED.md must exist"
    content = dep_file.read_text(encoding="utf-8")
    assert "DEPRECATED" in content
    assert "apps/web/" in content

