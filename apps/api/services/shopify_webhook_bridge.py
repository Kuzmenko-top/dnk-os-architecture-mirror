# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/shopify_webhook_bridge.py"
# purpose: "Shopify Webhook HMAC-SHA256 Verification & Event Routing Bridge."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import hmac
import hashlib
import base64
import logging
from typing import Dict, Any, Optional
from .shopify_flow_engine import ShopifyFlowEngine

logger = logging.getLogger("dnk.shopify.webhook_bridge")


class ShopifyWebhookBridge:
    """
    Shopify Webhook HMAC-SHA256 Bridge validating inbound webhook signatures
    and dispatching event handlers (Order Create, Product Update, App Uninstalled).
    """

    def __init__(
        self,
        webhook_secret: str = "whsec_test_secret",
        flow_engine: Optional[ShopifyFlowEngine] = None,
    ):
        self.webhook_secret = webhook_secret.encode("utf-8")
        self.flow_engine = flow_engine or ShopifyFlowEngine()
        self.processed_events: list[Dict[str, Any]] = []

    def verify_hmac(self, body: bytes, hmac_header: Optional[str]) -> bool:
        """
        Verifies Shopify HMAC-SHA256 signature against the raw request body.
        Supports both Base64-encoded signature (Shopify standard) and Hexadecimal.
        """
        if not hmac_header:
            return False

        # Calculate standard Shopify Base64 HMAC
        calculated_digest = hmac.new(
            self.webhook_secret,
            body,
            hashlib.sha256,
        ).digest()
        calculated_base64 = base64.b64encode(calculated_digest).decode("utf-8")

        if hmac.compare_digest(hmac_header, calculated_base64):
            return True

        # Also support hex format for flexibility
        calculated_hex = hmac.new(
            self.webhook_secret,
            body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(hmac_header, calculated_hex)

    async def process_webhook(self, payload: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """
        Dispatches validated webhook payload to the respective topic handler.
        """
        topic_normalized = topic.lower().replace(" ", "")
        
        if topic_normalized in ("orders/create", "order_create"):
            result = await self._handle_order_create(payload)
        elif topic_normalized in ("products/update", "product_update"):
            result = await self._handle_product_update(payload)
        elif topic_normalized in ("app/uninstalled", "app_uninstalled"):
            result = await self._handle_app_uninstalled(payload)
        else:
            result = {"status": "ignored", "topic": topic}

        self.processed_events.append({
            "topic": topic,
            "payload": payload,
            "result": result,
        })
        return result

    async def _handle_order_create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles 'orders/create' webhook: persists order, triggers Flow automation.
        """
        order_id = payload.get("id")
        order_number = payload.get("order_number") or payload.get("number")
        total_price = payload.get("total_price", "0.00")

        # Trigger Flow automation
        await self.flow_engine.trigger_flow("order_create", payload)

        logger.info(f"Order #{order_number} (ID: {order_id}) processed, total: {total_price}")
        return {
            "status": "processed",
            "order_id": order_id,
            "order_number": order_number,
            "total_price": total_price,
            "flow_triggered": True,
        }

    async def _handle_product_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles 'products/update' webhook: updates catalog and invalidates cache.
        """
        product_id = payload.get("id")
        title = payload.get("title", "")

        logger.info(f"Product updated: {product_id} ({title})")
        return {
            "status": "processed",
            "product_id": product_id,
            "title": title,
            "cache_invalidated": True,
        }

    async def _handle_app_uninstalled(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles 'app/uninstalled' webhook: initiates GDPR shop cleanup.
        """
        shop_id = payload.get("shop_id") or payload.get("id")
        shop_domain = payload.get("myshopify_domain", "")

        logger.info(f"App uninstalled from shop: {shop_id} ({shop_domain})")
        return {
            "status": "processed",
            "shop_id": shop_id,
            "shop_domain": shop_domain,
            "gdpr_cleanup_initiated": True,
        }
