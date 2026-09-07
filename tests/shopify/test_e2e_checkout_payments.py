# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_e2e_checkout_payments"
# purpose: "End-to-End API Integration tests for Shopify Checkout UI Extensions, Payment Gateways, Payment Intents, 3DS, Upsells & Webhooks (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import hashlib
import hmac
import base64
import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers.shopify_checkout_payments import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_e2e_checkout_extension_flow(client):
    workspace_id = f"ws_{uuid.uuid4().hex[:8]}"

    # 1. Create extension config
    payload = {
        "workspace_id": workspace_id,
        "extension_name": "Gift Message & Delivery Note",
        "shopify_app_id": "app_test_123",
        "extension_type": "checkout_ui",
        "target_placement": "purchase.checkout.shipping-option-list.render-after",
        "custom_fields": [
            {
                "key": "gift_wrap",
                "label": "Add Gift Wrap",
                "field_type": "checkbox",
                "required": False,
                "default_value": False,
            },
            {
                "key": "gift_message",
                "label": "Gift Message",
                "field_type": "text",
                "required": False,
                "max_length": 150,
            },
        ],
    }
    resp = client.post("/api/v1/shopify/checkout-extensions", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    config_id = data["id"]
    assert data["extension_name"] == "Gift Message & Delivery Note"

    # 2. Get extension config
    resp = client.get(f"/api/v1/shopify/checkout-extensions/{config_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == config_id

    # 3. Generate Manifest
    resp = client.get(f"/api/v1/shopify/checkout-extensions/{config_id}/manifest")
    assert resp.status_code == 200
    manifest = resp.json()
    assert manifest["name"] == "Gift Message & Delivery Note"
    assert manifest["api_version"] == "2024-07"

    # 4. Generate React / TSX Code
    resp = client.get(f"/api/v1/shopify/checkout-extensions/{config_id}/code")
    assert resp.status_code == 200
    code = resp.json()["code"]
    assert "reactExtension" in code
    assert "gift_wrap" in code
    assert "gift_message" in code

    # 5. Validate Payload
    valid_resp = client.post(
        "/api/v1/shopify/checkout-extensions/validate-payload",
        json={
            "config_id": config_id,
            "submitted_fields": {
                "gift_wrap": True,
                "gift_message": "Happy Birthday!",
            },
        },
    )
    assert valid_resp.status_code == 200
    val_data = valid_resp.json()
    assert val_data["is_valid"] is True
    assert val_data["sanitized_values"]["gift_wrap"] is True


def test_e2e_payment_gateway_registration_and_testing(client):
    workspace_id = f"ws_{uuid.uuid4().hex[:8]}"

    # Register Stripe Gateway
    resp = client.post(
        "/api/v1/shopify/payment-gateways",
        json={
            "workspace_id": workspace_id,
            "gateway_type": "stripe",
            "gateway_name": "Primary Stripe USD",
            "credentials": {
                "secret_key": "sk_test_" + "mockTestStripeSecretKeyForTestingOnly",
                "publishable_key": "pk_test_51MockPubkeyStripe",
                "webhook_secret": "whsec_mockTestSecret123",
            },
            "supported_methods": ["card", "apple_pay", "google_pay"],
            "is_test_mode": True,
            "enabled": True,
        },
    )
    assert resp.status_code == 200, resp.text
    gw_data = resp.json()
    gateway_id = gw_data["id"]
    assert "..." in gw_data["credentials"]["secret_key"]

    # Test Gateway Connection
    resp = client.post(
        "/api/v1/shopify/payment-gateways/test-connection",
        json={"gateway_id": gateway_id},
    )
    assert resp.status_code == 200
    conn_result = resp.json()
    assert conn_result["is_connected"] is True
    assert conn_result["gateway_type"] == "stripe"


def test_e2e_payment_intent_lifecycle_with_3ds_and_refund(client):
    workspace_id = f"ws_{uuid.uuid4().hex[:8]}"
    order_id = f"order_{uuid.uuid4().hex[:6]}"

    # 1. Create Payment Intent requiring 3DS SCA
    resp = client.post(
        "/api/v1/shopify/payment-intents",
        json={
            "workspace_id": workspace_id,
            "order_id": order_id,
            "gateway_type": "stripe",
            "amount_cents": 12500,
            "currency": "USD",
            "customer_email": "buyer@example.com",
            "require_3ds": True,
        },
    )
    assert resp.status_code == 200, resp.text
    intent = resp.json()
    intent_id = intent["id"]
    assert intent["status"] == "requires_action"
    assert intent["three_d_secure_state"]["status"] == "challenge_required"
    assert intent["three_d_secure_state"]["challenge_url"] is not None

    # 2. Complete 3DS Challenge successfully
    resp = client.post(
        f"/api/v1/shopify/payment-intents/{intent_id}/3ds-challenge",
        json={"authentication_status": "authenticated"},
    )
    assert resp.status_code == 200
    intent_auth = resp.json()
    assert intent_auth["status"] == "succeeded"
    assert intent_auth["three_d_secure_state"]["status"] == "authenticated"

    # 3. Partial Refund
    resp = client.post(
        f"/api/v1/shopify/payment-intents/{intent_id}/refund",
        json={
            "amount_cents": 5000,
            "reason": "requested_by_customer",
            "note": "Partial item return",
        },
    )
    assert resp.status_code == 200
    refund_res = resp.json()
    assert refund_res["is_full_refund"] is False
    assert refund_res["payment_intent"]["status"] == "partially_refunded"
    assert refund_res["payment_intent"]["amount_refunded_cents"] == 5000


def test_e2e_post_purchase_upsell_flow(client):
    workspace_id = f"ws_{uuid.uuid4().hex[:8]}"

    # 1. Validate Liquid AST syntax
    valid_liquid = "{% if customer.tags contains 'VIP' %}Special VIP Deal!{% endif %}"
    resp = client.post(
        "/api/v1/shopify/upsell/validate-liquid",
        json={"template": valid_liquid},
    )
    assert resp.status_code == 200
    assert resp.json()["is_valid"] is True

    # 2. Create Upsell Offer
    resp = client.post(
        "/api/v1/shopify/upsell/offers",
        json={
            "workspace_id": workspace_id,
            "offer_name": "Premium Leather Care Kit",
            "target_product_id": "prod_leather_care",
            "target_variant_id": "var_leather_care_01",
            "original_price_cents": 4000,
            "discount_type": "percentage",
            "discount_value": 25.0,  # 25% OFF -> 3000 cents
            "countdown_seconds": 180,
            "triggers": {
                "min_order_cents": 5000,
                "included_product_ids": ["prod_boots_123"],
            },
            "priority": 10,
        },
    )
    assert resp.status_code == 200, resp.text
    offer = resp.json()
    offer_id = offer["id"]
    assert offer["calculated_price_cents"] == 3000

    # 3. Evaluate matching upsell
    resp = client.post(
        "/api/v1/shopify/upsell/evaluate",
        json={
            "workspace_id": workspace_id,
            "order_total_cents": 8500,
            "cart_product_ids": ["prod_boots_123"],
            "currency": "USD",
        },
    )
    assert resp.status_code == 200
    match_data = resp.json()
    assert match_data["matching_offer"] is not None
    assert match_data["matching_offer"]["id"] == offer_id

    # 4. Accept offer
    resp = client.post(
        "/api/v1/shopify/upsell/decision",
        json={
            "offer_id": offer_id,
            "decision": "accepted",
            "order_id": "order_789",
        },
    )
    assert resp.status_code == 200
    decision_res = resp.json()
    assert decision_res["decision"] == "accepted"
    assert decision_res["final_upsell_price_cents"] == 3000


def test_e2e_webhook_ingress_and_event_bus(client):
    secret = "mock_shopify_shared_secret_placeholder"
    payload = {
        "id": 888999,
        "email": "buyer@dnk-shopify.test",
        "total_price": "199.99",
    }
    raw_body = b'{"id":888999,"email":"buyer@dnk-shopify.test","total_price":"199.99"}'

    # Compute valid Shopify HMAC
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    valid_hmac_b64 = base64.b64encode(digest).decode("utf-8")

    resp = client.post(
        "/api/v1/shopify/webhooks/ingress",
        json={
            "topic": "orders/paid",
            "source": "shopify",
            "payload": payload,
            "event_id": "evt_order_paid_123",
        },
        headers={"x-shopify-hmac-sha256": valid_hmac_b64},
    )
    assert resp.status_code == 200, resp.text
    event_data = resp.json()
    event_id = event_data["event_id"]
    assert event_data["status"] == "pending"

    # Dispatch event
    dispatch_resp = client.post(f"/api/v1/shopify/webhooks/{event_id}/dispatch")
    assert dispatch_resp.status_code == 200
    assert dispatch_resp.json()["status"] == "processed"
