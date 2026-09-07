# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_os_003_test_shopify_transport"
# purpose: "Unit tests for ShopifyTransport: timeouts, HTTP status mappings, rate-limit parsing, and fixture mode isolation"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from unittest.mock import patch, MagicMock
import requests

from apps.api.services.shopify_transport import HttpShopifyTransport, MockShopifyTransport


def test_mock_shopify_transport():
    transport = MockShopifyTransport()
    transport.register_route(
        "admin/api/2024-01/shop.json",
        {"shop": {"name": "Test Store"}},
        200,
        headers={"x-shopify-shop-api-call-limit": "1/40"}
    )
    
    data, code, error, headers = transport.get("dnk-e-com.myshopify.com", "/admin/api/2024-01/shop.json")
    assert code == 200
    assert error is None
    assert data == {"shop": {"name": "Test Store"}}
    assert headers is not None
    assert headers.get("x-shopify-shop-api-call-limit") == "1/40"


def test_fixture_mode_zero_network_egress(monkeypatch):
    monkeypatch.setenv("FIXTURE_MODE", "true")
    transport = HttpShopifyTransport(api_token="test-token")
    
    # Must not make network call, should return connection_error
    data, code, error, headers = transport.get("dnk-e-com.myshopify.com", "/admin/api/2024-01/shop.json")
    assert data is None
    assert code == 503
    assert error == "connection_error"


def test_http_transport_timeout():
    transport = HttpShopifyTransport(api_token="test-token")
    
    with patch("requests.get", side_effect=requests.Timeout("Request timed out")):
        data, code, error, headers = transport.get("dnk-e-com.myshopify.com", "/admin/api/2024-01/shop.json", timeout=0.1)
        assert data is None
        assert code == 504
        assert error == "timeout"


def test_http_transport_status_mappings():
    transport = HttpShopifyTransport(api_token="test-token")

    # 401 Unauthorized
    mock_resp_401 = MagicMock()
    mock_resp_401.status_code = 401
    mock_resp_401.headers = {}
    with patch("requests.get", return_value=mock_resp_401):
        data, code, error, _ = transport.get("dnk-e-com.myshopify.com", "/admin/api/2024-01/shop.json")
        assert code == 401
        assert error == "unauthorized"

    # 404 Not Found
    mock_resp_404 = MagicMock()
    mock_resp_404.status_code = 404
    mock_resp_404.headers = {}
    with patch("requests.get", return_value=mock_resp_404):
        data, code, error, _ = transport.get("dnk-e-com.myshopify.com", "/admin/api/2024-01/themes/999/assets.json")
        assert code == 404
        assert error == "not_found"

    # 429 Rate Limit
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_resp_429.headers = {"Retry-After": "2.0", "X-Shopify-Shop-Api-Call-Limit": "40/40"}
    with patch("requests.get", return_value=mock_resp_429):
        data, code, error, headers = transport.get("dnk-e-com.myshopify.com", "/admin/api/2024-01/shop.json")
        assert code == 429
        assert error == "rate_limit"
        assert headers is not None
        assert headers.get("retry-after") == "2.0"
        assert headers.get("x-shopify-shop-api-call-limit") == "40/40"

    # 500 Upstream Server Error
    mock_resp_500 = MagicMock()
    mock_resp_500.status_code = 500
    mock_resp_500.headers = {}
    with patch("requests.get", return_value=mock_resp_500):
        data, code, error, _ = transport.get("dnk-e-com.myshopify.com", "/admin/api/2024-01/shop.json")
        assert code == 500
        assert error == "upstream_5xx"


def test_zero_mutation_invariant_on_graphql():
    transport = HttpShopifyTransport(api_token="test-token")
    
    # Attempting GraphQL mutation must immediately fail closed without network call
    mutation_query = "mutation themeCreate($name: String!) { themeCreate(name: $name) { theme { id } } }"
    data, code, error, headers = transport.graphql("dnk-e-com.myshopify.com", mutation_query)
    assert code == 400
    assert error == "mutation_forbidden"
    assert data is None
