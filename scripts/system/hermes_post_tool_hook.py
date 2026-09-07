#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/hermes_post_tool_hook.py"
# purpose: "Hermes Post-Tool Hook: automatically intercepts tool errors and injects distilled self-healing solutions into context."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Antigravity"
# --- END DNK-MRH-HEADER ---

import sys
import json
import re
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
DISTILLATION_FILE = HUB_ROOT / "docs" / "scones" / "error_distillations.json"

DEFAULT_DISTILLATIONS = [
    {
        "pattern": r"(socket|network|egress|getaddrinfo|connection refused|block_network)",
        "category": "NETWORK_SOCKET_EGRESS",
        "root_cause": "Outbound socket call during isolated test environment violating zero egress invariant.",
        "solution": "Set FIXTURE_MODE=true or implement mock transport override in service constructor (_is_test_mode)."
    },
    {
        "pattern": r"(ModuleNotFoundError: No module named '(apps|services|core)\.)",
        "category": "MODULE_IMPORT_PATH",
        "root_cause": "Module exists in workspace root or sub-package but PYTHONPATH was not set or file not found.",
        "solution": "Ensure PYTHONPATH includes workspace root and relative imports use correct package syntax."
    },
    {
        "pattern": r"(404.*Not Found.*router|router.*404|404: Not Found)",
        "category": "FASTAPI_ROUTER_UNMOUNTED",
        "root_cause": "FastAPI router was created or requested but endpoint is not mounted in apps/api/main.py or missing prefix.",
        "solution": "Verify app.include_router(module.router, prefix='/api/...') in apps/api/main.py."
    },
    {
        "pattern": r"(401.*Unauthorized|Not authenticated|SecurityGateDenied|403.*Forbidden)",
        "category": "SECURITY_GATE_DENIAL",
        "root_cause": "SecurityMiddleware or SecurityGate blocked the request due to missing API key / bearer token or exempt route.",
        "solution": "Add header 'Authorization: Bearer test_token' or exempt route in apps/api/middleware/security.py."
    },
    {
        "pattern": r"(AttributeError:.*model_dump|\.dict\(\))",
        "category": "PYDANTIC_V2_MIGRATION",
        "root_cause": "Using legacy Pydantic v1 .dict() method instead of v2 .model_dump().",
        "solution": "Replace .dict() with .model_dump() across all domain model calls."
    },
    {
        "pattern": r"(SyntaxError: invalid syntax|IndentationError)",
        "category": "AST_SYNTAX_ERROR",
        "root_cause": "File contains malformed Python syntax or incorrect indentation.",
        "solution": "Run python3 -m py_compile <file> and inspect lines around the syntax error."
    }
]


def load_distillations():
    if DISTILLATION_FILE.exists():
        try:
            return json.loads(DISTILLATION_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_DISTILLATIONS


def find_remedy(error_text: str):
    kb = load_distillations()
    for item in kb:
        pat = item.get("pattern", "")
        if pat and re.search(pat, error_text, re.IGNORECASE):
            return item
    return None


def sync_canvas_live(tool_name: str, tool_input: dict, status: str, result_text: str):
    """
    Live Obsidian Canvas Control Panel Sync (Vector 1).
    Atomically updates HUD tool counters, active slice stages, and color badges.
    """
    try:
        from core.orchestrator.visual_canvas_control import VisualCanvasControlEngine
        engine = VisualCanvasControlEngine()
        engine.record_live_tool_execution(
            tool_name=tool_name,
            tool_input=tool_input,
            status=status,
            result_text=result_text,
        )
    except Exception:
        pass


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)

        payload = json.loads(raw_input)
        event_name = payload.get("hook_event_name", "")
        if event_name != "post_tool_call":
            sys.exit(0)

        tool_name = str(payload.get("tool_name") or "")
        tool_input = payload.get("tool_input") or {}
        extra = payload.get("extra", {})
        status = extra.get("status") or payload.get("status") or "success"
        result = str(extra.get("result") or payload.get("result") or "")
        error_msg = str(extra.get("error_message") or extra.get("error_type") or "")

        combined_text = f"{error_msg}\n{result}"

        # 1. Vector 1: Live Obsidian Canvas HUD & Stage Synchronization
        sync_canvas_live(tool_name, tool_input, status, combined_text)

        has_error = (status == "error") or ("Traceback (most recent call last)" in combined_text) or ("Error:" in combined_text) or ("FAILED" in combined_text and "test" in combined_text)

        if not has_error:
            sys.exit(0)

        remedy = find_remedy(combined_text)
        if remedy:
            category = remedy.get("category", "DISTILLED_ERROR")
            root_cause = remedy.get("root_cause", "Known error pattern identified in SCONES memory.")
            solution = remedy.get("solution", "Follow standard resolution protocol.")
            
            remedy_block = (
                f"\n\n⚡ [DNK OS SCONES Self-Healing Distiller Advice]\n"
                f"• Category: {category}\n"
                f"• Root Cause: {root_cause}\n"
                f"• Recommended Fix: {solution}\n"
                f"💡 Note: Do not guess blindly. Apply the recommended fix directly."
            )
            
            output = {
                "context": remedy_block
            }
            print(json.dumps(output))
            sys.exit(0)

    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
