# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/shopify_webhooks.py"
# purpose: "FastAPI REST API router for Shopify Inbound Webhooks with HMAC Verification."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
from fastapi import APIRouter, Request, Header, HTTPException, status
from typing import Optional
from ..services.shopify_webhook_bridge import ShopifyWebhookBridge

router = APIRouter(prefix="/shopify/webhooks", tags=["Shopify Webhooks"])

webhook_bridge = ShopifyWebhookBridge(webhook_secret="whsec_test_secret")


async def _verify_and_process(request: Request, topic: str, hmac_header: Optional[str]):
    body = await request.body()
    if not webhook_bridge.verify_hmac(body, hmac_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Shopify HMAC-SHA256 signature",
        )
    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except Exception:
        payload = {}
    return await webhook_bridge.process_webhook(payload, topic)


@router.post("/orders/create")
async def webhook_order_create(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None, alias="X-Shopify-Hmac-SHA256"),
    x_shopify_topic: Optional[str] = Header("orders/create", alias="X-Shopify-Topic"),
):
    """
    Shopify Inbound Webhook endpoint for Order Creation events.
    """
    topic = x_shopify_topic or "orders/create"
    return await _verify_and_process(request, topic, x_shopify_hmac_sha256)


@router.post("/products/update")
async def webhook_product_update(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None, alias="X-Shopify-Hmac-SHA256"),
    x_shopify_topic: Optional[str] = Header("products/update", alias="X-Shopify-Topic"),
):
    """
    Shopify Inbound Webhook endpoint for Product Update events.
    """
    topic = x_shopify_topic or "products/update"
    return await _verify_and_process(request, topic, x_shopify_hmac_sha256)


@router.post("/app/uninstalled")
async def webhook_app_uninstalled(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None, alias="X-Shopify-Hmac-SHA256"),
    x_shopify_topic: Optional[str] = Header("app/uninstalled", alias="X-Shopify-Topic"),
):
    """
    Shopify Inbound Webhook endpoint for App Uninstallation (GDPR cleanup).
    """
    topic = x_shopify_topic or "app/uninstalled"
    return await _verify_and_process(request, topic, x_shopify_hmac_sha256)


@router.post("/generic")
async def webhook_generic(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None, alias="X-Shopify-Hmac-SHA256"),
    x_shopify_topic: Optional[str] = Header("custom", alias="X-Shopify-Topic"),
):
    """
    Generic Shopify Inbound Webhook endpoint.
    """
    topic = x_shopify_topic or "custom"
    return await _verify_and_process(request, topic, x_shopify_hmac_sha256)
