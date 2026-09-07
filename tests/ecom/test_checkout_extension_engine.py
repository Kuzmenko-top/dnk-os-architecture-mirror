# --- DNK-MRH-HEADER ---
# mrh_id: "tests_ecom_test_checkout_extension_engine"
# purpose: "Unit tests for CheckoutExtensionEngine (DNK-ECOM-006 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.checkout_extension_engine import CheckoutExtensionEngine


def test_evaluate_rule_cart_total_and_currency():
    rule = {
        "min_cart_total": 50.0,
        "max_cart_total": 200.0,
        "allowed_currencies": ["USD", "EUR"],
    }

    # Match
    assert CheckoutExtensionEngine.evaluate_rule(rule, {
        "cart_total": 75.0,
        "currency": "USD",
    }) is True

    # Too low
    assert CheckoutExtensionEngine.evaluate_rule(rule, {
        "cart_total": 30.0,
        "currency": "USD",
    }) is False

    # Wrong currency
    assert CheckoutExtensionEngine.evaluate_rule(rule, {
        "cart_total": 100.0,
        "currency": "GBP",
    }) is False


def test_evaluate_rule_matching_and_excluded_products():
    rule = {
        "matching_product_ids": ["prod_A", "prod_B"],
        "excluded_product_ids": ["prod_C"],
    }

    # Matches prod_A, no prod_C
    assert CheckoutExtensionEngine.evaluate_rule(rule, {
        "line_items": [{"product_id": "prod_A"}, {"product_id": "prod_D"}],
    }) is True

    # Has prod_C (excluded)
    assert CheckoutExtensionEngine.evaluate_rule(rule, {
        "line_items": [{"product_id": "prod_A"}, {"product_id": "prod_C"}],
    }) is False

    # Has no matching product
    assert CheckoutExtensionEngine.evaluate_rule(rule, {
        "line_items": [{"product_id": "prod_D"}],
    }) is False


def test_filter_and_rank_extensions():
    extensions = [
        {
            "id": "ext-1",
            "extension_point": "purchase.checkout.block.render",
            "extension_type": "cross_sell",
            "status": "active",
            "priority": 5,
            "rules_payload": {"min_cart_total": 10.0},
        },
        {
            "id": "ext-2",
            "extension_point": "purchase.checkout.block.render",
            "extension_type": "banner",
            "status": "active",
            "priority": 20,
            "rules_payload": {"min_cart_total": 10.0},
        },
        {
            "id": "ext-3",
            "extension_point": "purchase.checkout.cart-line-item.render-after",
            "extension_type": "trust_badge",
            "status": "active",
            "priority": 30,
            "rules_payload": {},
        },
        {
            "id": "ext-4",
            "extension_point": "purchase.checkout.block.render",
            "extension_type": "cross_sell",
            "status": "paused",
            "priority": 50,
            "rules_payload": {},
        },
    ]

    ranked = CheckoutExtensionEngine.filter_and_rank_extensions(
        extensions=extensions,
        extension_point="purchase.checkout.block.render",
        context={"cart_total": 50.0},
    )

    assert len(ranked) == 2
    assert ranked[0]["id"] == "ext-2"  # Priority 20 > Priority 5
    assert ranked[1]["id"] == "ext-1"


def test_generate_widget_payload():
    cross_sell_ext = {
        "id": "ext-cs-1",
        "extension_point": "purchase.checkout.block.render",
        "extension_type": "cross_sell",
        "title": "Accessories",
        "config_schema": {
            "headline": "Frequently Bought Together",
            "discount_percentage": 20.0,
            "products": [
                {"product_id": "prod-acc", "title": "Eco Strap", "price": 25.0}
            ],
            "cta_text": "Add Now",
        },
    }

    widget = CheckoutExtensionEngine.generate_widget_payload(
        cross_sell_ext,
        {"currency": "USD"}
    )
    assert widget["extension_type"] == "cross_sell"
    assert widget["content"]["discount_percentage"] == 20.0
    assert widget["content"]["items"][0]["discounted_price"] == 20.0
    assert widget["content"]["items"][0]["currency"] == "USD"
