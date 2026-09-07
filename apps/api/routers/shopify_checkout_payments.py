# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_shopify_checkout_payments"
# purpose: "FastAPI router for Shopify Checkout UI Extensions, Payment Gateways, Payment Intents & Upsells (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from apps.api.services.shopify_checkout_extension import (
    ShopifyCheckoutExtensionService,
    CheckoutExtensionType,
    TargetPlacement,
    CustomFieldDefinition,
)
from apps.api.services.shopify_payment_gateway_handler import (
    ShopifyPaymentGatewayHandler,
    PaymentGatewayType,
    PaymentMethodType,
)
from apps.api.services.shopify_payment_intent_manager import (
    ShopifyPaymentIntentManager,
    RefundReason,
)
from apps.api.services.shopify_post_purchase_upsell import (
    ShopifyPostPurchaseUpsellService,
    DiscountType,
    UpsellTriggerCondition,
)
from apps.api.services.shopify_webhook_event_bus import (
    ShopifyWebhookEventBus,
    WebhookTopic,
)

router = APIRouter(prefix="/api/v1/shopify", tags=["shopify-checkout-payments"])

# Service singletons
_checkout_ext_service = ShopifyCheckoutExtensionService()
_gateway_handler = ShopifyPaymentGatewayHandler()
_intent_manager = ShopifyPaymentIntentManager()
_upsell_service = ShopifyPostPurchaseUpsellService()
_webhook_bus = ShopifyWebhookEventBus()


# -----------------------------------------------------------------------------
# DTO Models
# -----------------------------------------------------------------------------

class CreateExtensionConfigRequest(BaseModel):
    workspace_id: str
    extension_name: str
    shopify_app_id: str
    extension_type: CheckoutExtensionType = CheckoutExtensionType.CHECKOUT_UI
    target_placement: str = TargetPlacement.SHIPPING_OPTION_LIST_RENDER_AFTER.value
    custom_fields: Optional[List[CustomFieldDefinition]] = None
    api_version: str = "2024-07"
    metadata: Optional[Dict[str, Any]] = None


class ValidateCheckoutPayloadRequest(BaseModel):
    config_id: str
    submitted_fields: Dict[str, Any] = Field(default_factory=dict)


class RegisterGatewayRequest(BaseModel):
    workspace_id: str
    gateway_type: PaymentGatewayType
    gateway_name: str
    credentials: Dict[str, Any] = Field(default_factory=dict)
    supported_methods: Optional[List[PaymentMethodType]] = None
    is_test_mode: bool = True
    enabled: bool = True
    checkout_config_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TestGatewayConnectionRequest(BaseModel):
    gateway_id: str


class CreatePaymentIntentRequest(BaseModel):
    workspace_id: str
    order_id: str
    gateway_type: PaymentGatewayType = PaymentGatewayType.STRIPE
    amount_cents: int
    currency: str = "USD"
    customer_email: Optional[str] = None
    require_3ds: bool = False
    idempotency_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConfirmPaymentIntentRequest(BaseModel):
    payment_method_data: Optional[Dict[str, Any]] = None


class ThreeDSChallengeResultRequest(BaseModel):
    authentication_status: str = "authenticated"  # "authenticated" or "failed"


class CapturePaymentRequest(BaseModel):
    amount_cents: Optional[int] = None


class RefundPaymentRequest(BaseModel):
    amount_cents: Optional[int] = None
    reason: RefundReason = RefundReason.REQUESTED_BY_CUSTOMER
    note: Optional[str] = None


class CancelPaymentRequest(BaseModel):
    reason: Optional[str] = "Customer requested cancellation"


class CreateUpsellOfferRequest(BaseModel):
    workspace_id: str
    offer_name: str
    target_product_id: str
    target_variant_id: str
    original_price_cents: int
    discount_type: DiscountType
    discount_value: float
    countdown_seconds: int = 180
    custom_liquid_template: Optional[str] = None
    triggers: Optional[UpsellTriggerCondition] = None
    priority: int = 0


class EvaluateUpsellRequest(BaseModel):
    workspace_id: str
    order_total_cents: int
    cart_product_ids: List[str]
    currency: str = "USD"


class ValidateLiquidRequest(BaseModel):
    template: str


class UpsellDecisionRequest(BaseModel):
    offer_id: str
    decision: str  # "accepted" or "declined"
    order_id: str


class WebhookIngressRequest(BaseModel):
    topic: WebhookTopic
    source: str = "shopify"
    payload: Dict[str, Any] = Field(default_factory=dict)
    event_id: Optional[str] = None


# -----------------------------------------------------------------------------
# Endpoints: Checkout UI Extensions
# -----------------------------------------------------------------------------

@router.post("/checkout-extensions", summary="Create Checkout Extension Config")
def create_checkout_extension(req: CreateExtensionConfigRequest):
    cfg = _checkout_ext_service.create_extension_config(
        workspace_id=req.workspace_id,
        extension_name=req.extension_name,
        shopify_app_id=req.shopify_app_id,
        extension_type=req.extension_type,
        target_placement=req.target_placement,
        custom_fields=req.custom_fields,
        api_version=req.api_version,
        metadata=req.metadata,
    )
    return cfg.model_dump()


@router.get("/checkout-extensions/{config_id}", summary="Get Checkout Extension Config")
def get_checkout_extension(config_id: str):
    cfg = _checkout_ext_service.get_extension_config(config_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="Extension config not found")
    return cfg.model_dump()


@router.post("/checkout-extensions/validate-payload", summary="Validate Checkout Custom Fields")
def validate_checkout_payload(req: ValidateCheckoutPayloadRequest):
    is_valid, errors, sanitized = _checkout_ext_service.validate_checkout_payload(
        config_id_or_config=req.config_id,
        submitted_fields=req.submitted_fields,
    )
    return {
        "is_valid": is_valid,
        "errors": errors,
        "sanitized_values": sanitized,
    }


@router.get("/checkout-extensions/{config_id}/manifest", summary="Generate Extension Manifest")
def get_extension_manifest(config_id: str):
    try:
        manifest = _checkout_ext_service.generate_shopify_extension_manifest(config_id)
        return manifest
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/checkout-extensions/{config_id}/code", summary="Generate React/TSX Code Snippet")
def get_extension_code(config_id: str):
    try:
        code = _checkout_ext_service.generate_react_extension_snippet(config_id)
        return {"code": code}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -----------------------------------------------------------------------------
# Endpoints: Payment Gateways
# -----------------------------------------------------------------------------

@router.post("/payment-gateways", summary="Register/Configure Payment Gateway")
def register_payment_gateway(req: RegisterGatewayRequest):
    cfg = _gateway_handler.register_gateway(
        workspace_id=req.workspace_id,
        gateway_type=req.gateway_type,
        gateway_name=req.gateway_name,
        credentials=req.credentials,
        supported_methods=req.supported_methods,
        is_test_mode=req.is_test_mode,
        enabled=req.enabled,
        checkout_config_id=req.checkout_config_id,
        metadata=req.metadata,
    )
    return cfg.sanitized_dict()


@router.get("/payment-gateways/{gateway_id}", summary="Get Payment Gateway Details")
def get_payment_gateway(gateway_id: str):
    cfg = _gateway_handler.get_gateway(gateway_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="Gateway config not found")
    return cfg.sanitized_dict()


@router.post("/payment-gateways/test-connection", summary="Test Payment Gateway Connection")
def test_payment_gateway_connection(req: TestGatewayConnectionRequest):
    res = _gateway_handler.test_gateway_connection(req.gateway_id)
    return res.model_dump()


# -----------------------------------------------------------------------------
# Endpoints: Payment Intents & 3D Secure 2.0
# -----------------------------------------------------------------------------

@router.post("/payment-intents", summary="Create Payment Intent")
def create_payment_intent(req: CreatePaymentIntentRequest):
    try:
        intent = _intent_manager.create_payment_intent(
            workspace_id=req.workspace_id,
            order_id=req.order_id,
            gateway_type=req.gateway_type,
            amount_cents=req.amount_cents,
            currency=req.currency,
            customer_email=req.customer_email,
            require_3ds=req.require_3ds,
            idempotency_key=req.idempotency_key,
            metadata=req.metadata,
        )
        return intent.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payment-intents/{intent_id}", summary="Get Payment Intent")
def get_payment_intent(intent_id: str):
    intent = _intent_manager.get_payment_intent(intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="Payment Intent not found")
    return intent.model_dump()


@router.post("/payment-intents/{intent_id}/confirm", summary="Confirm Payment Intent with 3DS Handling")
def confirm_payment_intent(intent_id: str, req: Optional[ConfirmPaymentIntentRequest] = None):
    try:
        intent = _intent_manager.confirm_payment_intent(
            intent_id=intent_id,
        )
        return intent.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payment-intents/{intent_id}/3ds-challenge", summary="Handle 3DS 2.0 Challenge Result")
def handle_3ds_challenge(intent_id: str, req: ThreeDSChallengeResultRequest):
    try:
        intent = _intent_manager.complete_3ds_challenge(
            intent_id=intent_id,
            authenticated=(req.authentication_status == "authenticated"),
        )
        return intent.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payment-intents/{intent_id}/capture", summary="Capture Authorized Payment")
def capture_payment_intent(intent_id: str, req: CapturePaymentRequest):
    try:
        intent = _intent_manager.capture_payment(
            intent_id=intent_id,
            amount_cents=req.amount_cents,
        )
        return intent.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payment-intents/{intent_id}/refund", summary="Refund Payment Intent")
def refund_payment_intent(intent_id: str, req: RefundPaymentRequest):
    try:
        res = _intent_manager.refund_payment(
            intent_id=intent_id,
            amount_cents=req.amount_cents,
            reason=req.reason,
            note=req.note,
        )
        return {
            "payment_intent": res.payment_intent.model_dump(),
            "refund_record": res.refund_record.model_dump(),
            "is_full_refund": res.is_full_refund,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payment-intents/{intent_id}/cancel", summary="Cancel Payment Intent")
def cancel_payment_intent(intent_id: str, req: Optional[CancelPaymentRequest] = None):
    try:
        reason = req.reason if req else "Customer requested cancellation"
        intent = _intent_manager.cancel_payment_intent(
            intent_id=intent_id,
            cancellation_reason=reason,
        )
        return intent.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# Endpoints: Post-Purchase Upsells
# -----------------------------------------------------------------------------

@router.post("/upsell/offers", summary="Create Post-Purchase Upsell Offer")
def create_upsell_offer(req: CreateUpsellOfferRequest):
    offer = _upsell_service.create_upsell_offer(
        workspace_id=req.workspace_id,
        offer_name=req.offer_name,
        target_product_id=req.target_product_id,
        target_variant_id=req.target_variant_id,
        original_price_cents=req.original_price_cents,
        discount_type=req.discount_type,
        discount_value=req.discount_value,
        countdown_seconds=req.countdown_seconds,
        custom_liquid_template=req.custom_liquid_template,
        triggers=req.triggers,
        priority=req.priority,
    )
    return offer.model_dump()


@router.get("/upsell/offers/{offer_id}", summary="Get Upsell Offer")
def get_upsell_offer(offer_id: str):
    offer = _upsell_service.get_upsell_offer(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Upsell offer not found")
    return offer.model_dump()


@router.post("/upsell/evaluate", summary="Evaluate Matching Upsell Offer")
def evaluate_upsell(req: EvaluateUpsellRequest):
    match = _upsell_service.evaluate_matching_offers(
        workspace_id=req.workspace_id,
        order_total_cents=req.order_total_cents,
        cart_product_ids=req.cart_product_ids,
        currency=req.currency,
    )
    if not match:
        return {"matching_offer": None}
    return {"matching_offer": match.model_dump()}


@router.post("/upsell/validate-liquid", summary="Validate Liquid AST Syntax")
def validate_liquid(req: ValidateLiquidRequest):
    res = _upsell_service.validate_liquid_template(req.template)
    return res.model_dump()


@router.post("/upsell/decision", summary="Process Offer Decision")
def process_upsell_decision(req: UpsellDecisionRequest):
    try:
        res = _upsell_service.process_offer_decision(
            offer_id=req.offer_id,
            decision=req.decision,
            order_id=req.order_id,
        )
        return res.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# Endpoints: Webhooks
# -----------------------------------------------------------------------------

@router.post("/webhooks/ingress", summary="Ingest Webhook Event")
def ingest_webhook(
    req: WebhookIngressRequest,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    stripe_signature: Optional[str] = Header(None),
):
    headers = {}
    if x_shopify_hmac_sha256:
        headers["x-shopify-hmac-sha256"] = x_shopify_hmac_sha256
    if stripe_signature:
        headers["stripe-signature"] = stripe_signature

    rec = _webhook_bus.ingest_event(
        topic=req.topic,
        source=req.source,
        payload=req.payload,
        event_id=req.event_id,
        headers=headers,
    )
    return rec.model_dump()


@router.post("/webhooks/{event_id}/dispatch", summary="Dispatch Webhook Event")
def dispatch_webhook(event_id: str):
    try:
        rec = _webhook_bus.dispatch_event(event_id)
        return rec.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/webhooks/{event_id}", summary="Get Webhook Event")
def get_webhook(event_id: str):
    rec = _webhook_bus.get_event(event_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Webhook event not found")
    return rec.model_dump()
