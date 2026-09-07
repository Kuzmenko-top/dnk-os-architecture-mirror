# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_shopify_webhook_bridge.py"
# purpose: "Unit & Integration Tests for Shopify Flow Engine and Webhook HMAC Bridge."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import hmac
import hashlib
import base64
import json
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.services.shopify_flow_engine import ShopifyFlowEngine
from apps.api.services.shopify_webhook_bridge import ShopifyWebhookBridge


@pytest.fixture
def test_client():
    return TestClient(app)


class TestShopifyFlowEngine:
    @pytest.mark.asyncio
    async def test_create_order_fulfillment_flow(self):
        engine = ShopifyFlowEngine()
        flow_id = await engine.create_order_fulfillment_flow()
        assert flow_id is not None
        assert "flow" in flow_id.lower() or "gid://" in flow_id

    @pytest.mark.asyncio
    async def test_create_inventory_alert_flow(self):
        engine = ShopifyFlowEngine()
        flow_id = await engine.create_inventory_alert_flow(threshold=5)
        assert flow_id is not None

    @pytest.mark.asyncio
    async def test_trigger_flow(self):
        engine = ShopifyFlowEngine()
        payload = {"order_id": 999, "items_count": 2}
        result = await engine.trigger_flow("custom_flow", payload)
        assert result["status"] == "triggered"
        assert result["flow_name"] == "custom_flow"
        assert len(engine.triggered_flows) == 1


class TestShopifyWebhookBridge:
    def test_hmac_verification_valid_base64(self):
        secret = "whsec_test_secret"
        bridge = ShopifyWebhookBridge(webhook_secret=secret)
        payload = json.dumps({"order_id": 12345}).encode("utf-8")
        
        digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
        base64_hmac = base64.b64encode(digest).decode("utf-8")
        
        assert bridge.verify_hmac(payload, base64_hmac) is True

    def test_hmac_verification_valid_hex(self):
        secret = "whsec_test_secret"
        bridge = ShopifyWebhookBridge(webhook_secret=secret)
        payload = json.dumps({"order_id": 12345}).encode("utf-8")
        
        hex_hmac = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        assert bridge.verify_hmac(payload, hex_hmac) is True

    def test_hmac_verification_invalid(self):
        bridge = ShopifyWebhookBridge(webhook_secret="whsec_test_secret")
        payload = b'{"order_id": 12345}'
        assert bridge.verify_hmac(payload, "invalid_signature") is False
        assert bridge.verify_hmac(payload, None) is False

    @pytest.mark.asyncio
    async def test_handle_order_create(self):
        bridge = ShopifyWebhookBridge()
        payload = {
            "id": 8881,
            "order_number": "1001",
            "total_price": "149.50",
        }
        result = await bridge._handle_order_create(payload)
        assert result["status"] == "processed"
        assert result["order_id"] == 8881
        assert result["flow_triggered"] is True

    @pytest.mark.asyncio
    async def test_handle_product_update(self):
        bridge = ShopifyWebhookBridge()
        payload = {
            "id": 5552,
            "title": "DNK Cyber T-Shirt",
        }
        result = await bridge._handle_product_update(payload)
        assert result["status"] == "processed"
        assert result["product_id"] == 5552
        assert result["cache_invalidated"] is True

    @pytest.mark.asyncio
    async def test_handle_app_uninstalled(self):
        bridge = ShopifyWebhookBridge()
        payload = {
            "shop_id": 101,
            "myshopify_domain": "test-store.myshopify.com",
        }
        result = await bridge._handle_app_uninstalled(payload)
        assert result["status"] == "processed"
        assert result["shop_id"] == 101
        assert result["gdpr_cleanup_initiated"] is True

    @pytest.mark.asyncio
    async def test_process_webhook_routing(self):
        bridge = ShopifyWebhookBridge()
        order_res = await bridge.process_webhook({"id": 1}, "orders/create")
        assert order_res["status"] == "processed"

        prod_res = await bridge.process_webhook({"id": 2, "title": "P"}, "products/update")
        assert prod_res["status"] == "processed"

        uninstall_res = await bridge.process_webhook({"id": 3}, "app/uninstalled")
        assert uninstall_res["status"] == "processed"

        ignored_res = await bridge.process_webhook({"id": 4}, "unknown/topic")
        assert ignored_res["status"] == "ignored"


class TestShopifyWebhookEndpoints:
    def test_order_create_endpoint_unauthorized(self, test_client):
        response = test_client.post(
            "/shopify/webhooks/orders/create",
            json={"id": 123},
            headers={"X-Shopify-Hmac-SHA256": "bad_hmac"},
        )
        assert response.status_code == 401

    def test_order_create_endpoint_success(self, test_client):
        secret = "whsec_test_secret"
        payload_bytes = json.dumps({"id": 12345, "order_number": 501, "total_price": "29.99"}).encode("utf-8")
        digest = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
        base64_hmac = base64.b64encode(digest).decode("utf-8")

        response = test_client.post(
            "/shopify/webhooks/orders/create",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Hmac-SHA256": base64_hmac,
                "X-Shopify-Topic": "orders/create",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["order_id"] == 12345

    def test_product_update_endpoint_success(self, test_client):
        secret = "whsec_test_secret"
        payload_bytes = json.dumps({"id": 999, "title": "Smart Watch"}).encode("utf-8")
        digest = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
        base64_hmac = base64.b64encode(digest).decode("utf-8")

        response = test_client.post(
            "/shopify/webhooks/products/update",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Hmac-SHA256": base64_hmac,
                "X-Shopify-Topic": "products/update",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["product_id"] == 999

    def test_app_uninstalled_endpoint_success(self, test_client):
        secret = "whsec_test_secret"
        payload_bytes = json.dumps({"shop_id": 42, "myshopify_domain": "demo.myshopify.com"}).encode("utf-8")
        digest = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
        base64_hmac = base64.b64encode(digest).decode("utf-8")

        response = test_client.post(
            "/shopify/webhooks/app/uninstalled",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Hmac-SHA256": base64_hmac,
                "X-Shopify-Topic": "app/uninstalled",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["shop_id"] == 42
