# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_webhook_event_bus"
# purpose: "Shopify & Stripe Webhook Ingress, Cryptographic HMAC Verifier & Event Bus Dispatcher (DNK-ECOM-004)"
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
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field


class WebhookTopic(str, Enum):
    ORDERS_CREATE = "orders/create"
    ORDERS_PAID = "orders/paid"
    ORDERS_CANCELLED = "orders/cancelled"
    REFUNDS_CREATE = "refunds/create"
    PAYMENT_INTENT_SUCCEEDED = "payment_intent/succeeded"
    PAYMENT_INTENT_FAILED = "payment_intent/failed"
    CHECKOUT_UPDATE = "checkouts/update"


class WebhookDeliveryStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    DUPLICATE = "duplicate"
    DEAD_LETTER = "dead_letter"


class WebhookEventRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str  # External or unique event ID for idempotency
    topic: WebhookTopic
    source: str = "shopify"  # "shopify", "stripe", "coinbase"
    payload: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict)
    status: WebhookDeliveryStatus = WebhookDeliveryStatus.PENDING
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None


class ShopifyWebhookEventBus:
    """Ingress handler for webhooks with HMAC validation, deduplication, and subscriber dispatching."""

    def __init__(self, db_session=None):
        self.db_session = db_session
        self._events: Dict[str, WebhookEventRecord] = {}  # event_id -> Record
        self._handlers: Dict[WebhookTopic, List[Callable[[WebhookEventRecord], Any]]] = {
            t: [] for t in WebhookTopic
        }

    @staticmethod
    def verify_shopify_hmac(raw_body: bytes, hmac_header: str, secret: str) -> bool:
        """Verifies X-Shopify-Hmac-Sha256 base64 digest."""
        if not hmac_header or not secret:
            return False
        computed = base64.b64encode(hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()).decode("utf-8")
        return hmac.compare_digest(computed.strip(), hmac_header.strip())

    @staticmethod
    def verify_stripe_signature(raw_body: bytes, signature_header: str, secret: str, tolerance_s: int = 300) -> bool:
        """Verifies Stripe-Signature with timestamp and t,v1 signature matching."""
        if not signature_header or not secret:
            return False

        parts = signature_header.split(",")
        timestamp = None
        signatures = []

        for part in parts:
            if "=" in part:
                k, v = part.strip().split("=", 1)
                if k == "t":
                    timestamp = v
                elif k == "v1":
                    signatures.append(v)

        if not timestamp or not signatures:
            return False

        try:
            ts_int = int(timestamp)
            current_ts = int(time.time())
            if abs(current_ts - ts_int) > tolerance_s:
                return False
        except ValueError:
            return False

        signed_payload = f"{timestamp}.".encode("utf-8") + raw_body
        expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()

        return any(hmac.compare_digest(expected, sig) for sig in signatures)

    def register_handler(self, topic: WebhookTopic, handler: Callable[[WebhookEventRecord], Any]):
        """Subscribes an event handler to a webhook topic."""
        if topic not in self._handlers:
            self._handlers[topic] = []
        self._handlers[topic].append(handler)

    def ingest_event(
        self,
        topic: WebhookTopic,
        source: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> WebhookEventRecord:
        """Ingests a webhook event, enforcing deduplication and idempotency."""
        effective_event_id = event_id or f"evt_{uuid.uuid4().hex[:16]}"

        if effective_event_id in self._events:
            existing = self._events[effective_event_id]
            # Mark as duplicate if received again
            return existing

        record = WebhookEventRecord(
            event_id=effective_event_id,
            topic=topic,
            source=source,
            payload=payload,
            headers=headers or {},
            status=WebhookDeliveryStatus.PENDING,
        )

        self._events[effective_event_id] = record
        return record

    def dispatch_event(self, event_id: str) -> WebhookEventRecord:
        """Dispatches an ingested event to all registered topic subscribers."""
        if event_id not in self._events:
            raise ValueError(f"Event ID '{event_id}' not found in Event Bus registry.")

        record = self._events[event_id]
        handlers = self._handlers.get(record.topic, [])

        if not handlers:
            record.status = WebhookDeliveryStatus.PROCESSED
            record.processed_at = datetime.now(timezone.utc)
            return record

        try:
            for handler in handlers:
                handler(record)
            record.status = WebhookDeliveryStatus.PROCESSED
            record.processed_at = datetime.now(timezone.utc)
            record.error_message = None
        except Exception as ex:
            record.retry_count += 1
            record.error_message = str(ex)
            if record.retry_count >= 3:
                record.status = WebhookDeliveryStatus.DEAD_LETTER
            else:
                record.status = WebhookDeliveryStatus.FAILED

        return record

    def get_event(self, event_id: str) -> Optional[WebhookEventRecord]:
        return self._events.get(event_id)

    def list_events(
        self,
        topic: Optional[WebhookTopic] = None,
        status: Optional[WebhookDeliveryStatus] = None,
        source: Optional[str] = None,
    ) -> List[WebhookEventRecord]:
        events = list(self._events.values())
        if topic:
            events = [e for e in events if e.topic == topic]
        if status:
            events = [e for e in events if e.status == status]
        if source:
            events = [e for e in events if e.source == source]
        return sorted(events, key=lambda x: x.received_at, reverse=True)
