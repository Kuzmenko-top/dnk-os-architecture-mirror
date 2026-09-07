# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_functions_test_cart_transform_service"
# purpose: "Unit tests for Shopify Cart Transform Service (DNK-ECOM-005 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.shopify_cart_transform_service import ShopifyCartTransformService


@pytest.fixture
def service():
    return ShopifyCartTransformService()


def test_bundle_expansion_flow(service):
    ws = "ws-client-01"
    service.create_bundle_expansion_rule(
        workspace_id=ws,
        rule_name="Deluxe Kit Split",
        parent_variant_id="gid://shopify/ProductVariant/bundle-deluxe",
        components=[
            {"variant_id": "gid://shopify/ProductVariant/comp-1", "quantity": 1},
            {"variant_id": "gid://shopify/ProductVariant/comp-2", "quantity": 2},
        ],
    )

    rules = service.list_rules(ws)
    assert len(rules) == 1
    assert rules[0]["rule_name"] == "Deluxe Kit Split"

    cart_input = {
        "cart": {
            "lines": [
                {
                    "id": "line-deluxe",
                    "quantity": 3,
                    "merchandise": {"id": "gid://shopify/ProductVariant/bundle-deluxe"},
                }
            ]
        }
    }

    res = service.evaluate_cart_transformation(ws, cart_input)
    assert res.status == "success"
    assert len(res.output["operations"]) == 1
    expand = res.output["operations"][0]["expand"]
    assert expand["cartLineId"] == "line-deluxe"
    assert len(expand["expandedCartItems"]) == 2
    assert expand["expandedCartItems"][0]["quantity"] == 3
    assert expand["expandedCartItems"][1]["quantity"] == 6


def test_price_override_flow(service):
    ws = "ws-client-02"
    service.create_price_override_rule(
        workspace_id=ws,
        rule_name="Flash Sale Price",
        target_variant_id="gid://shopify/ProductVariant/flash-item",
        fixed_price=9.99,
    )

    cart_input = {
        "cart": {
            "lines": [
                {
                    "id": "line-flash",
                    "quantity": 1,
                    "merchandise": {"id": "gid://shopify/ProductVariant/flash-item"},
                }
            ]
        }
    }

    res = service.evaluate_cart_transformation(ws, cart_input)
    assert res.status == "success"
    update = res.output["operations"][0]["update"]
    assert update["price"]["fixedPricePerUnit"]["amount"] == "9.99"


def test_generate_manifest(service):
    ws = "ws-client-01"
    manifest = service.generate_function_manifest(ws, "fn-001")
    assert manifest["api_version"] == "2024-07"
    assert manifest["app_key"] == "dnk_shopify_functions_cart_transform"
    assert len(manifest["targets"]) == 1
