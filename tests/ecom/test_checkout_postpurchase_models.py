# --- DNK-MRH-HEADER ---
# mrh_id: "tests_ecom_test_checkout_postpurchase_models"
# purpose: "Unit tests for DNK-ECOM-006 Phase 1 ORM Models"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone

from apps.api.db.models.checkout_extension import CheckoutExtensionModel
from apps.api.db.models.post_purchase_offer import PostPurchaseOfferModel
from apps.api.db.models.upsell_rule import UpsellRuleModel
from apps.api.db.models.checkout_conversion_event import CheckoutConversionEventModel
from apps.api.db.models.shopify_webhook_event import ShopifyWebhookEventModel


def test_checkout_extension_model_to_dict():
    ext = CheckoutExtensionModel(
        id="ext-001",
        workspace_id="ws-001",
        shop_domain="shop.dnk-e.com",
        title="Eco Protection Plan",
        extension_point="purchase.checkout.block.render",
        extension_type="cross_sell",
        status="active",
        priority=1,
        config_schema={"theme": "dark"},
        rules_payload={"min_price": 50.0},
    )
    data = ext.to_dict()
    assert data["id"] == "ext-001"
    assert data["shop_domain"] == "shop.dnk-e.com"
    assert data["extension_type"] == "cross_sell"
    assert data["status"] == "active"
    assert data["config_schema"]["theme"] == "dark"


def test_post_purchase_offer_model_to_dict():
    offer = PostPurchaseOfferModel(
        id="offer-001",
        workspace_id="ws-001",
        shop_domain="shop.dnk-e.com",
        name="VIP VIP Upgrade",
        headline="Unlock 20% off your next item!",
        product_id="prod-123",
        variant_id="var-456",
        discount_type="percentage",
        discount_value=20.0,
        original_price=100.0,
        offer_price=80.0,
        currency="USD",
        priority=1,
        status="active",
        trigger_rules={"tier": "gold"},
        timer_seconds=180,
    )
    data = offer.to_dict()
    assert data["id"] == "offer-001"
    assert data["headline"] == "Unlock 20% off your next item!"
    assert data["discount_value"] == 20.0
    assert data["offer_price"] == 80.0
    assert data["timer_seconds"] == 180


def test_upsell_rule_model_to_dict():
    rule = UpsellRuleModel(
        id="rule-001",
        workspace_id="ws-001",
        shop_domain="shop.dnk-e.com",
        name="High Value Cart Rule",
        rule_type="cart_value",
        min_cart_value=150.0,
        max_cart_value=500.0,
        matching_product_ids=["p-1", "p-2"],
        matching_collection_ids=["col-1"],
        customer_tags=["vip", "wholesale"],
        action_type="recommend_upsell",
        target_offer_id="offer-001",
        priority=5,
        is_active=1,
    )
    data = rule.to_dict()
    assert data["id"] == "rule-001"
    assert data["min_cart_value"] == 150.0
    assert data["is_active"] is True
    assert "vip" in data["customer_tags"]


def test_checkout_conversion_event_model_to_dict():
    event = CheckoutConversionEventModel(
        id="ev-001",
        workspace_id="ws-001",
        shop_domain="shop.dnk-e.com",
        checkout_token="tok-abc",
        order_id="ord-789",
        offer_id="offer-001",
        extension_id="ext-001",
        event_type="CONVERSION",
        channel="post_purchase",
        revenue_impact=80.0,
        currency="USD",
        metadata_payload={"coupon": "DNK20"},
    )
    data = event.to_dict()
    assert data["id"] == "ev-001"
    assert data["event_type"] == "CONVERSION"
    assert data["revenue_impact"] == 80.0
    assert data["metadata_payload"]["coupon"] == "DNK20"


def test_shopify_webhook_event_model_to_dict():
    webhook = ShopifyWebhookEventModel(
        id="wh-001",
        workspace_id="ws-001",
        shop_domain="shop.dnk-e.com",
        webhook_id="wh-shopify-999",
        topic="orders/create",
        api_version="2026-04",
        hmac_verified=1,
        status="processed",
        payload={"order": {"id": 12345}},
    )
    data = webhook.to_dict()
    assert data["id"] == "wh-001"
    assert data["webhook_id"] == "wh-shopify-999"
    assert data["topic"] == "orders/create"
    assert data["hmac_verified"] is True
    assert data["payload"]["order"]["id"] == 12345
