# --- DNK-MRH-HEADER ---
# mrh_id: "tests_test_import_cycles"
# purpose: "Verify resolution of TypeScript circular dependencies in providers and updater subsystems"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import re
from pathlib import Path

def test_providers_cycle_broken():
    base_dir = Path("visual_shell/open_design/apps/web/src/providers")
    if not base_dir.exists():
        return
    
    # Check that types.ts exists and defines StreamHandlers
    types_file = base_dir / "types.ts"
    assert types_file.exists(), "providers/types.ts must exist"
    assert "StreamHandlers" in types_file.read_text(encoding="utf-8")
    
    # Check that openai-compatible.ts does not import from anthropic
    openai_file = base_dir / "openai-compatible.ts"
    openai_text = openai_file.read_text(encoding="utf-8")
    assert "from './anthropic'" not in openai_text, "openai-compatible.ts must not import from anthropic.ts"
    
    # Check that api-proxy.ts does not import from anthropic
    api_proxy_file = base_dir / "api-proxy.ts"
    api_proxy_text = api_proxy_file.read_text(encoding="utf-8")
    assert "from './anthropic'" not in api_proxy_text, "api-proxy.ts must not import from anthropic.ts"

    # Check that utils/apiProtocol.ts does not import from providers/
    utils_file = Path("visual_shell/open_design/apps/web/src/utils/apiProtocol.ts")
    utils_text = utils_file.read_text(encoding="utf-8")
    assert "../providers" not in utils_text, "utils/apiProtocol.ts must not depend on providers/"

def test_updater_cycle_broken():
    updater_dir = Path("visual_shell/open_design/apps/desktop/src/main/updater")
    if not updater_dir.exists():
        return

    # Check that updater/types.ts exists
    types_file = updater_dir / "types.ts"
    assert types_file.exists(), "updater/types.ts must exist"
    
    # Check that payload.ts does not import from ../updater
    payload_file = updater_dir / "payload.ts"
    payload_text = payload_file.read_text(encoding="utf-8")
    assert 'from "../updater.js"' not in payload_text, "payload.ts must not import from ../updater.js"
    
    # Check that scheduler.ts does not import from ../updater
    scheduler_file = updater_dir / "scheduler.ts"
    scheduler_text = scheduler_file.read_text(encoding="utf-8")
    assert 'from "../updater.js"' not in scheduler_text, "scheduler.ts must not import from ../updater.js"
