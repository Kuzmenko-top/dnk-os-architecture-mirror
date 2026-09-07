---
name: patchright_assimilated
description: Undetectable browser automation, anti-bot evasion (Cloudflare, DataDome, Kasada), and zero-CDP scraping patterns via Patchright.
category: software-development
---

# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/software-development/patchright_assimilated/SKILL.md"
# purpose: "Operational skill for deploying Patchright stealth automation and bypassing anti-bot systems."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🥷 Patchright Stealth Browser Skill

## Overview
Use this skill when web tasks, competitor store analysis, or documentation retrieval encounter anti-bot protection (Cloudflare Turnstile, DataDome, Kasada, Akamai).

## When to Use
- Scraping Shopify stores, competitor pricing, or inventory when vanilla requests get Cloudflare 403 / 503.
- Accessing web applications with closed shadow DOM or anti-automation flags (`navigator.webdriver`).
- Running high-trust automated tests on live environments without triggering bot defense alerts.

## Key Rules & Invariants
1. **Never use standard vanilla Playwright when anti-bot protection is present**: Vanilla Playwright triggers `Runtime.enable` which alerts Kasada and DataDome instantly.
2. **Always configure humanized viewports and locales**: Set realistic viewports (e.g. 1920x1080), valid User-Agent, and matching timezone.
3. **Handle Closed Shadow DOM**: Use Patchright's patched XPath engine to inspect elements behind closed shadow roots.
4. **Enforce Ephemeral Browser Lifecycles**: Close browser contexts immediately after extracting data to avoid memory leaks.

---

## 🛠️ Execution Modes

### Mode A: Direct Python Context Manager & CLI Runner
For direct programmatic use inside Python modules or manual CLI probing:

```python
from core.adapters.dnk_patchright_adapter import DNKPatchrightAdapter, StealthBrowserConfig

config = StealthBrowserConfig(
    headless=True,
    viewport_width=1920,
    viewport_height=1080,
    locale="en-US",
    timezone_id="America/New_York",
)

with DNKPatchrightAdapter(config) as adapter:
    response = adapter.navigate("https://example.com")
    print(f"Status: {response.status_code}, Title: {response.title}")
    
    # Verify zero-CDP stealth
    is_bot = adapter.evaluate("navigator.webdriver")  # Returns False
    
    # Extract DOM content
    heading = adapter.extract_text("h1")
```

**CLI Execution:**
```bash
./.venv/bin/python3 scripts/stealth/patchright_scraper.py --url "https://example.com" --selector "h1" --eval "navigator.webdriver"
```

---

### Mode B: Swarm Agent Tool Invocation (`stealth.scrape`)
For specialized Swarm Workers (`dnk_shopify`, `gerych_builder`, `gerych_researcher`):

```python
from core.orchestrator.tool_executor import execute_tool

result = execute_tool("stealth.scrape", {
    "url": "https://example.com",
    "selector": "h1",
    "eval_expression": "navigator.webdriver"
})
# Returns:
# {
#   "status": "success",
#   "url": "https://example.com",
#   "status_code": 200,
#   "title": "Example Domain",
#   "turnstile_bypassed": True,
#   "datadome_bypassed": True,
#   "eval_result": False,
#   "extracted_text": "Example Domain",
#   "cookies_count": 0
# }
```

**Swarm Dispatch delegation:**
```python
dnk_swarm_dispatch(
    agent="dnk_shopify",
    task_description="Scrape product pricing from competitor store using stealth.scrape tool",
    parameters={"url": "https://competitor.com/products/widget"}
)
```
