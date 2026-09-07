# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/tools/stealth_browser_tool.py"
# purpose: "High-level Swarm Tool exposing Patchright stealth browsing and extraction to DNK Swarm Agents"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Any, Dict, Optional

from core.adapters.dnk_patchright_adapter import (
    DNKPatchrightAdapter,
    StealthBrowserConfig,
    StealthPageResponse,
)

logger = logging.getLogger("StealthBrowserTool")


def execute_stealth_scrape(
    url: str,
    selector: Optional[str] = None,
    eval_expression: Optional[str] = None,
    headless: bool = True,
    timeout_ms: int = 30000,
    mock_mode: bool = False,
) -> Dict[str, Any]:
    """
    Executes a stealth browsing action using Patchright without triggering bot protection systems.
    Designed for Swarm Agents (dnk_shopify, gerych_builder, gerych_researcher).
    """
    try:
        config = StealthBrowserConfig(
            headless=headless,
            timeout_ms=timeout_ms,
            mock_mode=mock_mode,
            viewport_width=1920,
            viewport_height=1080,
            locale="en-US",
            timezone_id="America/New_York",
        )

        with DNKPatchrightAdapter(config) as adapter:
            nav_result: StealthPageResponse = adapter.navigate(url)

            eval_res = None
            if eval_expression:
                eval_res = adapter.evaluate(eval_expression)

            extracted_text = None
            if selector:
                extracted_text = adapter.extract_text(selector)

            return {
                "status": "success",
                "url": nav_result.url,
                "status_code": nav_result.status_code,
                "title": nav_result.title,
                "execution_time_ms": nav_result.execution_time_ms,
                "turnstile_bypassed": nav_result.turnstile_bypassed,
                "datadome_bypassed": nav_result.datadome_bypassed,
                "eval_result": eval_res,
                "extracted_text": extracted_text,
                "cookies_count": len(nav_result.cookies),
                "html_preview": nav_result.html_content[:300] if nav_result.html_content else "",
            }
    except Exception as exc:
        logger.error("Stealth scrape failed for %s: %s", url, exc, exc_info=True)
        return {
            "status": "error",
            "url": url,
            "error": str(exc),
        }
