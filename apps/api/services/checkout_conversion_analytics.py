# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_checkout_conversion_analytics"
# purpose: "Checkout & Post-Purchase Real-Time Conversion, AOV Lift & Attribution Analytics (DNK-ECOM-006 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from collections import defaultdict


class CheckoutConversionAnalytics:
    """
    Real-Time Analytics Engine for Checkout UI Extensions & Post-Purchase Funnels.
    Computes CTR, Conversion Rate, AOV Lift, and Multi-Channel Attribution.
    """

    def __init__(self):
        self._events: List[Dict[str, Any]] = []

    def record_event(
        self,
        event_type: str,
        shop_domain: str,
        channel: str = "checkout_ui",
        extension_id: Optional[str] = None,
        offer_id: Optional[str] = None,
        order_id: Optional[str] = None,
        checkout_token: Optional[str] = None,
        revenue_delta: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record a conversion funnel event.
        """
        event = {
            "id": f"evt-{len(self._events) + 1}",
            "event_type": event_type.upper(),
            "shop_domain": shop_domain,
            "channel": channel,
            "extension_id": extension_id,
            "offer_id": offer_id,
            "order_id": order_id,
            "checkout_token": checkout_token,
            "revenue_delta": float(revenue_delta),
            "metadata": metadata or {},
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        }
        self._events.append(event)
        return event

    def get_events(
        self,
        shop_domain: Optional[str] = None,
        channel: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter recorded events.
        """
        results = self._events
        if shop_domain:
            results = [e for e in results if e["shop_domain"] == shop_domain]
        if channel:
            results = [e for e in results if e["channel"] == channel]
        if event_type:
            results = [e for e in results if e["event_type"] == event_type.upper()]
        return results

    def calculate_funnel_metrics(
        self,
        shop_domain: Optional[str] = None,
        channel: Optional[str] = None,
        offer_id: Optional[str] = None,
        extension_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate CTR, Conversion Rate, Acceptance Rate, and Total Revenue Lift.
        """
        events = self._events
        if shop_domain:
            events = [e for e in events if e["shop_domain"] == shop_domain]
        if channel:
            events = [e for e in events if e["channel"] == channel]
        if offer_id:
            events = [e for e in events if e.get("offer_id") == offer_id]
        if extension_id:
            events = [e for e in events if e.get("extension_id") == extension_id]

        impressions = sum(1 for e in events if e["event_type"] == "IMPRESSION")
        clicks = sum(1 for e in events if e["event_type"] == "CLICK")
        accepts = sum(1 for e in events if e["event_type"] == "ACCEPT")
        declines = sum(1 for e in events if e["event_type"] == "DECLINE")
        completed = sum(1 for e in events if e["event_type"] == "CHECKOUT_COMPLETED")

        incremental_revenue = sum(
            e["revenue_delta"] for e in events if e["event_type"] == "ACCEPT"
        )

        ctr = (clicks / impressions) * 100.0 if impressions > 0 else 0.0
        conversion_rate = (accepts / impressions) * 100.0 if impressions > 0 else 0.0
        decisions = accepts + declines
        acceptance_rate = (accepts / decisions) * 100.0 if decisions > 0 else 0.0
        aov_lift = incremental_revenue / completed if completed > 0 else (incremental_revenue if accepts > 0 else 0.0)

        return {
            "impressions": impressions,
            "clicks": clicks,
            "accepts": accepts,
            "declines": declines,
            "completed_checkouts": completed,
            "ctr_percentage": round(ctr, 2),
            "conversion_rate_percentage": round(conversion_rate, 2),
            "acceptance_rate_percentage": round(acceptance_rate, 2),
            "total_incremental_revenue": round(incremental_revenue, 2),
            "aov_lift": round(aov_lift, 2),
            "total_events_analyzed": len(events),
        }

    def aggregate_by_channel(self, shop_domain: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Break down metrics by attribution channel (e.g. checkout_ui, post_purchase, thank_you).
        """
        channels = {"checkout_ui", "post_purchase", "thank_you"}
        events = self._events
        if shop_domain:
            events = [e for e in events if e["shop_domain"] == shop_domain]

        for e in events:
            channels.add(e.get("channel", "unknown"))

        report = {}
        for ch in channels:
            report[ch] = self.calculate_funnel_metrics(shop_domain=shop_domain, channel=ch)
        return report

    def aggregate_by_period(self, shop_domain: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Group conversion metrics by date (YYYY-MM-DD).
        """
        events = self._events
        if shop_domain:
            events = [e for e in events if e["shop_domain"] == shop_domain]

        by_date = defaultdict(list)
        for e in events:
            date_key = e["timestamp"][:10]  # Extract YYYY-MM-DD
            by_date[date_key].append(e)

        report = {}
        for date_key, date_events in by_date.items():
            impressions = sum(1 for e in date_events if e["event_type"] == "IMPRESSION")
            accepts = sum(1 for e in date_events if e["event_type"] == "ACCEPT")
            incremental_revenue = sum(
                e["revenue_delta"] for e in date_events if e["event_type"] == "ACCEPT"
            )
            report[date_key] = {
                "impressions": impressions,
                "accepts": accepts,
                "incremental_revenue": round(incremental_revenue, 2),
                "events_count": len(date_events),
            }
        return dict(report)
