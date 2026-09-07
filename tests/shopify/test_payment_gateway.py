# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_payment_gateway"
# purpose: "Comprehensive Unit and Integration Tests for Multi-Gateway Payments & Credentials Verification (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
import pytest
from apps.api.services.shopify_payment_gateway_handler import (
    ShopifyPaymentGatewayManager,
    PaymentGatewayType,
    PaymentMethodType,
)
from apps.api.db.models.shopify_payment_gateway_config import ShopifyPaymentGatewayConfigModel
from apps.api.db.models.shopify_payment_intent import ShopifyPaymentIntentModel
from apps.api.db.models.shopify_post_purchase_upsell_config import ShopifyPostPurchaseUpsellConfigModel
from apps.api.db.models.shopify_webhook_event import ShopifyWebhookEventModel


@pytest.fixture
def gateway_manager():
    return ShopifyPaymentGatewayManager()


def test_register_and_test_stripe_gateway_success(gateway_manager):
    workspace_id = str(uuid.uuid4())
    creds = {
        "secret_key": "sk_test_mock_test_key_non_secret",
        "publishable_key": "pk_test_mock_pubkey_placeholder",
        "webhook_secret": "whsec_mock_webhook_secret_placeholder",
    }

    config = gateway_manager.register_gateway(
        workspace_id=workspace_id,
        gateway_type=PaymentGatewayType.STRIPE,
        gateway_name="Main Stripe Gateway (Test Mode)",
        credentials=creds,
        is_test_mode=True,
    )

    assert config.id is not None
    assert config.gateway_type == PaymentGatewayType.STRIPE
    assert PaymentMethodType.CARD in config.supported_methods
    assert PaymentMethodType.APPLE_PAY in config.supported_methods

    # Test connection verification
    result = gateway_manager.test_gateway_connection(config.id)
    assert result.is_connected is True
    assert "USD" in result.supported_currencies
    assert result.latency_ms > 0
    assert "Successfully connected" in result.message

    # Test sanitized credentials hygiene (no raw keys exposed in API output)
    sanitized = config.sanitized_dict()
    assert "51MzAbc1234567890TestKeySecurePass" not in sanitized["credentials"]["secret_key"]
    assert sanitized["credentials"]["secret_key"].startswith("sk_t...")


def test_stripe_gateway_invalid_credentials(gateway_manager):
    workspace_id = str(uuid.uuid4())
    invalid_creds = {
        "secret_key": "invalid_format_key",
        "publishable_key": "",
    }

    config = gateway_manager.register_gateway(
        workspace_id=workspace_id,
        gateway_type=PaymentGatewayType.STRIPE,
        gateway_name="Broken Stripe",
        credentials=invalid_creds,
    )

    result = gateway_manager.test_gateway_connection(config.id)
    assert result.is_connected is False
    assert result.error is not None
    assert "Stripe 'publishable_key' is required" in result.error


def test_register_and_test_shopify_payments(gateway_manager):
    workspace_id = str(uuid.uuid4())
    creds = {
        "shop_domain": "my-awesome-store.myshopify.com",
        "access_token": "shpat_example_mock_1234567890abcdef12345678",
    }

    config = gateway_manager.register_gateway(
        workspace_id=workspace_id,
        gateway_type=PaymentGatewayType.SHOPIFY_PAYMENTS,
        gateway_name="Shopify Native Gateway",
        credentials=creds,
    )

    result = gateway_manager.test_gateway_connection(config.id)
    assert result.is_connected is True
    assert "Successfully verified Shopify Payments" in result.message
    assert PaymentMethodType.NATIVE_SHOPIFY in result.supported_methods


def test_register_and_test_coinbase_crypto(gateway_manager):
    workspace_id = str(uuid.uuid4())
    creds = {
        "api_key": "cb_live_apiKey1234567890SecureSecret",
        "webhook_secret": "cb_whsec_mock_webhook_secret_placeholder",
    }

    config = gateway_manager.register_gateway(
        workspace_id=workspace_id,
        gateway_type=PaymentGatewayType.COINBASE,
        gateway_name="Coinbase Commerce Crypto",
        credentials=creds,
    )

    result = gateway_manager.test_gateway_connection(config.id)
    assert result.is_connected is True
    assert "BTC" in result.supported_currencies
    assert "ETH" in result.supported_currencies
    assert "USDC" in result.supported_currencies
    assert PaymentMethodType.CRYPTO in result.supported_methods


def test_list_and_delete_gateways(gateway_manager):
    ws1 = str(uuid.uuid4())
    ws2 = str(uuid.uuid4())

    g1 = gateway_manager.register_gateway(
        workspace_id=ws1,
        gateway_type=PaymentGatewayType.STRIPE,
        gateway_name="Stripe 1",
        credentials={"secret_key": "sk_test_12345678", "publishable_key": "pk_test_" + "12345678"},
    )
    g2 = gateway_manager.register_gateway(
        workspace_id=ws2,
        gateway_type=PaymentGatewayType.COINBASE,
        gateway_name="Crypto 1",
        credentials={"api_key": "123456789012345678", "webhook_secret": "secret"},
    )

    ws1_gateways = gateway_manager.list_gateways(workspace_id=ws1)
    assert len(ws1_gateways) == 1
    assert ws1_gateways[0].id == g1.id

    # Delete gateway
    deleted = gateway_manager.delete_gateway(g1.id)
    assert deleted is True
    assert gateway_manager.get_gateway(g1.id) is None


def test_orm_models_schema_integrity():
    ws_id = uuid.uuid4()
    chk_id = uuid.uuid4()

    gw_model = ShopifyPaymentGatewayConfigModel(
        checkout_config_id=chk_id,
        gateway_type="stripe",
        gateway_name="Stripe Prod",
        gateway_config={"secret_key": "sk_test_xxx"},
        is_test_mode=True,
    )
    assert gw_model.gateway_type == "stripe"

    pi_model = ShopifyPaymentIntentModel(
        workspace_id=ws_id,
        order_id="order_9988",
        gateway_type="stripe",
        payment_intent_id="pi_3MzAbc123456",
        amount_cents=9900,
        currency="USD",
        status="succeeded",
        customer_email="customer@example.com",
    )
    assert pi_model.amount_cents == 9900
    assert pi_model.status == "succeeded"

    upsell_model = ShopifyPostPurchaseUpsellConfigModel(
        checkout_config_id=chk_id,
        upsell_type="one_click_addon",
        product_ids=["prod_01", "prod_02"],
        discount_percentage=15.0,
    )
    assert upsell_model.discount_percentage == 15.0

    webhook_model = ShopifyWebhookEventModel(
        workspace_id=ws_id,
        event_type="payment/succeeded",
        payload={"order_id": "order_9988", "amount": 99.00},
        processing_status="pending",
    )
    assert webhook_model.event_type == "payment/succeeded"
