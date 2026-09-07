# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-VERIFY-SHOPIFY-EXTENSIONS-001"
# purpose: "Comprehensive Unit and E2E Tests for Shopify Checkout UI Extensions"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Auditor"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.shopify.extensions import (
    CheckoutUpsell,
    CheckoutUpsellEngine,
    CartLineItem,
    CheckoutLoyalty,
    CheckoutLoyaltyEngine,
    PostPurchaseUpsell,
    PostPurchaseUpsellEngine,
)


class TestCheckoutUpsell:
    def test_upsell_banner_shows_when_total_below_100(self):
        cart_lines = [
            {"id": "line_1", "cost": {"totalAmount": {"amount": "50.00"}}},
        ]
        upsell = CheckoutUpsell(cart_lines)
        assert upsell.should_show_upsell() is True
        assert upsell.calculate_cart_total() == 50.00
        assert upsell.get_remaining_threshold() == 50.00

    def test_upsell_banner_hidden_when_total_above_100(self):
        cart_lines = [
            {"id": "line_2", "cost": {"totalAmount": {"amount": "150.00"}}},
        ]
        upsell = CheckoutUpsell(cart_lines)
        assert upsell.should_show_upsell() is False
        assert upsell.get_remaining_threshold() == 0.0

    def test_upsell_remaining_calculation_and_recommendation(self):
        # Gap = 15.00 <= 25.00 -> recommends express warranty
        cart_lines = [
            {"id": "line_3", "cost": {"totalAmount": {"amount": "85.00"}}},
        ]
        upsell = CheckoutUpsell(cart_lines, free_shipping_threshold=100.0)
        assert upsell.should_show_upsell() is True
        rec = upsell.get_recommended_upsell()
        assert rec is not None
        assert rec.product_id == "prod_express_warranty"
        assert rec.price == 19.99

        # Gap = 70.00 > 25.00 -> recommends protective armor case
        cart_lines_low = [
            {"id": "line_4", "cost": {"totalAmount": {"amount": "30.00"}}},
        ]
        upsell_low = CheckoutUpsell(cart_lines_low, free_shipping_threshold=100.0)
        rec_low = upsell_low.get_recommended_upsell()
        assert rec_low is not None
        assert rec_low.product_id == "prod_protective_armor_case"


class TestCheckoutLoyalty:
    def test_apply_loyalty_points(self):
        loyalty = CheckoutLoyalty(customer_id="customer-123")
        result = loyalty.apply_points(100)
        assert result.success is True
        assert result.discount_amount == 10.00
        assert result.points_used == 100
        assert result.remaining_points == 150

    def test_insufficient_points_rejection(self):
        loyalty = CheckoutLoyalty(customer_id="customer-new")
        # customer-new only has 50 points
        result = loyalty.apply_points(100)
        assert result.success is False
        assert result.discount_amount == 0.0
        assert "Insufficient points" in result.message

    def test_max_discount_cap_enforcement(self):
        loyalty = CheckoutLoyalty(customer_id="customer-vip", max_discount_percentage=20.0)
        # customer-vip has 1000 points ($100 value). Cart total is $50. Max discount is 20% of $50 = $10 (100 points)
        result = loyalty.apply_points(500, cart_total=50.0)
        assert result.success is True
        assert result.discount_amount == 10.00
        assert result.points_used == 100


class TestPostPurchaseUpsell:
    def test_offer_retrieval_and_pricing(self):
        engine = PostPurchaseUpsell(order_id="DNK-ORD-9999", base_order_total=120.0)
        offer = engine.get_eligible_offer("var_cyber_armor_001")
        assert offer is not None
        assert offer.discounted_price == 19.99
        assert offer.original_price == 39.99

    def test_execute_post_purchase_upsell(self):
        engine = PostPurchaseUpsell(order_id="DNK-ORD-9999", base_order_total=120.0)
        result = engine.execute_upsell("var_cyber_armor_001")
        assert result.success is True
        assert result.added_amount == 19.99
        assert result.new_order_total == 139.99
        assert len(engine.accepted_offers) == 1

    def test_invalid_variant_rejection(self):
        engine = PostPurchaseUpsell(order_id="DNK-ORD-9999", base_order_total=120.0)
        result = engine.execute_upsell("invalid_variant_id")
        assert result.success is False
        assert result.added_amount == 0.0
        assert result.new_order_total == 120.0
