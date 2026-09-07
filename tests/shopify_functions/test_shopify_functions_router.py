# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_functions_test_shopify_functions_router"
# purpose: "Integration tests for Shopify Functions FastAPI router (DNK-ECOM-005 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_functions_health():
    response = client.get("/api/v1/shopify/functions/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "cart_transform" in data["supported_targets"]


def test_cart_transform_rules_and_evaluation():
    # 1. Create Bundle Expansion Rule
    payload = {
        "workspace_id": "ws-router-test",
        "rule_name": "Mega Bundle Pack",
        "parent_variant_id": "gid://shopify/ProductVariant/bundle-99",
        "components": [
            {"variant_id": "gid://shopify/ProductVariant/comp-1", "quantity": 2},
            {"variant_id": "gid://shopify/ProductVariant/comp-2", "quantity": 1},
        ],
        "min_quantity": 1,
    }
    create_res = client.post("/api/v1/shopify/functions/cart-transform/rules/bundle", json=payload)
    assert create_res.status_code == 200
    rule_data = create_res.json()
    assert rule_data["status"] == "success"
    assert rule_data["rule"]["rule_name"] == "Mega Bundle Pack"

    # 2. List Rules
    list_res = client.get("/api/v1/shopify/functions/cart-transform/rules?workspace_id=ws-router-test")
    assert list_res.status_code == 200
    rules = list_res.json()["rules"]
    assert len(rules) >= 1

    # 3. Evaluate Cart Transform
    eval_payload = {
        "cart": {
            "lines": [
                {
                    "id": "line-1",
                    "quantity": 2,
                    "merchandise": {"id": "gid://shopify/ProductVariant/bundle-99"},
                }
            ]
        }
    }
    eval_res = client.post(
        "/api/v1/shopify/functions/cart-transform/evaluate?workspace_id=ws-router-test",
        json=eval_payload,
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["status"] == "success"
    assert len(eval_data["output"]["operations"]) >= 1

    # 4. Manifest
    manifest_res = client.get("/api/v1/shopify/functions/cart-transform/manifest?workspace_id=ws-router-test")
    assert manifest_res.status_code == 200
    assert manifest_res.json()["api_version"] == "2024-07"


def test_discount_rules_and_evaluation():
    # 1. Create Tiered Volume Rule
    payload = {
        "workspace_id": "ws-router-test",
        "discount_title": "Bulk Discount 20%",
        "discount_type": "tiered_volume",
        "min_quantity": 5,
        "percentage_off": 20.0,
    }
    create_res = client.post("/api/v1/shopify/functions/discounts/rules", json=payload)
    assert create_res.status_code == 200
    assert create_res.json()["status"] == "success"

    # 2. List Rules
    list_res = client.get("/api/v1/shopify/functions/discounts/rules?workspace_id=ws-router-test")
    assert list_res.status_code == 200
    assert len(list_res.json()["rules"]) >= 1

    # 3. Evaluate Discounts
    cart_payload = {
        "cart": {
            "lines": [
                {"id": "line-1", "quantity": 10, "cost": {"amountPerQuantity": {"amount": "100.0"}}}
            ]
        }
    }
    eval_res = client.post(
        "/api/v1/shopify/functions/discounts/evaluate?workspace_id=ws-router-test",
        json=cart_payload,
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["status"] == "success"
    assert len(eval_data["output"]["discounts"]) >= 1


def test_delivery_and_payment_customization():
    # 1. Create Delivery Rule
    delivery_payload = {
        "workspace_id": "ws-router-test",
        "rule_name": "Hide Freight",
        "action": "hide",
        "target_delivery_methods": ["Freight Cargo"],
    }
    deliv_res = client.post("/api/v1/shopify/functions/delivery/rules", json=delivery_payload)
    assert deliv_res.status_code == 200

    # 2. Evaluate Delivery
    deliv_eval_res = client.post(
        "/api/v1/shopify/functions/delivery/evaluate?workspace_id=ws-router-test",
        json={
            "deliveryCustomization": {
                "deliveryOptions": [
                    {"handle": "Freight Cargo", "title": "Freight Cargo"},
                    {"handle": "Standard Express", "title": "Standard Express"},
                ]
            }
        },
    )
    assert deliv_eval_res.status_code == 200
    assert len(deliv_eval_res.json()["output"]["operations"]) == 1

    # 3. Create Payment Rule
    payment_payload = {
        "workspace_id": "ws-router-test",
        "rule_name": "Hide COD",
        "target_payment_methods": ["Cash On Delivery"],
    }
    pay_res = client.post("/api/v1/shopify/functions/payment/rules", json=payment_payload)
    assert pay_res.status_code == 200

    # 4. Evaluate Payment
    pay_eval_res = client.post(
        "/api/v1/shopify/functions/payment/evaluate?workspace_id=ws-router-test",
        json={
            "paymentCustomization": {
                "paymentMethods": [
                    {"id": "pm-1", "name": "Cash On Delivery"},
                    {"id": "pm-2", "name": "Credit Card"},
                ]
            }
        },
    )
    assert pay_eval_res.status_code == 200
    assert len(pay_eval_res.json()["output"]["operations"]) == 1


def test_generic_evaluate_endpoint():
    req_body = {
        "workspace_id": "ws-router-test",
        "api_type": "order_routing",
        "input_payload": {"fulfillmentGroups": [{"id": "grp-1"}]},
    }
    res = client.post("/api/v1/shopify/functions/evaluate", json=req_body)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["api_type"] == "order_routing"
