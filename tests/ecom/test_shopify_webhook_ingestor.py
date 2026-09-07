# --- DNK-MRH-HEADER ---
# mrh_id: "tests_ecom_test_shopify_webhook_ingestor"
# purpose: "Unit tests for ShopifyWebhookIngestor (DNK-ECOM-006 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import hmac
import hashlib
import base64
import json
import pytest
from apps.api.services.shopify_webhook_ingestor import ShopifyWebhookIngestor


def generate_hmac_header(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def test_webhook_hmac_verification():
    secret = "test_secret_key_123"
    ingestor = ShopifyWebhookIngestor(secret=secret)

    payload = {"id": 1001, "total_price": "99.99"}
    body = json.dumps(payload).encode("utf-8")
    valid_hmac = generate_hmac_header(secret, body)

    assert ingestor.verify_hmac(body, valid_hmac) is True
    assert ingestor.verify_hmac(body, "invalid_base64_hmac") is False


def test_webhook_deduplication():
    ingestor = ShopifyWebhookIngestor(secret="secret")
    webhook_id = "wh_unique_001"

    assert ingestor.is_duplicate(webhook_id) is False
    assert ingestor.is_duplicate(webhook_id) is True  # Second time is duplicate


def test_webhook_dispatch_and_handler():
    secret = "secret"
    ingestor = ShopifyWebhookIngestor(secret=secret)

    handled_orders = []

    def on_order_created(payload, shop_domain):
        handled_orders.append({"order_id": payload["id"], "shop": shop_domain})
        return {"processed": True}

    ingestor.register_handler("orders/create", on_order_created)

    payload = {"id": 8888, "line_items": [{"id": 1, "title": "Widget"}]}
    body = json.dumps(payload).encode("utf-8")
    hmac_val = generate_hmac_header(secret, body)

    res = ingestor.process_webhook(
        raw_body=body,
        hmac_header=hmac_val,
        webhook_id="wh_ord_1",
        topic="orders/create",
        shop_domain="mystore.myshopify.com",
        payload=payload,
    )

    assert res["success"] is True
    assert res["status"] == "processed"
    assert len(handled_orders) == 1
    assert handled_orders[0]["order_id"] == 8888
    assert handled_orders[0]["shop"] == "mystore.myshopify.com"

    # Duplicate call should skip handlers
    res_dup = ingestor.process_webhook(
        raw_body=body,
        hmac_header=hmac_val,
        webhook_id="wh_ord_1",
        topic="orders/create",
        shop_domain="mystore.myshopify.com",
        payload=payload,
    )
    assert res_dup["status"] == "skipped_duplicate"
    assert len(handled_orders) == 1
