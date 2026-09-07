# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_post_purchase_upsell"
# purpose: "Comprehensive Unit and Integration Tests for Post-Purchase Upsell Engine & AST Liquid Validator (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.shopify_post_purchase_upsell import (
    ShopifyPostPurchaseUpsellService,
    DiscountType,
    UpsellTriggerCondition,
)


def test_create_and_discount_calculation():
    service = ShopifyPostPurchaseUpsellService()

    # 1. 20% discount on $50.00 (5000 cents) -> $40.00 (4000 cents)
    offer_pct = service.create_upsell_offer(
        workspace_id="ws_001",
        offer_name="Matching Leather Belt 20% Off",
        target_product_id="prod_belt_123",
        target_variant_id="var_belt_m",
        original_price_cents=5000,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=20.0,
        countdown_seconds=120,
    )
    assert offer_pct.calculated_price_cents == 4000
    assert offer_pct.countdown_seconds == 120

    # 2. $15.00 fixed discount on $60.00 (6000 cents) -> $45.00 (4500 cents)
    offer_fixed = service.create_upsell_offer(
        workspace_id="ws_001",
        offer_name="Shoe Care Kit $15 Off",
        target_product_id="prod_kit_456",
        target_variant_id="var_kit_std",
        original_price_cents=6000,
        discount_type=DiscountType.FIXED_AMOUNT,
        discount_value=1500,
    )
    assert offer_fixed.calculated_price_cents == 4500


def test_liquid_ast_syntax_validation():
    service = ShopifyPostPurchaseUpsellService()

    # Valid template
    valid_liquid = """
    <div class="upsell-container">
      {% if customer.name %}
        <h3>Special offer for {{ customer.name }}!</h3>
      {% endif %}
      <p>Add this for only {{ offer.price | money }}</p>
    </div>
    """
    res_valid = service.validate_liquid_template(valid_liquid)
    assert res_valid.is_valid is True
    assert len(res_valid.errors) == 0
    assert res_valid.ast_tokens_count > 0

    # Invalid template with mismatched tag
    invalid_liquid = """
    <div>
      {% if offer.available %}
        <span>Limited Stock!</span>
      {% for item in collections.featured %}
        <p>{{ item.title }}</p>
      {% endif %}
    </div>
    """
    res_invalid = service.validate_liquid_template(invalid_liquid)
    assert res_invalid.is_valid is False
    assert any("Mismatched Liquid tag: 'for'" in err for err in res_invalid.errors)


def test_evaluate_matching_offers_criteria():
    service = ShopifyPostPurchaseUpsellService()

    # Offer A: high priority (20), requires order >= $100 and specific product
    service.create_upsell_offer(
        workspace_id="ws_001",
        offer_name="VIP Watch Upsell",
        target_product_id="prod_watch_789",
        target_variant_id="var_watch_gold",
        original_price_cents=20000,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=30.0,
        priority=20,
        triggers=UpsellTriggerCondition(
            min_order_total_cents=10000,
            included_product_ids=["prod_shoes_100"],
            currency="USD",
        ),
    )

    # Offer B: lower priority (10), requires order >= $30
    service.create_upsell_offer(
        workspace_id="ws_001",
        offer_name="Socks Bundle",
        target_product_id="prod_socks_200",
        target_variant_id="var_socks_pack",
        original_price_cents=1500,
        discount_type=DiscountType.FIXED_AMOUNT,
        discount_value=500,
        priority=10,
        triggers=UpsellTriggerCondition(
            min_order_total_cents=3000,
            currency="USD",
        ),
    )

    # Match for $120 order with shoes -> should pick Offer A (higher priority)
    match1 = service.evaluate_matching_offers(
        workspace_id="ws_001",
        order_total_cents=12000,
        cart_product_ids=["prod_shoes_100", "prod_shirt_50"],
        currency="USD",
    )
    assert match1 is not None
    assert match1.offer_name == "VIP Watch Upsell"

    # Match for $50 order without shoes -> should pick Offer B
    match2 = service.evaluate_matching_offers(
        workspace_id="ws_001",
        order_total_cents=5000,
        cart_product_ids=["prod_shirt_50"],
        currency="USD",
    )
    assert match2 is not None
    assert match2.offer_name == "Socks Bundle"

    # If target product is already in cart, should not trigger it
    match3 = service.evaluate_matching_offers(
        workspace_id="ws_001",
        order_total_cents=5000,
        cart_product_ids=["prod_socks_200"],
        currency="USD",
    )
    assert match3 is None


def test_process_offer_decision():
    service = ShopifyPostPurchaseUpsellService()

    offer = service.create_upsell_offer(
        workspace_id="ws_001",
        offer_name="Hat Upsell",
        target_product_id="prod_hat_1",
        target_variant_id="var_hat_1",
        original_price_cents=3000,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,  # $27.00 = 2700 cents
    )

    # Accept
    acc = service.process_offer_decision(offer.id, decision="accepted", order_id="order_999")
    assert acc.decision == "accepted"
    assert acc.added_amount_cents == 2700

    # Decline
    dec = service.process_offer_decision(offer.id, decision="declined", order_id="order_999")
    assert dec.decision == "declined"
    assert dec.added_amount_cents == 0

    # Invalid decision
    with pytest.raises(ValueError, match="Decision must be either 'accepted' or 'declined'"):
        service.process_offer_decision(offer.id, decision="maybe", order_id="order_999")
