# --- DNK-MRH-HEADER ---
# mrh_id: "tests_ecom_test_post_purchase_funnel_engine"
# purpose: "Unit tests for PostPurchaseFunnelEngine (DNK-ECOM-006 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import time
import pytest
from apps.api.services.post_purchase_funnel_engine import PostPurchaseFunnelEngine


def test_calculate_discounted_price_and_margin():
    # Percentage
    p1 = PostPurchaseFunnelEngine.calculate_discounted_price(100.0, "percentage", 25.0)
    assert p1 == 75.0

    # Fixed amount
    p2 = PostPurchaseFunnelEngine.calculate_discounted_price(100.0, "fixed_amount", 30.0)
    assert p2 == 70.0

    # Margin calculation
    margin = PostPurchaseFunnelEngine.calculate_margin_score(offer_price=80.0, cogs=20.0)
    assert margin == 0.75


def test_token_generation_and_verification():
    order_id = "order_12345"
    offer_id = "offer_999"
    now = int(time.time())
    expires_at = now + 120

    token = PostPurchaseFunnelEngine.generate_token(order_id, offer_id, expires_at)
    assert "." in token

    # Valid token
    assert PostPurchaseFunnelEngine.verify_token(order_id, offer_id, token) is True

    # Invalid order ID
    assert PostPurchaseFunnelEngine.verify_token("wrong_order", offer_id, token) is False

    # Expired token
    expired_token = PostPurchaseFunnelEngine.generate_token(order_id, offer_id, now - 10)
    assert PostPurchaseFunnelEngine.verify_token(order_id, offer_id, expired_token) is False


def test_select_primary_upsell_and_downsell():
    offers = [
        {
            "id": "offer-low",
            "name": "Standard Upsell",
            "headline": "Upgrade today!",
            "product_id": "p-100",
            "original_price": 50.0,
            "discount_type": "percentage",
            "discount_value": 10.0,
            "priority": 1,
            "status": "active",
            "timer_seconds": 300,
            "trigger_rules": {"min_order_total": 20.0},
        },
        {
            "id": "offer-high",
            "name": "Premium Bundle Upsell",
            "headline": "Special VIP Addon!",
            "product_id": "p-200",
            "original_price": 100.0,
            "discount_type": "percentage",
            "discount_value": 20.0,
            "priority": 10,
            "status": "active",
            "timer_seconds": 300,
            "trigger_rules": {"min_order_total": 50.0},
        },
    ]

    order_ctx = {
        "order_id": "order-777",
        "total_price": 120.0,
        "line_items": [{"product_id": "p-base"}],
        "currency": "USD",
    }

    primary = PostPurchaseFunnelEngine.select_primary_upsell(offers, order_ctx)
    assert primary is not None
    assert primary["offer_id"] == "offer-high"
    assert primary["offer_price"] == 80.0
    assert "token" in primary

    # Downsell selection when primary declined
    downsell = PostPurchaseFunnelEngine.select_downsell_offer("offer-high", offers, order_ctx)
    assert downsell is not None
    assert downsell["offer_id"] == "offer-low"
