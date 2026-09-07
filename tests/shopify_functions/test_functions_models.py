# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_functions_test_functions_models"
# purpose: "Unit tests for Shopify Functions & Wasm ORM Models (DNK-ECOM-005 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.db.models import (
    ShopifyFunctionManifestModel,
    ShopifyCartTransformRuleModel,
    ShopifyDynamicDiscountRuleModel,
    ShopifyDeliveryCustomizationRuleModel,
    ShopifyPaymentCustomizationRuleModel,
    ShopifyFunctionExecutionLogModel,
)


def test_function_manifest_model():
    model = ShopifyFunctionManifestModel(
        workspace_id="ws-test-001",
        function_id="fn-cart-transform-01",
        function_title="Bundle Expansion Function",
        api_type="cart_transform",
        api_version="2024-07",
        wasm_binary_hash="sha256:abc123wasm",
        wasm_source_type="rust",
        status="active",
        input_query="query { cart { lines { id } } }",
    )
    d = model.to_dict()
    assert d["workspace_id"] == "ws-test-001"
    assert d["function_id"] == "fn-cart-transform-01"
    assert d["api_type"] == "cart_transform"
    assert d["status"] == "active"


def test_cart_transform_rule_model():
    model = ShopifyCartTransformRuleModel(
        workspace_id="ws-test-001",
        function_id="fn-cart-transform-01",
        rule_name="Starter Kit Bundle Split",
        transform_type="bundle_expand",
        trigger_criteria={"parent_variant_id": "gid://shopify/ProductVariant/101"},
        operations=[{"expand": {"title": "Component A", "quantity": 1}}],
    )
    d = model.to_dict()
    assert d["rule_name"] == "Starter Kit Bundle Split"
    assert d["transform_type"] == "bundle_expand"
    assert len(d["operations"]) == 1


def test_dynamic_discount_rule_model():
    model = ShopifyDynamicDiscountRuleModel(
        workspace_id="ws-test-001",
        function_id="fn-discounts-01",
        discount_title="Volume Tier 10+",
        discount_type="tiered_volume",
        conditions={"min_quantity": 10},
        discount_value_type="percentage",
        discount_value=15.0,
    )
    d = model.to_dict()
    assert d["discount_title"] == "Volume Tier 10+"
    assert d["discount_value"] == 15.0


def test_delivery_customization_rule_model():
    model = ShopifyDeliveryCustomizationRuleModel(
        workspace_id="ws-test-001",
        function_id="fn-delivery-01",
        rule_name="Hide Freight for Overseas",
        action="hide",
        match_conditions={"country_codes": ["US", "CA"]},
        target_delivery_methods=["Freight Express"],
    )
    d = model.to_dict()
    assert d["action"] == "hide"
    assert "Freight Express" in d["target_delivery_methods"]


def test_payment_customization_rule_model():
    model = ShopifyPaymentCustomizationRuleModel(
        workspace_id="ws-test-001",
        function_id="fn-payment-01",
        rule_name="Hide COD for High Risk",
        action="hide",
        match_conditions={"risk_level": "high"},
        target_payment_methods=["Cash on Delivery"],
    )
    d = model.to_dict()
    assert d["action"] == "hide"
    assert "Cash on Delivery" in d["target_payment_methods"]


def test_function_execution_log_model():
    model = ShopifyFunctionExecutionLogModel(
        workspace_id="ws-test-001",
        function_id="fn-cart-transform-01",
        invocation_id="inv-998877",
        api_type="cart_transform",
        input_payload={"cart": {"lines": []}},
        output_payload={"operations": []},
        execution_time_ms=1.45,
        memory_usage_bytes=1024500,
        status="success",
    )
    d = model.to_dict()
    assert d["invocation_id"] == "inv-998877"
    assert d["execution_time_ms"] == 1.45
    assert d["status"] == "success"
