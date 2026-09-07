# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_product_normalization"
# purpose: "Unit tests for Shopify product normalization contract (DNK-SHOPIFY-PILOT-001)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

import pytest
from plugins.dnk_shopify_sync.plugin import DNKShopifySyncPlugin


def test_normalization_deterministic_output(valid_shopify_product_payload):
    plugin = DNKShopifySyncPlugin()
    plugin.initialize()

    res1 = plugin.normalize_product_payload(valid_shopify_product_payload)
    res2 = plugin.normalize_product_payload(valid_shopify_product_payload)

    assert res1 == res2
    assert res1["plugin_id"] == "dnk-shopify-sync"
    assert res1["mode"] == "dry_run"
    assert res1["operation"] == "product_sync_preview"
    assert res1["source_product_id"] == "gid://shopify/Product/1001"
    assert res1["mutations"] == []
    assert res1["write_performed"] is False

    norm = res1["normalized"]
    assert norm["external_id"] == "1001"
    assert norm["title"] == "ReBurn Sample Product"
    assert norm["handle"] == "reburn-sample-product"
    assert norm["status"] == "active"
    assert norm["sku"] == "RB-TEST-001"
    assert norm["price_minor"] == 4900
    assert norm["currency"] == "USD"
    assert norm["inventory_quantity"] == 3
    assert norm["tags"] == ["pilot", "reburn"]


def test_normalization_price_minor_units():
    plugin = DNKShopifySyncPlugin()
    assert plugin.parse_price_minor("49.00") == 4900
    assert plugin.parse_price_minor("129.99") == 12999
    assert plugin.parse_price_minor(15) == 1500
    assert plugin.parse_price_minor("0.05") == 5


def test_normalization_tag_deduplication_and_sorting(valid_shopify_product_payload):
    plugin = DNKShopifySyncPlugin()
    payload = dict(valid_shopify_product_payload)
    payload["tags"] = ["zebra", "pilot", "reburn", "pilot", "alpha"]

    res = plugin.normalize_product_payload(payload)
    assert res["normalized"]["tags"] == ["alpha", "pilot", "reburn", "zebra"]


def test_normalization_missing_fields_raises_error():
    plugin = DNKShopifySyncPlugin()
    invalid_payload = {
        "id": "gid://shopify/Product/1001",
        # missing title, handle, status
        "variants": []
    }
    with pytest.raises(ValueError, match="Missing required Shopify product fields"):
        plugin.normalize_product_payload(invalid_payload)
