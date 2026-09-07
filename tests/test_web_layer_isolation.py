# --- DNK-MRH-HEADER ---
# mrh_id: "tests_test_web_layer_isolation"
# purpose: "Verify apps/web strict layer isolation from visual_shell and deprecated modules per Two-Tier Protocol"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import re
import pytest
from pathlib import Path

def test_apps_web_has_zero_visual_shell_imports():
    """Verify that apps/web source files do not import anything from visual_shell."""
    web_dir = Path("apps/web")
    assert web_dir.exists(), "apps/web directory must exist"

    forbidden_patterns = [
        re.compile(r"['\"].*visual_shell.*['\"]"),
        re.compile(r"['\"].*\.\./\.\./visual_shell.*['\"]"),
        re.compile(r"from\s+['\"][^'\"]*open_design[^'\"]*['\"]"),
    ]

    violating_files = []

    for root, dirs, files in os.walk(web_dir):
        # Skip node_modules, .next, dist
        dirs[:] = [d for d in dirs if d not in {"node_modules", ".next", "dist", "out", ".turbo"}]
        for f in files:
            if f.endswith((".ts", ".tsx", ".js", ".jsx")):
                full_path = Path(root) / f
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                for pat in forbidden_patterns:
                    if pat.search(content):
                        violating_files.append(str(full_path))
                        break

    assert len(violating_files) == 0, f"Found forbidden cross-layer imports in apps/web: {violating_files}"


def test_api_protocol_types_exist():
    """Verify that canonical apiProtocol.ts exists and exports standard Result and ApiError contracts."""
    protocol_file = Path("apps/web/types/apiProtocol.ts")
    assert protocol_file.exists(), "apps/web/types/apiProtocol.ts must exist"
    
    content = protocol_file.read_text(encoding="utf-8")
    assert "export interface ApiError" in content
    assert "export type Result<T, E = ApiError>" in content
    assert "export const ok" in content
    assert "export const err" in content
    assert "export function normalizeError" in content
    assert "export async function safeAsync" in content
