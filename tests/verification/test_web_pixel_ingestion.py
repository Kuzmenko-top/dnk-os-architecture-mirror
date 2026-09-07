# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-VERIFY-WEB-PIXEL-001"
# purpose: "Comprehensive Unit and Integration Tests for Shopify Web Pixel Ingestion Pipeline"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import hashlib
import hmac
import json
from apps.api.services.pii_anonymizer import (
    anonymize_customer_id,
    anonymize_email,
    anonymize_ip_address,
    sanitize_payload,
)
from apps.api.services.web_pixel_ingestion import (
    WebPixelEvent,
    WebPixelIngestionEngine,
    ingest_web_pixel_event,
)


class TestPIIAnonymizer:
    def test_anonymize_customer_id(self):
        cid = "cust_vip_998811"
        hashed = anonymize_customer_id(cid)
        assert hashed == hashlib.sha256(b"cust_vip_998811").hexdigest()
        assert anonymize_customer_id(None) is None
        assert anonymize_customer_id("") is None

    def test_anonymize_email(self):
        assert anonymize_email("john.doe@example.com") == "j******e@example.com"
        assert anonymize_email("me@test.com") == "m*@test.com"
        assert anonymize_email("a@test.com") == "a*@test.com"
        assert anonymize_email(None) is None

    def test_anonymize_ip_address(self):
        assert anonymize_ip_address("192.168.1.45") == "192.168.1.0"
        assert anonymize_ip_address("10.0.0.123") == "10.0.0.0"
        assert anonymize_ip_address(None) is None

    def test_sanitize_payload(self):
        raw = {
            "customer_id": "cust_123",
            "email": "alice@cyber.net",
            "ip": "1.2.3.4",
            "cart_id": "cart_999",
        }
        sanitized = sanitize_payload(raw)
        assert sanitized["customer_id"] == hashlib.sha256(b"cust_123").hexdigest()
        assert sanitized["email"] == "a***e@cyber.net"
        assert sanitized["ip"] == "1.2.3.0"
        assert sanitized["cart_id"] == "cart_999"


class TestWebPixelIngestion:
    @pytest.mark.asyncio
    async def test_page_view_event(self):
        engine = WebPixelIngestionEngine()
        event = WebPixelEvent(
            event_type="page_view",
            shop_id="shop-123",
            customer_id=None,
            product_id=None,
            currency="USD",
            timestamp=1234567890,
            url="https://dnk-e.com/products/cyber-armor",
            referrer=None,
        )
        result = await engine.ingest_event(event)
        assert result["status"] == "ok"
        assert result["event_type"] == "page_view"
        assert result["anonymized_customer_id"] is None
        assert result["has_anomalies"] is False

    @pytest.mark.asyncio
    async def test_purchase_event_pii_anonymization(self):
        engine = WebPixelIngestionEngine()
        event = WebPixelEvent(
            event_type="purchase",
            shop_id="shop-123",
            customer_id="customer-456",
            product_id="product-789",
            quantity=2,
            price=50.00,
            currency="USD",
            timestamp=1234567890,
            url="https://dnk-e.com/checkout/order-completed",
            referrer="https://google.com",
        )
        result = await engine.ingest_event(event)
        expected_hash = hashlib.sha256(b"customer-456").hexdigest()
        assert result["status"] == "ok"
        assert result["anonymized_customer_id"] == expected_hash

        events = engine.get_events(shop_id="shop-123")
        assert len(events) == 1
        assert events[0]["customer_id"] == expected_hash

    @pytest.mark.asyncio
    async def test_hmac_verification(self):
        secret = "test_pixel_secret_key"
        engine = WebPixelIngestionEngine(hmac_secret=secret)

        event = WebPixelEvent(
            event_type="add_to_cart",
            shop_id="shop-hmac",
            product_id="prod_001",
            price=29.99,
        )
        raw_body = b'{"event_type": "add_to_cart", "shop_id": "shop-hmac"}'
        valid_hmac = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

        # Valid HMAC
        res_valid = await engine.ingest_event(event, raw_body=raw_body, x_shopify_hmac=valid_hmac)
        assert res_valid["status"] == "ok"

        # Invalid HMAC
        res_invalid = await engine.ingest_event(event, raw_body=raw_body, x_shopify_hmac="invalid-hmac-sig")
        assert res_invalid["status"] == "error"
        assert res_invalid["code"] == "HMAC_VERIFICATION_FAILED"

    @pytest.mark.asyncio
    async def test_anomaly_detection(self):
        engine = WebPixelIngestionEngine()

        # Suspicious negative price
        event_bad_price = WebPixelEvent(
            event_type="add_to_cart",
            shop_id="shop-anomaly",
            price=-10.0,
            quantity=1,
        )
        res_bad_price = await engine.ingest_event(event_bad_price)
        assert res_bad_price["has_anomalies"] is True
        assert "Negative price detected" in res_bad_price["anomalies"]

        # Suspicious zero purchase
        event_zero_purchase = WebPixelEvent(
            event_type="purchase",
            shop_id="shop-anomaly",
            price=0.0,
            quantity=1,
        )
        res_zero = await engine.ingest_event(event_zero_purchase)
        assert res_zero["has_anomalies"] is True
        assert "Zero-value purchase event" in res_zero["anomalies"]

        # Metrics verify anomaly count
        metrics = engine.get_metrics()
        assert metrics["total_anomalies"] >= 2
