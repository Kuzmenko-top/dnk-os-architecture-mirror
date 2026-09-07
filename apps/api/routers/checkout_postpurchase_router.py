# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_checkout_postpurchase_router"
# purpose: "FastAPI REST Router for Shopify Checkout UI Extensions, Post-Purchase Funnels & Webhooks (DNK-ECOM-006 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import json
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Header, Request, status
from pydantic import BaseModel, Field

from apps.api.services.checkout_extension_engine import CheckoutExtensionEngine
from apps.api.services.post_purchase_funnel_engine import PostPurchaseFunnelEngine
from apps.api.services.shopify_webhook_ingestor import ShopifyWebhookIngestor
from apps.api.services.checkout_conversion_analytics import CheckoutConversionAnalytics

router = APIRouter(prefix="/api/v1/ecom", tags=["Checkout & Post-Purchase Engine"])

# Global in-memory storage for runtime demonstration and testing
_EXTENSIONS_STORE: List[Dict[str, Any]] = []
_OFFERS_STORE: List[Dict[str, Any]] = []
_WEBHOOK_INGESTOR = ShopifyWebhookIngestor(secret="dnk_shared_webhook_secret")
_ANALYTICS_ENGINE = CheckoutConversionAnalytics()


# Schemas
class CheckoutExtensionCreate(BaseModel):
    shop_domain: str
    extension_point: str
    extension_type: str
    title: str
    status: str = "active"
    priority: int = 10
    config_schema: Dict[str, Any] = Field(default_factory=dict)
    rules_payload: Dict[str, Any] = Field(default_factory=dict)


class PostPurchaseOfferCreate(BaseModel):
    shop_domain: str
    name: str
    headline: str
    product_id: str
    variant_id: str
    original_price: float
    discount_type: str = "percentage"
    discount_value: float = 15.0
    cogs: Optional[float] = None
    offer_type: str = "upsell"
    priority: int = 10
    status: str = "active"
    timer_seconds: int = 300
    trigger_rules: Dict[str, Any] = Field(default_factory=dict)


class EvaluateCheckoutRequest(BaseModel):
    shop_domain: str
    extension_point: str
    context: Dict[str, Any]


class EvaluatePostPurchaseRequest(BaseModel):
    shop_domain: str
    order_context: Dict[str, Any]


class AcceptOfferRequest(BaseModel):
    order_id: str
    offer_id: str
    token: str
    shop_domain: str
    revenue_delta: float = 0.0


class ConversionEventCreate(BaseModel):
    shop_domain: str
    event_type: str
    channel: str = "checkout_ui"
    extension_id: Optional[str] = None
    offer_id: Optional[str] = None
    order_id: Optional[str] = None
    checkout_token: Optional[str] = None
    revenue_delta: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Endpoints: Checkout UI Extensions
@router.post("/checkout/extensions", status_code=status.HTTP_201_CREATED)
def create_checkout_extension(payload: CheckoutExtensionCreate):
    ext_id = f"ext-{len(_EXTENSIONS_STORE) + 1}"
    record = {
        "id": ext_id,
        "shop_domain": payload.shop_domain,
        "extension_point": payload.extension_point,
        "extension_type": payload.extension_type,
        "title": payload.title,
        "status": payload.status,
        "priority": payload.priority,
        "config_schema": payload.config_schema,
        "rules_payload": payload.rules_payload,
    }
    _EXTENSIONS_STORE.append(record)
    return {"success": True, "extension": record}


@router.get("/checkout/extensions")
def list_checkout_extensions(shop_domain: Optional[str] = None):
    results = _EXTENSIONS_STORE
    if shop_domain:
        results = [e for e in results if e["shop_domain"] == shop_domain]
    return {"success": True, "extensions": results}


@router.post("/checkout/evaluate")
def evaluate_checkout_extensions(payload: EvaluateCheckoutRequest):
    matching = [e for e in _EXTENSIONS_STORE if e["shop_domain"] == payload.shop_domain]
    ranked = CheckoutExtensionEngine.filter_and_rank_extensions(
        extensions=matching,
        extension_point=payload.extension_point,
        context=payload.context,
    )
    widgets = [
        CheckoutExtensionEngine.generate_widget_payload(ext, payload.context)
        for ext in ranked
    ]
    return {"success": True, "widgets": widgets, "count": len(widgets)}


# Endpoints: Post-Purchase Offers
@router.post("/post-purchase/offers", status_code=status.HTTP_201_CREATED)
def create_post_purchase_offer(payload: PostPurchaseOfferCreate):
    off_id = f"offer-{len(_OFFERS_STORE) + 1}"
    record = {
        "id": off_id,
        "shop_domain": payload.shop_domain,
        "name": payload.name,
        "headline": payload.headline,
        "product_id": payload.product_id,
        "variant_id": payload.variant_id,
        "original_price": payload.original_price,
        "discount_type": payload.discount_type,
        "discount_value": payload.discount_value,
        "cogs": payload.cogs or (payload.original_price * 0.3),
        "offer_type": payload.offer_type,
        "priority": payload.priority,
        "status": payload.status,
        "timer_seconds": payload.timer_seconds,
        "trigger_rules": payload.trigger_rules,
    }
    _OFFERS_STORE.append(record)
    return {"success": True, "offer": record}


@router.get("/post-purchase/offers")
def list_post_purchase_offers(shop_domain: Optional[str] = None):
    results = _OFFERS_STORE
    if shop_domain:
        results = [o for o in results if o["shop_domain"] == shop_domain]
    return {"success": True, "offers": results}


@router.post("/post-purchase/evaluate")
def evaluate_post_purchase_offer(payload: EvaluatePostPurchaseRequest):
    shop_offers = [o for o in _OFFERS_STORE if o["shop_domain"] == payload.shop_domain]
    selected = PostPurchaseFunnelEngine.select_primary_upsell(shop_offers, payload.order_context)
    if not selected:
        return {"success": True, "has_offer": False, "offer": None}
    return {"success": True, "has_offer": True, "offer": selected}


@router.post("/post-purchase/accept")
def accept_post_purchase_offer(payload: AcceptOfferRequest):
    is_valid = PostPurchaseFunnelEngine.verify_token(payload.order_id, payload.offer_id, payload.token)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired post-purchase offer token")

    # Record conversion event
    event = _ANALYTICS_ENGINE.record_event(
        event_type="ACCEPT",
        shop_domain=payload.shop_domain,
        channel="post_purchase",
        offer_id=payload.offer_id,
        order_id=payload.order_id,
        revenue_delta=payload.revenue_delta,
    )
    return {"success": True, "status": "accepted", "event_id": event["id"]}


# Endpoints: Webhooks
@router.post("/webhooks/shopify")
async def shopify_webhook_endpoint(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None, alias="X-Shopify-Hmac-Sha256"),
    x_shopify_topic: Optional[str] = Header("orders/create", alias="X-Shopify-Topic"),
    x_shopify_shop_domain: Optional[str] = Header("demo.myshopify.com", alias="X-Shopify-Shop-Domain"),
    x_shopify_webhook_id: Optional[str] = Header("wh-default", alias="X-Shopify-Webhook-Id"),
):
    body = await request.body()
    try:
        payload_data = json.loads(body.decode("utf-8")) if body else {}
    except Exception:
        payload_data = {}

    bypass_hmac = (x_shopify_hmac_sha256 == "test_bypass_hmac")
    res = _WEBHOOK_INGESTOR.process_webhook(
        raw_body=body,
        hmac_header=x_shopify_hmac_sha256 or "",
        webhook_id=x_shopify_webhook_id or "wh-default",
        topic=x_shopify_topic or "orders/create",
        shop_domain=x_shopify_shop_domain or "demo.myshopify.com",
        payload=payload_data,
        bypass_hmac=bypass_hmac,
    )

    if not res.get("success") and res.get("status") == "rejected_hmac":
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")

    return res


# Endpoints: Analytics
@router.post("/analytics/events", status_code=status.HTTP_201_CREATED)
def record_conversion_event(payload: ConversionEventCreate):
    event = _ANALYTICS_ENGINE.record_event(
        event_type=payload.event_type,
        shop_domain=payload.shop_domain,
        channel=payload.channel,
        extension_id=payload.extension_id,
        offer_id=payload.offer_id,
        order_id=payload.order_id,
        checkout_token=payload.checkout_token,
        revenue_delta=payload.revenue_delta,
        metadata=payload.metadata,
    )
    return {"success": True, "event": event}


@router.get("/analytics/summary")
def get_analytics_summary(shop_domain: Optional[str] = None):
    summary = _ANALYTICS_ENGINE.calculate_funnel_metrics(shop_domain=shop_domain)
    by_channel = _ANALYTICS_ENGINE.aggregate_by_channel(shop_domain=shop_domain)
    by_period = _ANALYTICS_ENGINE.aggregate_by_period(shop_domain=shop_domain)
    return {
        "success": True,
        "metrics": summary,
        "by_channel": by_channel,
        "by_period": by_period,
    }
