# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_functions_test_functions_wasm_engine"
# purpose: "Unit tests for Shopify Functions Wasm Engine (DNK-ECOM-005 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.shopify_functions_wasm_engine import (
    ShopifyFunctionsWasmEngine,
    WasmExecutionResult,
)


@pytest.fixture
def wasm_engine():
    return ShopifyFunctionsWasmEngine()


def test_cart_transform_bundle_expand(wasm_engine):
    input_data = {
        "cart": {
            "lines": [
                {
                    "id": "cart-line-1",
                    "quantity": 2,
                    "merchandise": {"id": "gid://shopify/ProductVariant/bundle-starter"},
                }
            ]
        }
    }
    config = {
        "rules": [
            {
                "rule_name": "Expand Starter Bundle",
                "transform_type": "bundle_expand",
                "enabled": True,
                "trigger_criteria": {"parent_variant_id": "gid://shopify/ProductVariant/bundle-starter"},
                "operations": [
                    {"merchandise_id": "gid://shopify/ProductVariant/item-a", "quantity": 1},
                    {"merchandise_id": "gid://shopify/ProductVariant/item-b", "quantity": 2},
                ],
            }
        ]
    }

    res = wasm_engine.execute_function("cart_transform", input_data, config)
    assert res.status == "success"
    assert res.api_type == "cart_transform"
    assert len(res.output["operations"]) == 1
    expand_op = res.output["operations"][0]["expand"]
    assert expand_op["cartLineId"] == "cart-line-1"
    assert len(expand_op["expandedCartItems"]) == 2
    assert expand_op["expandedCartItems"][0]["quantity"] == 2  # 1 * 2
    assert expand_op["expandedCartItems"][1]["quantity"] == 4  # 2 * 2


def test_cart_transform_price_override(wasm_engine):
    input_data = {
        "cart": {
            "lines": [
                {
                    "id": "cart-line-promo",
                    "quantity": 1,
                    "merchandise": {"id": "gid://shopify/ProductVariant/promo-item"},
                }
            ]
        }
    }
    config = {
        "rules": [
            {
                "rule_name": "VIP Price Override",
                "transform_type": "price_override",
                "enabled": True,
                "trigger_criteria": {"parent_variant_id": "gid://shopify/ProductVariant/promo-item"},
                "operations": [{"price_override": {"fixedPricePerUnit": {"amount": "19.99"}}}],
            }
        ]
    }

    res = wasm_engine.execute_function("cart_transform", input_data, config)
    assert res.status == "success"
    assert len(res.output["operations"]) == 1
    update_op = res.output["operations"][0]["update"]
    assert update_op["cartLineId"] == "cart-line-promo"
    assert update_op["price"]["fixedPricePerUnit"]["amount"] == "19.99"


def test_dynamic_discounts_volume_tier(wasm_engine):
    input_data = {
        "cart": {
            "lines": [
                {"id": "line-1", "quantity": 5},
                {"id": "line-2", "quantity": 6},
            ]
        },
        "customer": {"tags": ["b2b", "wholesale"]},
    }
    config = {
        "rules": [
            {
                "discount_title": "Wholesale Bulk 10+",
                "enabled": True,
                "conditions": {"min_quantity": 10, "customer_tags": ["b2b"]},
                "discount_value_type": "percentage",
                "discount_value": 20.0,
            }
        ]
    }

    res = wasm_engine.execute_function("product_discounts", input_data, config)
    assert res.status == "success"
    assert len(res.output["discounts"]) == 1
    disc = res.output["discounts"][0]
    assert disc["message"] == "Wholesale Bulk 10+"
    assert disc["value"]["percentage"]["value"] == "20.0"


def test_delivery_customization_hide_and_rename(wasm_engine):
    input_data = {
        "deliveryGroups": [
            {
                "deliveryOptions": [
                    {"handle": "standard-shipping", "title": "Standard Shipping"},
                    {"handle": "freight-express", "title": "Freight Express"},
                ]
            }
        ]
    }
    config = {
        "rules": [
            {
                "rule_name": "Hide Freight",
                "action": "hide",
                "enabled": True,
                "target_delivery_methods": ["Freight Express"],
            },
            {
                "rule_name": "Rename Standard",
                "action": "rename",
                "enabled": True,
                "target_delivery_methods": ["standard-shipping"],
                "parameters": {"rename_to": "DNK Green Priority Direct"},
            },
        ]
    }

    res = wasm_engine.execute_function("delivery_customization", input_data, config)
    assert res.status == "success"
    ops = res.output["operations"]
    assert len(ops) == 2
    assert any("hide" in op and op["hide"]["deliveryOptionHandle"] == "freight-express" for op in ops)
    assert any("rename" in op and op["rename"]["title"] == "DNK Green Priority Direct" for op in ops)


def test_payment_customization_hide_gateway(wasm_engine):
    input_data = {
        "paymentMethods": [
            {"id": "pm_shopify_payments", "name": "Credit Card"},
            {"id": "pm_cod", "name": "Cash on Delivery"},
        ]
    }
    config = {
        "rules": [
            {
                "rule_name": "Hide COD",
                "action": "hide",
                "enabled": True,
                "target_payment_methods": ["Cash on Delivery"],
            }
        ]
    }

    res = wasm_engine.execute_function("payment_customization", input_data, config)
    assert res.status == "success"
    ops = res.output["operations"]
    assert len(ops) == 1
    assert ops[0]["hide"]["paymentMethodId"] == "pm_cod"


def test_order_routing_ranking(wasm_engine):
    input_data = {
        "locations": [
            {"id": "loc-warehouse-eu", "name": "Frankfurt Hub"},
            {"id": "loc-warehouse-us", "name": "New Jersey Hub"},
        ]
    }
    res = wasm_engine.execute_function("order_routing", input_data)
    assert res.status == "success"
    ranks = res.output["ranks"]
    assert len(ranks) == 2
    assert ranks[0]["locationId"] == "loc-warehouse-eu"
    assert ranks[0]["rank"] == 1


def test_unsupported_api_type(wasm_engine):
    res = wasm_engine.execute_function("invalid_unknown_target", {})
    assert res.status == "error"
    assert "Unsupported Shopify Function API target" in res.error_message


def test_custom_handler_registration(wasm_engine):
    def custom_handler(inp, cfg):
        return {"custom_result": inp.get("x", 0) * 2}

    wasm_engine.register_custom_handler("custom_math_func", custom_handler)
    res = wasm_engine.execute_function("custom_math_func", {"x": 21})
    assert res.status == "success"
    assert res.output["custom_result"] == 42
