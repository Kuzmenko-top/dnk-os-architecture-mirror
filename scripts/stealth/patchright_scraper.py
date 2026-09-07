# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/stealth/patchright_scraper.py"
# purpose: "Canonical CLI runner and context-manager utility for stealth Patchright scraping"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import argparse
import json
import sys
from typing import Optional

from core.adapters.dnk_patchright_adapter import DNKPatchrightAdapter, StealthBrowserConfig


def scrape_target(
    url: str,
    selector: Optional[str] = None,
    eval_expression: Optional[str] = None,
    headless: bool = True,
    timeout_ms: int = 30000,
    mock_mode: bool = False,
) -> dict:
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
        response = adapter.navigate(url)

        eval_result = None
        if eval_expression:
            eval_result = adapter.evaluate(eval_expression)

        extracted_text = None
        if selector:
            extracted_text = adapter.extract_text(selector)

        return {
            "url": response.url,
            "status_code": response.status_code,
            "title": response.title,
            "execution_time_ms": response.execution_time_ms,
            "turnstile_bypassed": response.turnstile_bypassed,
            "datadome_bypassed": response.datadome_bypassed,
            "eval_result": eval_result,
            "extracted_text": extracted_text,
            "cookies_count": len(response.cookies),
            "html_preview": response.html_content[:300] if response.html_content else "",
        }


def main():
    parser = argparse.ArgumentParser(description="DNK OS Stealth Patchright Browser Scraper")
    parser.add_argument("--url", required=True, help="Target URL to inspect or scrape")
    parser.add_argument("--selector", help="DOM selector to extract text from")
    parser.add_argument("--eval", dest="eval_expression", help="JavaScript expression to evaluate")
    parser.add_argument("--headed", action="store_true", help="Launch in visible browser window")
    parser.add_argument("--mock", action="store_true", help="Force mock mode")
    parser.add_argument("--timeout", type=int, default=30000, help="Navigation timeout in ms")
    parser.add_argument("--json", action="store_true", help="Output pure JSON")

    args = parser.parse_args()

    result = scrape_target(
        url=args.url,
        selector=args.selector,
        eval_expression=args.eval_expression,
        headless=not args.headed,
        timeout_ms=args.timeout,
        mock_mode=args.mock,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print("🎯 DNK OS Stealth Patchright Browser Result")
        print("=" * 60)
        print(f"URL: {result['url']}")
        print(f"Status: {result['status_code']}")
        print(f"Title: {result['title']}")
        print(f"Time: {result['execution_time_ms']} ms")
        print(f"Turnstile Bypassed: {result['turnstile_bypassed']}")
        print(f"DataDome Bypassed: {result['datadome_bypassed']}")
        if result["eval_result"] is not None:
            print(f"Eval Result: {result['eval_result']}")
        if result["extracted_text"] is not None:
            print(f"Extracted Text: {result['extracted_text']}")
        print(f"Cookies Count: {result['cookies_count']}")
        print("=" * 60)


if __name__ == "__main__":
    main()
