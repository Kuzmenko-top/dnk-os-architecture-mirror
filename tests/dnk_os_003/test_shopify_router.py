# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_os_003_test_shopify_router"
# purpose: "Integration tests for FastAPI /api/shopify endpoints verifying status codes, parameters, and allowlist security"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routers.shopify import set_adapter
from apps.api.services.shopify_adapter import ShopifyAdapter
from apps.api.services.shopify_transport import MockShopifyTransport


@pytest.fixture
def test_client():
    mock_transport = MockShopifyTransport()
    # Register mock responses
    mock_transport.register_route(
        "admin/api/2024-01/shop.json",
        {"shop": {"id": 987654321, "name": "DNK-e.com Official Store", "myshopify_domain": "dnk-e-com.myshopify.com", "currency": "USD"}},
        200
    )
    mock_transport.register_route(
        "admin/api/2024-01/themes.json",
        {"themes": [{"id": 160000001, "name": "Dawn Production 2026", "role": "main", "previewable": True}]},
        200
    )
    mock_transport.register_route(
        "admin/api/2024-01/themes/160000001/assets.json",
        {"assets": [{"key": "layout/theme.liquid", "content_type": "text/x-liquid", "size": 12450}]},
        200
    )
    mock_transport.register_route(
        "admin/api/2024-01/themes/160000001/assets.json?asset[key]=layout/theme.liquid",
        {"asset": {"key": "layout/theme.liquid", "theme_id": 160000001, "value": "<html><body>{{ content_for_layout }}</body></html>"}},
        200
    )

    adapter = ShopifyAdapter(transport=mock_transport)
    set_adapter(adapter)
    return TestClient(app)


def test_router_shop_meta(test_client):
    response = test_client.get("/api/shopify/dnk-e-com.myshopify.com/meta")
    assert response.status_code == 200
    data = response.json()
    assert data["data_source"] == "live"
    assert data["data"]["name"] == "DNK-e.com Official Store"
    assert data["data"]["currency"] == "USD"


def test_router_themes_and_assets(test_client):
    # Get themes
    res_themes = test_client.get("/api/shopify/dnk-e-com.myshopify.com/themes")
    assert res_themes.status_code == 200
    themes_payload = res_themes.json()
    assert len(themes_payload["data"]) == 1
    assert themes_payload["data"][0]["name"] == "Dawn Production 2026"

    # Get assets
    res_assets = test_client.get("/api/shopify/dnk-e-com.myshopify.com/themes/160000001/assets")
    assert res_assets.status_code == 200
    assets_payload = res_assets.json()
    assert len(assets_payload["data"]) == 1
    assert assets_payload["data"][0]["key"] == "layout/theme.liquid"

    # Get asset content
    res_content = test_client.get(
        "/api/shopify/dnk-e-com.myshopify.com/themes/160000001/asset",
        params={"asset_key": "layout/theme.liquid"}
    )
    assert res_content.status_code == 200
    content_payload = res_content.json()
    assert content_payload["data"]["key"] == "layout/theme.liquid"
    assert "content_for_layout" in content_payload["data"]["value"]


def test_router_forbidden_store(test_client):
    # Store not on allowlist
    response = test_client.get("/api/shopify/unauthorized-hacker-store.com/meta")
    assert response.status_code == 403
    assert "not in the allowed list" in response.json()["detail"]


def test_router_invalid_asset_key(test_client):
    # Missing / empty asset key
    response = test_client.get(
        "/api/shopify/dnk-e-com.myshopify.com/themes/160000001/asset",
        params={"asset_key": ""}
    )
    assert response.status_code == 400
