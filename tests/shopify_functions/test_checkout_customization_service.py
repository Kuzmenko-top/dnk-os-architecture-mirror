# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_functions_test_checkout_customization_service"
# purpose: "Unit tests for Delivery & Payment Customization Service (DNK-ECOM-005 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.shopify_checkout_customization_service import ShopifyCheckoutCustomizationService


@pytest.fixture
def custom_service():
    return ShopifyCheckoutCustomizationService()


def test_delivery_customization_operations(custom_service):
    ws = "ws-custom-01"
    custom_service.create_hide_delivery_option_rule(
        workspace_id=ws,
        rule_name="Hide Freight for Retail",
        target_delivery_methods=["Freight Super Heavy"],
    )
    custom_service.create_rename_delivery_option_rule(
        workspace_id=ws,
        rule_name="Brand Air Shipping",
        target_delivery_method="standard-air",
        rename_to="DNK Green Aero Express",
    )

    delivery_input = {
        "deliveryGroups": [
            {
                "deliveryOptions": [
                    {"handle": "standard-air", "title": "Standard Air"},
                    {"handle": "freight-heavy", "title": "Freight Super Heavy"},
                ]
            }
        ]
    }

    res = custom_service.evaluate_delivery_customization(ws, delivery_input)
    assert res.status == "success"
    ops = res.output["operations"]
    assert len(ops) == 2
    assert any("hide" in op and op["hide"]["deliveryOptionHandle"] == "freight-heavy" for op in ops)
    assert any("rename" in op and op["rename"]["title"] == "DNK Green Aero Express" for op in ops)


def test_payment_customization_operations(custom_service):
    ws = "ws-custom-02"
    custom_service.create_hide_payment_gateway_rule(
        workspace_id=ws,
        rule_name="Hide Cash On Delivery",
        target_payment_methods=["Cash On Delivery", "pm_cod_gateway"],
    )

    payment_input = {
        "paymentMethods": [
            {"id": "pm_shopify_payments", "name": "Credit Card"},
            {"id": "pm_cod_gateway", "name": "Cash On Delivery"},
        ]
    }

    res = custom_service.evaluate_payment_customization(ws, payment_input)
    assert res.status == "success"
    ops = res.output["operations"]
    assert len(ops) == 1
    assert ops[0]["hide"]["paymentMethodId"] == "pm_cod_gateway"
