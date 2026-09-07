# --- DNK-MRH-HEADER ---
# mrh_id: "tests_ecom_test_checkout_conversion_analytics"
# purpose: "Unit tests for CheckoutConversionAnalytics (DNK-ECOM-006 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.checkout_conversion_analytics import CheckoutConversionAnalytics


def test_conversion_metrics_calculation():
    analytics = CheckoutConversionAnalytics()
    shop = "demo.myshopify.com"

    # Record 10 impressions
    for _ in range(10):
        analytics.record_event("IMPRESSION", shop_domain=shop, offer_id="off-1")

    # Record 4 clicks
    for _ in range(4):
        analytics.record_event("CLICK", shop_domain=shop, offer_id="off-1")

    # Record 2 accepts ($30 each)
    analytics.record_event("ACCEPT", shop_domain=shop, offer_id="off-1", revenue_delta=30.0)
    analytics.record_event("ACCEPT", shop_domain=shop, offer_id="off-1", revenue_delta=30.0)

    # Record 1 decline
    analytics.record_event("DECLINE", shop_domain=shop, offer_id="off-1")

    # Record 2 completed checkouts
    analytics.record_event("CHECKOUT_COMPLETED", shop_domain=shop)
    analytics.record_event("CHECKOUT_COMPLETED", shop_domain=shop)

    metrics = analytics.calculate_funnel_metrics(shop_domain=shop)

    assert metrics["impressions"] == 10
    assert metrics["clicks"] == 4
    assert metrics["accepts"] == 2
    assert metrics["declines"] == 1
    assert metrics["completed_checkouts"] == 2
    assert metrics["ctr_percentage"] == 40.0
    assert metrics["conversion_rate_percentage"] == 20.0
    assert metrics["total_incremental_revenue"] == 60.0
    assert metrics["aov_lift"] == 30.0  # $60 / 2 orders


def test_aggregate_by_channel_and_period():
    analytics = CheckoutConversionAnalytics()
    shop = "demo.myshopify.com"

    analytics.record_event(
        "IMPRESSION", shop_domain=shop, channel="checkout_ui", timestamp="2026-08-28T10:00:00Z"
    )
    analytics.record_event(
        "ACCEPT", shop_domain=shop, channel="checkout_ui", revenue_delta=15.0, timestamp="2026-08-28T10:05:00Z"
    )
    analytics.record_event(
        "IMPRESSION", shop_domain=shop, channel="post_purchase", timestamp="2026-08-29T11:00:00Z"
    )
    analytics.record_event(
        "ACCEPT", shop_domain=shop, channel="post_purchase", revenue_delta=45.0, timestamp="2026-08-29T11:05:00Z"
    )

    by_channel = analytics.aggregate_by_channel(shop_domain=shop)
    assert by_channel["checkout_ui"]["total_incremental_revenue"] == 15.0
    assert by_channel["post_purchase"]["total_incremental_revenue"] == 45.0

    by_period = analytics.aggregate_by_period(shop_domain=shop)
    assert "2026-08-28" in by_period
    assert by_period["2026-08-28"]["incremental_revenue"] == 15.0
    assert "2026-08-29" in by_period
    assert by_period["2026-08-29"]["incremental_revenue"] == 45.0
