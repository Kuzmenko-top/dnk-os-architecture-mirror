# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/web_pixel.py"
# purpose: "FastAPI router for Web Pixel Event Ingestion, Analytics & Real-time Metrics"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, Header, HTTPException, Query
from apps.api.services.web_pixel_ingestion import (
    WebPixelEvent,
    pixel_ingestion_engine,
)

router = APIRouter(prefix="/web-pixel", tags=["Web Pixel & Analytics"])


@router.post("/events")
async def ingest_event_endpoint(
    event: WebPixelEvent,
    request: Request,
    x_shopify_hmac: Optional[str] = Header(None, alias="X-Shopify-Hmac"),
    x_shopify_topic: Optional[str] = Header(None, alias="X-Shopify-Topic"),
):
    raw_body = await request.body()
    result = await pixel_ingestion_engine.ingest_event(
        event=event,
        raw_body=raw_body,
        x_shopify_hmac=x_shopify_hmac,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=401, detail=result)
    return result


@router.get("/events")
async def list_events_endpoint(
    shop_id: Optional[str] = Query(None, description="Filter by shop ID"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
):
    events = pixel_ingestion_engine.get_events(shop_id=shop_id, limit=limit)
    return {"status": "ok", "count": len(events), "events": events}


@router.get("/metrics")
async def get_metrics_endpoint():
    metrics = pixel_ingestion_engine.get_metrics()
    return {"status": "ok", "metrics": metrics}
