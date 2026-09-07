# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_os_003_test_shopify_adapter"
# purpose: "Unit & regression tests for ShopifyAdapter: normalization, caching TTL, fallback chain, and store allowlist"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import os
import json
import pytest
from apps.api.services.shopify_adapter import ShopifyAdapter
from apps.api.services.shopify_transport import MockShopifyTransport


@pytest.fixture
def mock_fixtures():
    base_dir = os.path.dirname(__file__)
    fixtures_dir = os.path.join(base_dir, "fixtures")

    with open(os.path.join(fixtures_dir, "shop_meta.json"), "r") as f:
        shop_raw = json.load(f)
    with open(os.path.join(fixtures_dir, "themes_list.json"), "r") as f:
        themes_raw = json.load(f)
    with open(os.path.join(fixtures_dir, "theme_assets.json"), "r") as f:
        assets_raw = json.load(f)
    with open(os.path.join(fixtures_dir, "asset_content.json"), "r") as f:
        asset_content_raw = json.load(f)

    return {
        "shop": shop_raw,
        "themes": themes_raw,
        "assets": assets_raw,
        "asset_content": asset_content_raw
    }


def test_store_allowlist_security():
    adapter = ShopifyAdapter()
    
    # Store not in allowlist must be immediately rejected with 403 / forbidden_store
    result = adapter.get_shop_meta("malicious-store.com")
    assert result.error_code == "forbidden_store"
    assert result.data is None
    assert result.data_source == "live"


def test_get_shop_meta_live_and_caching(mock_fixtures):
    mock_transport = MockShopifyTransport()
    mock_transport.register_route("admin/api/2024-01/shop.json", mock_fixtures["shop"], 200)

    adapter = ShopifyAdapter(transport=mock_transport)
    
    # First call: Live
    res1 = adapter.get_shop_meta("dnk-e-com.myshopify.com")
    assert res1.data_source == "live"
    assert res1.error_code is None
    assert isinstance(res1.data, dict)
    assert res1.data["name"] == "DNK-e.com Official Store"
    assert res1.data["currency"] == "USD"
    assert mock_transport.call_count == 1

    # Second call: Cache
    res2 = adapter.get_shop_meta("dnk-e-com.myshopify.com")
    assert res2.data_source == "cache"
    assert isinstance(res2.data, dict)
    assert res2.data["name"] == "DNK-e.com Official Store"
    assert mock_transport.call_count == 1  # No extra network call


def test_get_themes_and_theme_assets(mock_fixtures):
    mock_transport = MockShopifyTransport()
    mock_transport.register_route("admin/api/2024-01/themes.json", mock_fixtures["themes"], 200)
    mock_transport.register_route("admin/api/2024-01/themes/160000001/assets.json", mock_fixtures["assets"], 200)

    adapter = ShopifyAdapter(transport=mock_transport)

    # Fetch themes
    res_themes = adapter.get_themes("dnk-e-com.myshopify.com")
    assert res_themes.data_source == "live"
    assert isinstance(res_themes.data, list)
    assert len(res_themes.data) == 3
    assert res_themes.data[0]["role"] == "main"
    assert res_themes.data[0]["name"] == "Dawn Production 2026"

    # Fetch theme assets
    res_assets = adapter.get_theme_assets("dnk-e-com.myshopify.com", 160000001)
    assert res_assets.data_source == "live"
    assert isinstance(res_assets.data, list)
    assert len(res_assets.data) == 4
    assert res_assets.data[0]["key"] == "layout/theme.liquid"


def test_get_asset_content(mock_fixtures):
    mock_transport = MockShopifyTransport()
    mock_transport.register_route(
        "admin/api/2024-01/themes/160000001/assets.json?asset[key]=layout/theme.liquid",
        mock_fixtures["asset_content"],
        200
    )

    adapter = ShopifyAdapter(transport=mock_transport)

    # Empty asset key test
    res_empty = adapter.get_asset_content("dnk-e-com.myshopify.com", 160000001, "")
    assert res_empty.error_code == "invalid_asset"

    # Valid asset content fetch
    res = adapter.get_asset_content("dnk-e-com.myshopify.com", 160000001, "layout/theme.liquid")
    assert res.data_source == "live"
    assert res.error_code is None
    assert isinstance(res.data, dict)
    assert res.data["key"] == "layout/theme.liquid"
    assert "{{ content_for_layout }}" in res.data["value"]


def test_fallback_chain_fixture_fallback_when_allowed(mock_fixtures):
    mock_transport = MockShopifyTransport()
    # No routes registered -> 404 / upstream failure
    adapter = ShopifyAdapter(transport=mock_transport)

    # Without fixture fallback allowed -> returns error
    res_no_fb = adapter.get_shop_meta("dnk-e-com.myshopify.com", allow_fixture_fallback=False)
    assert res_no_fb.error_code in ("not_found", "upstream_5xx")
    assert res_no_fb.data is None

    # With fixture fallback allowed -> returns fixture
    res_fb = adapter.get_shop_meta("dnk-e-com.myshopify.com", allow_fixture_fallback=True)
    assert res_fb.data_source == "fixture"
    assert res_fb.error_code is None
    assert isinstance(res_fb.data, dict)
    assert res_fb.data["name"] == "DNK-e.com Official Store"


def test_fixture_mode_deterministic_execution(monkeypatch):
    monkeypatch.setenv("FIXTURE_MODE", "true")
    adapter = ShopifyAdapter()

    res_shop = adapter.get_shop_meta("dnk-e-com.myshopify.com")
    assert res_shop.data_source == "fixture"
    assert isinstance(res_shop.data, dict)

    res_themes = adapter.get_themes("dnk-e-com.myshopify.com")
    assert res_themes.data_source == "fixture"
    assert isinstance(res_themes.data, list)
    assert len(res_themes.data) == 3

    res_assets = adapter.get_theme_assets("dnk-e-com.myshopify.com", 160000001)
    assert res_assets.data_source == "fixture"
    assert isinstance(res_assets.data, list)
    assert len(res_assets.data) >= 4

    res_content = adapter.get_asset_content("dnk-e-com.myshopify.com", 160000001, "layout/theme.liquid")
    assert res_content.data_source == "fixture"
    assert isinstance(res_content.data, dict)
    assert "content_for_layout" in res_content.data["value"]
