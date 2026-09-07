# --- DNK-MRH-HEADER ---
# mrh_id: "tests_ecom_test_checkout_postpurchase_api_and_ws"
# purpose: "E2E Integration tests for Checkout UI & Post-Purchase REST API and WebSocket (DNK-ECOM-006 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.services.post_purchase_funnel_engine import PostPurchaseFunnelEngine
import time


@pytest.fixture
def client():
    return TestClient(app)


def test_create_and_list_checkout_extensions(client):
    shop = "mystore-test.myshopify.com"
    ext_payload = {
        "shop_domain": shop,
        "extension_point": "purchase.checkout.block.render",
        "extension_type": "cross_sell",
        "title": "VIP Cross Sell",
        "priority": 15,
        "config_schema": {
            "headline": "Special Bundle",
            "products": [{"product_id": "prod-1", "title": "Strap", "price": 20.0}],
        },
        "rules_payload": {"min_cart_total": 30.0},
    }

    # Create
    res = client.post("/api/v1/ecom/checkout/extensions", json=ext_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["extension"]["title"] == "VIP Cross Sell"

    # List
    list_res = client.get(f"/api/v1/ecom/checkout/extensions?shop_domain={shop}")
    assert list_res.status_code == 200
    extensions = list_res.json()["extensions"]
    assert len(extensions) >= 1
    assert any(e["title"] == "VIP Cross Sell" for e in extensions)


def test_evaluate_checkout_extensions_endpoint(client):
    shop = "evalstore.myshopify.com"
    client.post("/api/v1/ecom/checkout/extensions", json={
        "shop_domain": shop,
        "extension_point": "purchase.checkout.block.render",
        "extension_type": "banner",
        "title": "Free Shipping Banner",
        "priority": 25,
        "config_schema": {"message": "Spend $50 for Free Shipping"},
        "rules_payload": {"min_cart_total": 10.0},
    })

    eval_res = client.post("/api/v1/ecom/checkout/evaluate", json={
        "shop_domain": shop,
        "extension_point": "purchase.checkout.block.render",
        "context": {"cart_total": 45.0, "currency": "USD"},
    })

    assert eval_res.status_code == 200
    res_data = eval_res.json()
    assert res_data["success"] is True
    assert res_data["count"] >= 1
    assert res_data["widgets"][0]["extension_type"] == "banner"


def test_create_and_evaluate_post_purchase_offer(client):
    shop = "postpurchase-store.myshopify.com"
    offer_payload = {
        "shop_domain": shop,
        "name": "One-Time VIP Upsell",
        "headline": "Wait! Add this exclusive accessory!",
        "product_id": "prod-vip-100",
        "variant_id": "var-vip-100",
        "original_price": 50.0,
        "discount_type": "percentage",
        "discount_value": 20.0,
        "cogs": 10.0,
        "priority": 10,
        "timer_seconds": 300,
        "trigger_rules": {"min_order_total": 20.0},
    }

    create_res = client.post("/api/v1/ecom/post-purchase/offers", json=offer_payload)
    assert create_res.status_code == 201
    offer_id = create_res.json()["offer"]["id"]

    # Evaluate
    eval_res = client.post("/api/v1/ecom/post-purchase/evaluate", json={
        "shop_domain": shop,
        "order_context": {
            "order_id": "order-abc-123",
            "total_price": 75.0,
            "currency": "USD",
            "line_items": [{"product_id": "prod-main"}],
        },
    })
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["has_offer"] is True
    offer = eval_data["offer"]
    assert offer["offer_price"] == 40.0  # 50 - 20%
    assert "token" in offer

    # Accept Offer
    accept_res = client.post("/api/v1/ecom/post-purchase/accept", json={
        "order_id": "order-abc-123",
        "offer_id": offer_id,
        "token": offer["token"],
        "shop_domain": shop,
        "revenue_delta": 40.0,
    })
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "accepted"


def test_shopify_webhook_and_analytics_summary(client):
    shop = "analytics-store.myshopify.com"

    # Track conversion event directly
    evt_res = client.post("/api/v1/ecom/analytics/events", json={
        "shop_domain": shop,
        "event_type": "IMPRESSION",
        "channel": "checkout_ui",
    })
    assert evt_res.status_code == 201

    # Webhook trigger
    wh_res = client.post(
        "/api/v1/ecom/webhooks/shopify",
        json={"id": 9999, "total_price": "120.00"},
        headers={
            "X-Shopify-Hmac-Sha256": "test_bypass_hmac",
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": shop,
            "X-Shopify-Webhook-Id": "wh-unit-test-1",
        },
    )
    assert wh_res.status_code == 200
    assert wh_res.json()["status"] == "processed"

    # Get summary
    summary_res = client.get(f"/api/v1/ecom/analytics/summary?shop_domain={shop}")
    assert summary_res.status_code == 200
    assert summary_res.json()["success"] is True


def test_checkout_analytics_websocket(client):
    shop = "ws-store.myshopify.com"
    with client.websocket_connect(f"/api/v1/ecom/analytics/ws/{shop}") as ws:
        init_msg = ws.receive_json()
        assert init_msg["type"] == "CONNECTION_ESTABLISHED"
        assert init_msg["shop_domain"] == shop

        # Ping
        ws.send_json({"action": "ping"})
        pong_msg = ws.receive_json()
        assert pong_msg["type"] == "PONG"
