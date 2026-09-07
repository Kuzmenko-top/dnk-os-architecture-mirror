#!/usr/bin/env python3
"""
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/ensure_dnk_tui_integrity.py"
# purpose: "Guarantees DNK OS TUI banner, skin, and Ukrainian tips integrity against upstream overwrites."
# canonical_source: true
# alters_files: [
#   "core/hermes_agent/hermes_cli/banner.py",
#   "core/hermes_agent/hermes_cli/skin_engine.py",
#   "~/.hermes/skins/dnk-os.yaml"
# ]
# triggers_tasks: []
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---
"""

import sys
import shutil
from pathlib import Path

DNK_HUB_ROOT = Path(__file__).resolve().parent.parent.parent
SKIN_SRC = DNK_HUB_ROOT / "core/orchestrator/agents/herich_librarian/skins/dnk-os.yaml"
USER_SKIN_DST = Path.home() / ".hermes/skins/dnk-os.yaml"


def ensure_skins():
    """Ensure dnk-os skin exists both in project and user home."""
    if SKIN_SRC.is_file():
        USER_SKIN_DST.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SKIN_SRC, USER_SKIN_DST)
    elif USER_SKIN_DST.is_file():
        SKIN_SRC.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(USER_SKIN_DST, SKIN_SRC)


def ensure_banner_patch() -> bool:
    """Verify banner.py and skin_engine.py contain canonical DNK OS enhancements."""
    banner_py = DNK_HUB_ROOT / "core/hermes_agent/hermes_cli/banner.py"
    skin_py = DNK_HUB_ROOT / "core/hermes_agent/hermes_cli/skin_engine.py"
    has_errors = False

    if banner_py.is_file():
        content = banner_py.read_text(encoding="utf-8")
        if "_is_dnk" not in content or "Google Vertex AI" not in content:
            print("❌ Error: banner.py missing DNK OS enhancements (_is_dnk / Google Vertex AI).")
            has_errors = True
        if "🛠️" in content:
            print("❌ Error: banner.py contains non-standard VS16 emoji 🛠️ that causes border desync.")
            has_errors = True

    if skin_py.is_file():
        content = skin_py.read_text(encoding="utf-8")
        if "dnk-os" not in content:
            print("❌ Error: skin_engine.py missing dnk-os built-in preset.")
            has_errors = True

    return not has_errors


if __name__ == "__main__":
    ensure_skins()
    if not ensure_banner_patch():
        print("❌ DNK OS TUI Integrity Check FAILED.")
        sys.exit(1)
    print("✅ DNK OS TUI Integrity Verified.")

