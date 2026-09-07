# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_functions_test_dynamic_discount_service"
# purpose: "Unit tests for Shopify Dynamic Discount Service (DNK-ECOM-005 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.shopify_dynamic_discount_service import ShopifyDynamicDiscountService


@pytest.fixture
def discount_service():
    return ShopifyDynamicDiscountService()


def test_volume_discount_flow(discount_service):
    ws = "ws-disc-01"
    discount_service.create_volume_tier_discount(
        workspace_id=ws,
        discount_title="Buy 5+ Get 15% Off",
        min_quantity=5,
        percentage_off=15.0,
    )

    cart_input = {
        "cart": {
            "lines": [
                {"id": "line-a", "quantity": 3},
                {"id": "line-b", "quantity": 3},
            ]
        }
    }

    res = discount_service.evaluate_discounts(ws, cart_input)
    assert res.status == "success"
    assert len(res.output["discounts"]) == 1
    assert res.output["discounts"][0]["message"] == "Buy 5+ Get 15% Off"
    assert res.output["discounts"][0]["value"]["percentage"]["value"] == "15.0"


def test_b2b_discount_flow(discount_service):
    ws = "ws-disc-02"
    discount_service.create_b2b_wholesale_discount(
        workspace_id=ws,
        discount_title="B2B Direct 25% Off",
        percentage_off=25.0,
        customer_tags=["b2b_gold"],
    )

    cart_matching = {
        "cart": {"lines": [{"id": "line-item", "quantity": 1}]},
        "customer": {"tags": ["b2b_gold", "wholesale"]},
    }
    res_match = discount_service.evaluate_discounts(ws, cart_matching)
    assert res_match.status == "success"
    assert len(res_match.output["discounts"]) == 1

    cart_non_matching = {
        "cart": {"lines": [{"id": "line-item", "quantity": 1}]},
        "customer": {"tags": ["retail_consumer"]},
    }
    res_no = discount_service.evaluate_discounts(ws, cart_non_matching)
    assert res_no.status == "success"
    assert len(res_no.output["discounts"]) == 0


def test_vip_fixed_discount_flow(discount_service):
    ws = "ws-disc-03"
    discount_service.create_vip_fixed_discount(
        workspace_id=ws,
        discount_title="VIP Loyalty $50 Credit",
        fixed_amount=50.0,
        customer_tags=["vip"],
    )

    cart_input = {
        "cart": {"lines": [{"id": "line-vip", "quantity": 1}]},
        "customer": {"tags": ["vip"]},
    }
    res = discount_service.evaluate_discounts(ws, cart_input)
    assert res.status == "success"
    assert len(res.output["discounts"]) == 1
    assert res.output["discounts"][0]["value"]["fixedAmount"]["amount"] == "50.0"


def test_discount_manifest(discount_service):
    ws = "ws-disc-01"
    manifest = discount_service.generate_function_manifest(ws, "fn-disc")
    assert manifest["api_version"] == "2024-07"
    assert manifest["app_key"] == "dnk_shopify_functions_discounts"
