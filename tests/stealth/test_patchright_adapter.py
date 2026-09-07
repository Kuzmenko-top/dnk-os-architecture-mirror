# --- DNK-MRH-HEADER ---
# mrh_id: "tests/stealth/test_patchright_adapter.py"
# purpose: "Unit and integration tests for DNK Patchright stealth browser adapter"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from core.adapters.dnk_patchright_adapter import (
    DNKPatchrightAdapter,
    StealthBrowserConfig,
    StealthPageResponse,
    PATCHRIGHT_AVAILABLE
)

def test_stealth_browser_config_defaults():
    config = StealthBrowserConfig()
    assert config.headless is True
    assert config.stealth_mode is True
    assert config.viewport_width == 1920
    assert config.viewport_height == 1080
    assert config.locale == "en-US"
    assert config.mock_mode is False

def test_stealth_chromium_args_hygiene():
    adapter = DNKPatchrightAdapter()
    args = adapter.get_stealth_chromium_args()
    assert "--disable-blink-features=AutomationControlled" in args
    assert "--enable-automation" not in args
    assert "--no-first-run" in args

def test_patchright_lifecycle_mock():
    config = StealthBrowserConfig(mock_mode=True)
    adapter = DNKPatchrightAdapter(config)
    assert adapter.is_running is False
    adapter.start()
    assert adapter.is_running is True
    adapter.stop()
    assert adapter.is_running is False

def test_patchright_stealth_navigation_mock():
    config = StealthBrowserConfig(mock_mode=True)
    adapter = DNKPatchrightAdapter(config)
    response = adapter.navigate("https://example.com/protected-store")
    assert isinstance(response, StealthPageResponse)
    assert response.status_code == 200
    assert response.turnstile_bypassed is True
    assert response.datadome_bypassed is True
    assert "Stealth Captured" in response.title

def test_patchright_zero_cdp_evaluation_mock():
    config = StealthBrowserConfig(mock_mode=True)
    adapter = DNKPatchrightAdapter(config)
    adapter.start()
    webdriver_flag = adapter.evaluate("navigator.webdriver")
    assert webdriver_flag is False
    text = adapter.extract_text("#content")
    assert "Bypassed anti-bot verification" in text
    adapter.stop()

@pytest.mark.skipif(not PATCHRIGHT_AVAILABLE, reason="Live patchright-python is not installed")
def test_patchright_live_browser_evaluation():
    config = StealthBrowserConfig(headless=True, mock_mode=False)
    with DNKPatchrightAdapter(config) as adapter:
        assert adapter.is_running is True
        assert adapter._is_live is True
        
        # Navigate to a blank page
        resp = adapter.navigate("about:blank")
        assert resp.status_code == 200
        
        # In live Patchright with zero-CDP, navigator.webdriver is strictly False
        webdriver_flag = adapter.evaluate("navigator.webdriver")
        assert webdriver_flag is False
        
        # Evaluate math & DOM
        math_eval = adapter.evaluate("1 + 1")
        assert math_eval == 2


def test_stealth_browser_tool_execution():
    from core.orchestrator.tools.stealth_browser_tool import execute_stealth_scrape
    from core.orchestrator.tool_executor import execute_tool

    # Test via execute_stealth_scrape
    res = execute_stealth_scrape("https://example.com", mock_mode=True)
    assert res["status"] == "success"
    assert res["url"] == "https://example.com"
    assert res["turnstile_bypassed"] is True

    # Test via tool executor alias
    alias_res = execute_tool("stealth.scrape", {"url": "https://example.com", "mock_mode": True})
    assert alias_res["status"] == "success"
    assert alias_res["status_code"] == 200

