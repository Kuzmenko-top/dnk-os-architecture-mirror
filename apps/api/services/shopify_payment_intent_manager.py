# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_payment_intent_manager"
# purpose: "Payment Intent Lifecycle Management, 3DS 2.0 Challenge Handler & Multi-Gateway Processing (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from apps.api.services.shopify_payment_gateway_handler import PaymentGatewayType


class PaymentIntentStatus(str, Enum):
    PENDING = "pending"
    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTION = "requires_action"  # 3D Secure 2.0 Challenge
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"


class RefundReason(str, Enum):
    DUPLICATE = "duplicate"
    FRAUDULENT = "fraudulent"
    REQUESTED_BY_CUSTOMER = "requested_by_customer"
    PRODUCT_DEFECT = "product_defect"


class ThreeDSecureState(BaseModel):
    is_required: bool = False
    status: str = "not_required"  # "not_required", "frictionless", "challenge_required", "authenticated", "failed"
    version: str = "2.2.0"
    challenge_url: Optional[str] = None
    three_ds_server_trans_id: Optional[str] = None


class RefundRecord(BaseModel):
    refund_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amount_cents: int
    currency: str
    reason: RefundReason
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaymentIntentRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    order_id: str
    gateway_type: PaymentGatewayType
    payment_intent_id: str
    amount_cents: int
    currency: str
    status: PaymentIntentStatus = PaymentIntentStatus.PENDING
    customer_email: Optional[str] = None
    amount_captured_cents: int = 0
    amount_refunded_cents: int = 0
    idempotency_key: Optional[str] = None
    three_d_secure_state: ThreeDSecureState = Field(default_factory=ThreeDSecureState)
    refunds: List[RefundRecord] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Tuple_RefundResult(BaseModel):
    payment_intent: PaymentIntentRecord
    refund_record: RefundRecord
    is_full_refund: bool


class ShopifyPaymentIntentManager:
    """Manages payment intent states, 3D Secure 2.0 SCA challenges, captures, and refunds."""

    def __init__(self, db_session=None):
        self.db_session = db_session
        self._intents: Dict[str, PaymentIntentRecord] = {}
        self._idempotency_index: Dict[str, str] = {}  # idempotency_key -> intent_id

    def create_payment_intent(
        self,
        workspace_id: str,
        order_id: str,
        gateway_type: PaymentGatewayType,
        amount_cents: int,
        currency: str = "USD",
        customer_email: Optional[str] = None,
        require_3ds: bool = False,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentIntentRecord:
        if amount_cents <= 0:
            raise ValueError("Payment amount must be greater than 0.")

        currency = currency.upper()

        if idempotency_key and idempotency_key in self._idempotency_index:
            existing_id = self._idempotency_index[idempotency_key]
            return self._intents[existing_id]

        # Generate gateway-specific external intent ID
        prefix_map = {
            PaymentGatewayType.STRIPE: "pi_stripe_",
            PaymentGatewayType.SHOPIFY_PAYMENTS: "shppi_",
            PaymentGatewayType.COINBASE: "cb_charge_",
        }
        external_id = f"{prefix_map.get(gateway_type, 'pi_')}{uuid.uuid4().hex[:16]}"

        three_ds = ThreeDSecureState()
        status = PaymentIntentStatus.PENDING

        if require_3ds:
            three_ds.is_required = True
            three_ds.status = "challenge_required"
            three_ds.challenge_url = f"https://3ds-verify.gateway.io/challenge/{external_id}"
            three_ds.three_ds_server_trans_id = str(uuid.uuid4())
            status = PaymentIntentStatus.REQUIRES_ACTION

        intent = PaymentIntentRecord(
            workspace_id=workspace_id,
            order_id=order_id,
            gateway_type=gateway_type,
            payment_intent_id=external_id,
            amount_cents=amount_cents,
            currency=currency,
            status=status,
            customer_email=customer_email,
            idempotency_key=idempotency_key,
            three_d_secure_state=three_ds,
            metadata=metadata or {},
        )

        self._intents[intent.id] = intent
        if idempotency_key:
            self._idempotency_index[idempotency_key] = intent.id

        return intent

    def get_payment_intent(self, intent_id_or_external_id: str) -> Optional[PaymentIntentRecord]:
        if intent_id_or_external_id in self._intents:
            return self._intents[intent_id_or_external_id]
        for intent in self._intents.values():
            if intent.payment_intent_id == intent_id_or_external_id:
                return intent
        return None

    def list_payment_intents(
        self,
        workspace_id: Optional[str] = None,
        order_id: Optional[str] = None,
        status: Optional[PaymentIntentStatus] = None,
    ) -> List[PaymentIntentRecord]:
        res = list(self._intents.values())
        if workspace_id:
            res = [i for i in res if i.workspace_id == workspace_id]
        if order_id:
            res = [i for i in res if i.order_id == order_id]
        if status:
            res = [i for i in res if i.status == status]
        return res

    def confirm_payment_intent(self, intent_id: str) -> PaymentIntentRecord:
        intent = self.get_payment_intent(intent_id)
        if not intent:
            raise ValueError(f"Payment intent '{intent_id}' not found.")

        if intent.status in [PaymentIntentStatus.SUCCEEDED, PaymentIntentStatus.CANCELLED, PaymentIntentStatus.REFUNDED]:
            raise ValueError(f"Cannot confirm payment intent in terminal state '{intent.status}'.")

        if intent.three_d_secure_state.is_required and intent.three_d_secure_state.status != "authenticated":
            intent.status = PaymentIntentStatus.REQUIRES_ACTION
            intent.updated_at = datetime.now(timezone.utc)
            return intent

        intent.status = PaymentIntentStatus.SUCCEEDED
        intent.amount_captured_cents = intent.amount_cents
        intent.updated_at = datetime.now(timezone.utc)
        return intent

    def complete_3ds_challenge(self, intent_id: str, authenticated: bool = True) -> PaymentIntentRecord:
        intent = self.get_payment_intent(intent_id)
        if not intent:
            raise ValueError(f"Payment intent '{intent_id}' not found.")

        if intent.status != PaymentIntentStatus.REQUIRES_ACTION:
            raise ValueError(f"Payment intent '{intent_id}' is not awaiting 3DS action (status: {intent.status}).")

        if authenticated:
            intent.three_d_secure_state.status = "authenticated"
            intent.status = PaymentIntentStatus.SUCCEEDED
            intent.amount_captured_cents = intent.amount_cents
        else:
            intent.three_d_secure_state.status = "failed"
            intent.status = PaymentIntentStatus.FAILED

        intent.updated_at = datetime.now(timezone.utc)
        return intent

    def capture_payment(self, intent_id: str, amount_cents: Optional[int] = None) -> PaymentIntentRecord:
        intent = self.get_payment_intent(intent_id)
        if not intent:
            raise ValueError(f"Payment intent '{intent_id}' not found.")

        capture_amount = amount_cents or (intent.amount_cents - intent.amount_captured_cents)
        if capture_amount <= 0:
            raise ValueError("Capture amount must be greater than 0.")

        if intent.amount_captured_cents + capture_amount > intent.amount_cents:
            raise ValueError(
                f"Capture amount {capture_amount} exceeds uncaptured balance {intent.amount_cents - intent.amount_captured_cents}."
            )

        intent.amount_captured_cents += capture_amount
        intent.status = PaymentIntentStatus.SUCCEEDED
        intent.updated_at = datetime.now(timezone.utc)
        return intent

    def refund_payment(
        self,
        intent_id: str,
        amount_cents: Optional[int] = None,
        reason: RefundReason = RefundReason.REQUESTED_BY_CUSTOMER,
        note: Optional[str] = None,
    ) -> Tuple_RefundResult:
        intent = self.get_payment_intent(intent_id)
        if not intent:
            raise ValueError(f"Payment intent '{intent_id}' not found.")

        if intent.status not in [PaymentIntentStatus.SUCCEEDED, PaymentIntentStatus.PARTIALLY_REFUNDED]:
            raise ValueError(f"Cannot refund payment intent in status '{intent.status}'. Payment must be succeeded.")

        available_to_refund = intent.amount_captured_cents - intent.amount_refunded_cents
        refund_amount = amount_cents or available_to_refund

        if refund_amount <= 0:
            raise ValueError("Refund amount must be greater than 0.")

        if refund_amount > available_to_refund:
            raise ValueError(f"Refund amount {refund_amount} exceeds available refundable amount {available_to_refund}.")

        refund_record = RefundRecord(
            amount_cents=refund_amount,
            currency=intent.currency,
            reason=reason,
            note=note,
        )
        intent.refunds.append(refund_record)
        intent.amount_refunded_cents += refund_amount

        if intent.amount_refunded_cents == intent.amount_captured_cents:
            intent.status = PaymentIntentStatus.REFUNDED
        else:
            intent.status = PaymentIntentStatus.PARTIALLY_REFUNDED

        intent.updated_at = datetime.now(timezone.utc)

        return Tuple_RefundResult(
            payment_intent=intent,
            refund_record=refund_record,
            is_full_refund=intent.status == PaymentIntentStatus.REFUNDED,
        )

    def cancel_payment_intent(self, intent_id: str, cancellation_reason: Optional[str] = None) -> PaymentIntentRecord:
        intent = self.get_payment_intent(intent_id)
        if not intent:
            raise ValueError(f"Payment intent '{intent_id}' not found.")

        if intent.status in [PaymentIntentStatus.SUCCEEDED, PaymentIntentStatus.REFUNDED, PaymentIntentStatus.PARTIALLY_REFUNDED]:
            raise ValueError(f"Cannot cancel settled payment intent in status '{intent.status}'.")

        intent.status = PaymentIntentStatus.CANCELLED
        if cancellation_reason:
            intent.metadata["cancellation_reason"] = cancellation_reason
        intent.updated_at = datetime.now(timezone.utc)
        return intent
