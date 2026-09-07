# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_webhook_ingestor"
# purpose: "Shopify Webhook Ingestion, HMAC-SHA256 Verification & Idempotency Dispatcher (DNK-ECOM-006 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import hmac
import hashlib
import base64
import time
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timezone


class ShopifyWebhookIngestor:
    """
    Shopify Webhook Ingestion Engine with HMAC-SHA256 signature verification,
    idempotent event deduplication, and topic-based handler dispatching.
    """

    def __init__(self, secret: str = "shopify_app_api_shared_secret", dedupe_ttl_seconds: int = 3600):
        self.secret = secret
        self.dedupe_ttl_seconds = dedupe_ttl_seconds
        self._seen_webhooks: Dict[str, float] = {}  # webhook_id -> timestamp
        self._handlers: Dict[str, List[Callable[[Dict[str, Any], str], Dict[str, Any]]]] = {}
        self._events_log: List[Dict[str, Any]] = []

    def verify_hmac(self, raw_body: bytes, hmac_header: str) -> bool:
        """
        Verify Shopify HMAC-SHA256 header (base64 encoded).
        """
        if not hmac_header or not raw_body:
            return False

        try:
            computed_hmac = hmac.new(
                self.secret.encode("utf-8"),
                raw_body,
                hashlib.sha256
            ).digest()
            computed_b64 = base64.b64encode(computed_hmac).decode("utf-8")
            return hmac.compare_digest(computed_b64, hmac_header)
        except Exception:
            return False

    def is_duplicate(self, webhook_id: str) -> bool:
        """
        Check if the webhook has already been processed within the TTL window.
        """
        now = time.time()
        # Clean up stale entries
        self._seen_webhooks = {
            wid: ts for wid, ts in self._seen_webhooks.items()
            if (now - ts) < self.dedupe_ttl_seconds
        }

        if webhook_id in self._seen_webhooks:
            return True

        self._seen_webhooks[webhook_id] = now
        return False

    def register_handler(self, topic: str, handler: Callable[[Dict[str, Any], str], Dict[str, Any]]) -> None:
        """
        Register a callback for a specific webhook topic (e.g. 'orders/create', 'checkouts/update').
        """
        if topic not in self._handlers:
            self._handlers[topic] = []
        self._handlers[topic].append(handler)

    def process_webhook(
        self,
        raw_body: bytes,
        hmac_header: str,
        webhook_id: str,
        topic: str,
        shop_domain: str,
        payload: Dict[str, Any],
        bypass_hmac: bool = False,
    ) -> Dict[str, Any]:
        """
        Process an incoming Shopify webhook with signature verification, deduplication, and handler dispatch.
        """
        if not bypass_hmac and not self.verify_hmac(raw_body, hmac_header):
            event_record = {
                "webhook_id": webhook_id,
                "topic": topic,
                "shop_domain": shop_domain,
                "status": "rejected_hmac",
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
            self._events_log.append(event_record)
            return {
                "success": False,
                "status": "rejected_hmac",
                "error": "Invalid HMAC signature",
            }

        if self.is_duplicate(webhook_id):
            return {
                "success": True,
                "status": "skipped_duplicate",
                "message": f"Webhook {webhook_id} already processed",
            }

        # Dispatch to registered topic handlers
        handler_results = []
        handlers = self._handlers.get(topic, [])
        for handler in handlers:
            try:
                res = handler(payload, shop_domain)
                handler_results.append({"status": "ok", "result": res})
            except Exception as e:
                handler_results.append({"status": "error", "error": str(e)})

        event_record = {
            "webhook_id": webhook_id,
            "topic": topic,
            "shop_domain": shop_domain,
            "status": "processed",
            "handlers_count": len(handlers),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._events_log.append(event_record)

        return {
            "success": True,
            "status": "processed",
            "webhook_id": webhook_id,
            "topic": topic,
            "shop_domain": shop_domain,
            "handler_results": handler_results,
        }

    def get_event_log(self) -> List[Dict[str, Any]]:
        return list(self._events_log)
