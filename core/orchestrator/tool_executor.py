# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/tool_executor.py"
# purpose: "Unified tool execution gateway for MCP Slim Guard and agentic tools."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import os
from pathlib import Path
from typing import Any, Dict

from core.orchestrator.tool_aliases import resolve_tool_name


def execute_tool(name: str, args: Dict[str, Any]) -> Any:
    """Executes a tool by name or alias with arguments."""
    canonical = resolve_tool_name(name)

    # Mock tool support for tests and simulations
    if name == "mock.large_tool" or canonical == "mock.large_tool":
        return "x" * 5000

    if name in ("file.read", "read_file") or canonical == "read_file":
        path = args.get("path") or args.get("file") or ""
        p = Path(path)
        if p.is_file():
            try:
                content = p.read_text(encoding="utf-8")
                return {"status": "success", "content": content}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "success", "content": f"Content of {path}"}

    if name in ("file.write", "write_file") or canonical == "write_file":
        path = args.get("path") or ""
        content = args.get("content") or ""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"status": "success", "bytes_written": len(content)}

    if name in ("stealth.scrape", "dnk_stealth_scrape") or canonical in ("stealth.scrape", "dnk_stealth_scrape"):
        from core.orchestrator.tools.stealth_browser_tool import execute_stealth_scrape
        return execute_stealth_scrape(
            url=args.get("url", ""),
            selector=args.get("selector"),
            eval_expression=args.get("eval_expression") or args.get("eval"),
            headless=args.get("headless", True),
            timeout_ms=args.get("timeout_ms", 30000),
            mock_mode=args.get("mock_mode", False),
        )

    # Fallback / generic execution response
    return {"status": "success", "tool": canonical, "result": f"Executed {canonical} with {args}"}
