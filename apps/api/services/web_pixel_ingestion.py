# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/web_pixel_ingestion.py"
# purpose: "High-throughput Web Pixel Ingestion, HMAC verification, PII sanitization and anomaly detection"
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
import json
import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from apps.api.services.pii_anonymizer import anonymize_customer_id, sanitize_payload


class WebPixelEvent(BaseModel):
    event_type: str = Field(..., description="page_view, add_to_cart, checkout_started, purchase")
    shop_id: str = Field(..., description="Shopify store identifier")
    customer_id: Optional[str] = None
    product_id: Optional[str] = None
    variant_id: Optional[str] = None
    quantity: Optional[int] = 1
    price: Optional[float] = None
    currency: str = "USD"
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    url: str = ""
    referrer: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class WebPixelIngestionEngine:
    DEFAULT_SECRET = "dnk_shopify_pixel_secret_v2"

    def __init__(self, hmac_secret: str = DEFAULT_SECRET):
        self.hmac_secret = hmac_secret
        self._events_store: List[Dict[str, Any]] = []
        self._anomaly_alerts: List[Dict[str, Any]] = []

    def verify_hmac(self, body_bytes: bytes, received_hmac: Optional[str]) -> bool:
        """Validate HMAC-SHA256 signature against webhook/event payload."""
        if not received_hmac:
            # If no HMAC provided and secret is present, check if optional or required
            return False
        expected_hmac = hmac.new(
            self.hmac_secret.encode("utf-8"),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_hmac, received_hmac)

    def detect_anomalies(self, event: WebPixelEvent) -> List[str]:
        """Simple rule-based anomaly detection for pixel events."""
        anomalies: List[str] = []
        if event.price is not None and event.price < 0:
            anomalies.append("Negative price detected")
        if event.quantity is not None and (event.quantity <= 0 or event.quantity > 10000):
            anomalies.append(f"Suspicious quantity: {event.quantity}")
        if event.event_type == "purchase" and (event.price is None or event.price == 0):
            anomalies.append("Zero-value purchase event")
        return anomalies

    async def ingest_event(
        self,
        event: WebPixelEvent,
        raw_body: Optional[bytes] = None,
        x_shopify_hmac: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process, validate, anonymize and persist incoming web pixel event."""
        # 1. HMAC validation if signature is provided
        if x_shopify_hmac:
            body = raw_body or json.dumps(event.model_dump(), sort_keys=True).encode("utf-8")
            if not self.verify_hmac(body, x_shopify_hmac):
                return {
                    "status": "error",
                    "message": "Invalid HMAC",
                    "code": "HMAC_VERIFICATION_FAILED"
                }

        # 2. PII Anonymization
        original_customer_id = event.customer_id
        anonymized_customer = anonymize_customer_id(event.customer_id)
        
        event_dict = event.model_dump()
        event_dict["customer_id"] = anonymized_customer
        if event.extra_data:
            event_dict["extra_data"] = sanitize_payload(event.extra_data)

        # 3. Anomaly Analysis
        anomalies = self.detect_anomalies(event)
        if anomalies:
            alert = {
                "timestamp": int(time.time()),
                "shop_id": event.shop_id,
                "event_type": event.event_type,
                "anomalies": anomalies
            }
            self._anomaly_alerts.append(alert)

        # 4. Storage
        self._events_store.append(event_dict)

        return {
            "status": "ok",
            "event_type": event.event_type,
            "anonymized_customer_id": anonymized_customer,
            "has_anomalies": len(anomalies) > 0,
            "anomalies": anomalies,
            "persisted_at": int(time.time() * 1000)
        }

    def get_events(self, shop_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve latest events, optionally filtered by shop_id."""
        events = self._events_store
        if shop_id:
            events = [e for e in events if e.get("shop_id") == shop_id]
        return events[-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        """Aggregate event metrics."""
        total = len(self._events_store)
        by_type: Dict[str, int] = {}
        for e in self._events_store:
            t = e.get("event_type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "total_events": total,
            "events_by_type": by_type,
            "total_anomalies": len(self._anomaly_alerts),
            "latest_anomalies": self._anomaly_alerts[-10:]
        }


# Global singleton instance
pixel_ingestion_engine = WebPixelIngestionEngine()


async def ingest_web_pixel_event(
    event: WebPixelEvent,
    raw_body: Optional[bytes] = None,
    x_shopify_hmac: Optional[str] = None
) -> Dict[str, Any]:
    """Helper functional wrapper for ingestion."""
    return await pixel_ingestion_engine.ingest_event(event, raw_body, x_shopify_hmac)
