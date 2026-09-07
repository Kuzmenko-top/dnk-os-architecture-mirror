# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_webhook_event_bus"
# purpose: "Comprehensive Unit and Integration Tests for Webhook Ingress, HMAC Verifier & Event Bus (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import base64
import hashlib
import hmac
import time
from apps.api.services.shopify_webhook_event_bus import (
    ShopifyWebhookEventBus,
    WebhookTopic,
    WebhookDeliveryStatus,
)


def test_shopify_hmac_verification():
    bus = ShopifyWebhookEventBus()
    secret = "shpss_test_secret_key_123"
    body = b'{"id":123456,"total_price":"99.00","currency":"USD"}'

    # Compute valid signature
    valid_hmac = base64.b64encode(hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()).decode("utf-8")

    assert bus.verify_shopify_hmac(body, valid_hmac, secret) is True
    assert bus.verify_shopify_hmac(body, "invalid_signature", secret) is False
    assert bus.verify_shopify_hmac(b'{"tampered":true}', valid_hmac, secret) is False


def test_stripe_signature_verification():
    bus = ShopifyWebhookEventBus()
    secret = "whsec_stripe_test_secret"
    body = b'{"type":"payment_intent.succeeded","data":{"object":{"id":"pi_123"}}}'
    now_ts = int(time.time())

    signed_payload = f"{now_ts}.".encode("utf-8") + body
    sig_hex = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    valid_header = f"t={now_ts},v1={sig_hex}"

    assert bus.verify_stripe_signature(body, valid_header, secret) is True
    assert bus.verify_stripe_signature(body, f"t={now_ts},v1=wrong_hex", secret) is False

    # Expired signature (tolerance test)
    expired_ts = now_ts - 600
    expired_signed_payload = f"{expired_ts}.".encode("utf-8") + body
    expired_sig_hex = hmac.new(secret.encode("utf-8"), expired_signed_payload, hashlib.sha256).hexdigest()
    expired_header = f"t={expired_ts},v1={expired_sig_hex}"
    assert bus.verify_stripe_signature(body, expired_header, secret, tolerance_s=300) is False


def test_event_ingestion_and_deduplication():
    bus = ShopifyWebhookEventBus()
    event_id = "evt_unique_1001"

    rec1 = bus.ingest_event(
        topic=WebhookTopic.ORDERS_CREATE,
        source="shopify",
        payload={"order_id": "ord_888", "customer": "test@example.com"},
        event_id=event_id,
    )
    assert rec1.status == WebhookDeliveryStatus.PENDING
    assert rec1.event_id == event_id

    # Ingest duplicate
    rec2 = bus.ingest_event(
        topic=WebhookTopic.ORDERS_CREATE,
        source="shopify",
        payload={"order_id": "ord_888", "customer": "test@example.com"},
        event_id=event_id,
    )
    assert rec2.id == rec1.id
    assert len(bus.list_events()) == 1


def test_event_subscription_and_dispatch():
    bus = ShopifyWebhookEventBus()
    handled_events = []

    def order_paid_handler(record):
        handled_events.append(record.payload.get("order_id"))

    bus.register_handler(WebhookTopic.ORDERS_PAID, order_paid_handler)

    rec = bus.ingest_event(
        topic=WebhookTopic.ORDERS_PAID,
        source="shopify",
        payload={"order_id": "ord_paid_777", "amount": 15000},
        event_id="evt_paid_1",
    )

    dispatched = bus.dispatch_event(rec.event_id)
    assert dispatched.status == WebhookDeliveryStatus.PROCESSED
    assert dispatched.processed_at is not None
    assert "ord_paid_777" in handled_events


def test_event_dispatch_failure_and_dead_letter():
    bus = ShopifyWebhookEventBus()

    def failing_handler(record):
        raise RuntimeError("External inventory service down")

    bus.register_handler(WebhookTopic.ORDERS_CANCELLED, failing_handler)

    rec = bus.ingest_event(
        topic=WebhookTopic.ORDERS_CANCELLED,
        source="shopify",
        payload={"order_id": "ord_cancelled_999"},
        event_id="evt_fail_1",
    )

    # 1st try -> FAILED
    d1 = bus.dispatch_event(rec.event_id)
    assert d1.status == WebhookDeliveryStatus.FAILED
    assert d1.retry_count == 1
    assert "External inventory service down" in (d1.error_message or "")

    # 2nd try -> FAILED
    d2 = bus.dispatch_event(rec.event_id)
    assert d2.status == WebhookDeliveryStatus.FAILED
    assert d2.retry_count == 2

    # 3rd try -> DEAD_LETTER
    d3 = bus.dispatch_event(rec.event_id)
    assert d3.status == WebhookDeliveryStatus.DEAD_LETTER
    assert d3.retry_count == 3
