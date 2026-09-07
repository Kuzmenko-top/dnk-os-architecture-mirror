# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_payment_intents"
# purpose: "Comprehensive Unit and Integration Tests for Payment Intents & 3DS 2.0 Lifecycle (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.shopify_payment_gateway_handler import PaymentGatewayType
from apps.api.services.shopify_payment_intent_manager import (
    ShopifyPaymentIntentManager,
    PaymentIntentStatus,
    RefundReason,
)


def test_create_payment_intent_lifecycle():
    manager = ShopifyPaymentIntentManager()

    # Create Stripe intent
    intent = manager.create_payment_intent(
        workspace_id="ws_001",
        order_id="order_1001",
        gateway_type=PaymentGatewayType.STRIPE,
        amount_cents=15000,
        currency="USD",
        customer_email="customer@example.com",
    )
    assert intent.status == PaymentIntentStatus.PENDING
    assert intent.amount_cents == 15000
    assert intent.currency == "USD"
    assert intent.payment_intent_id.startswith("pi_stripe_")
    assert intent.amount_captured_cents == 0

    # Confirm intent
    confirmed = manager.confirm_payment_intent(intent.id)
    assert confirmed.status == PaymentIntentStatus.SUCCEEDED
    assert confirmed.amount_captured_cents == 15000


def test_payment_intent_idempotency():
    manager = ShopifyPaymentIntentManager()
    idempotency_key = "idem_key_abc_123"

    intent1 = manager.create_payment_intent(
        workspace_id="ws_001",
        order_id="order_1002",
        gateway_type=PaymentGatewayType.SHOPIFY_PAYMENTS,
        amount_cents=25000,
        currency="EUR",
        idempotency_key=idempotency_key,
    )

    intent2 = manager.create_payment_intent(
        workspace_id="ws_001",
        order_id="order_1002",
        gateway_type=PaymentGatewayType.SHOPIFY_PAYMENTS,
        amount_cents=25000,
        currency="EUR",
        idempotency_key=idempotency_key,
    )

    assert intent1.id == intent2.id
    assert intent1.payment_intent_id == intent2.payment_intent_id


def test_3d_secure_2_challenge_success_and_failure():
    manager = ShopifyPaymentIntentManager()

    # 1. 3DS Success Flow
    intent_3ds = manager.create_payment_intent(
        workspace_id="ws_001",
        order_id="order_1003",
        gateway_type=PaymentGatewayType.STRIPE,
        amount_cents=8000,
        currency="GBP",
        require_3ds=True,
    )
    assert intent_3ds.status == PaymentIntentStatus.REQUIRES_ACTION
    assert intent_3ds.three_d_secure_state.is_required is True
    assert intent_3ds.three_d_secure_state.status == "challenge_required"
    assert intent_3ds.three_d_secure_state.challenge_url is not None
    assert "3ds-verify.gateway.io" in intent_3ds.three_d_secure_state.challenge_url

    # Complete challenge successfully
    authenticated = manager.complete_3ds_challenge(intent_3ds.id, authenticated=True)
    assert authenticated.status == PaymentIntentStatus.SUCCEEDED
    assert authenticated.three_d_secure_state.status == "authenticated"
    assert authenticated.amount_captured_cents == 8000

    # 2. 3DS Failure Flow
    intent_3ds_fail = manager.create_payment_intent(
        workspace_id="ws_001",
        order_id="order_1004",
        gateway_type=PaymentGatewayType.STRIPE,
        amount_cents=4500,
        currency="USD",
        require_3ds=True,
    )
    failed = manager.complete_3ds_challenge(intent_3ds_fail.id, authenticated=False)
    assert failed.status == PaymentIntentStatus.FAILED
    assert failed.three_d_secure_state.status == "failed"
    assert failed.amount_captured_cents == 0


def test_refund_lifecycle_partial_and_full():
    manager = ShopifyPaymentIntentManager()

    intent = manager.create_payment_intent(
        workspace_id="ws_001",
        order_id="order_1005",
        gateway_type=PaymentGatewayType.STRIPE,
        amount_cents=10000,
        currency="USD",
    )
    manager.confirm_payment_intent(intent.id)

    # Partial refund $40
    res1 = manager.refund_payment(
        intent.id,
        amount_cents=4000,
        reason=RefundReason.REQUESTED_BY_CUSTOMER,
        note="Customer changed mind on item 1",
    )
    assert res1.is_full_refund is False
    assert res1.payment_intent.status == PaymentIntentStatus.PARTIALLY_REFUNDED
    assert res1.payment_intent.amount_refunded_cents == 4000
    assert len(res1.payment_intent.refunds) == 1

    # Remaining refund $60 -> Full refund
    res2 = manager.refund_payment(
        intent.id,
        amount_cents=6000,
        reason=RefundReason.REQUESTED_BY_CUSTOMER,
    )
    assert res2.is_full_refund is True
    assert res2.payment_intent.status == PaymentIntentStatus.REFUNDED
    assert res2.payment_intent.amount_refunded_cents == 10000
    assert len(res2.payment_intent.refunds) == 2


def test_cancel_payment_intent():
    manager = ShopifyPaymentIntentManager()

    intent = manager.create_payment_intent(
        workspace_id="ws_001",
        order_id="order_1006",
        gateway_type=PaymentGatewayType.COINBASE,
        amount_cents=50000,
        currency="USDC",
    )
    cancelled = manager.cancel_payment_intent(intent.id, cancellation_reason="Abandoned cart")
    assert cancelled.status == PaymentIntentStatus.CANCELLED
    assert cancelled.metadata.get("cancellation_reason") == "Abandoned cart"

    # Cannot cancel already succeeded intent
    intent_succeeded = manager.create_payment_intent(
        workspace_id="ws_001",
        order_id="order_1007",
        gateway_type=PaymentGatewayType.STRIPE,
        amount_cents=2000,
    )
    manager.confirm_payment_intent(intent_succeeded.id)
    with pytest.raises(ValueError, match="Cannot cancel settled payment intent"):
        manager.cancel_payment_intent(intent_succeeded.id)


def test_validation_errors():
    manager = ShopifyPaymentIntentManager()

    with pytest.raises(ValueError, match="Payment amount must be greater than 0"):
        manager.create_payment_intent(
            workspace_id="ws_001",
            order_id="order_bad",
            gateway_type=PaymentGatewayType.STRIPE,
            amount_cents=0,
        )

    intent = manager.create_payment_intent(
        workspace_id="ws_001",
        order_id="order_bad2",
        gateway_type=PaymentGatewayType.STRIPE,
        amount_cents=5000,
    )

    with pytest.raises(ValueError, match="Cannot refund payment intent in status"):
        manager.refund_payment(intent.id, amount_cents=1000)
