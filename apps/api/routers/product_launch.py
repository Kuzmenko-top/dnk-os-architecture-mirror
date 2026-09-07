# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_product_launch"
# purpose: "FastAPI router for triggering and tracking One-Click Multi-Agent Product Launch pipelines."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any

from core.flows.product_launch_flow import (
    product_launch_pipeline,
    ProductLaunchInput,
    ProductLaunchResult,
)

router = APIRouter(prefix="/api/v1/product-launch", tags=["Product Launch Pipeline"])


@router.post("/execute", response_model=ProductLaunchResult)
async def execute_product_launch(payload: ProductLaunchInput):
    """
    Trigger end-to-end One-Click Product Launch Flow:
    1. dnk_marketing_cmo (Angles & Copy)
    2. dnk_shopify (PDP Liquid Section)
    3. dnk_video_ai_creator (Remotion Reel 9:16)
    4. dnk_finance_cfo (Unit Economics & Break-Even ROAS)
    """
    try:
        result = await product_launch_pipeline.execute(payload)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Product launch failed: {str(exc)}")


@router.get("/health")
async def product_launch_health():
    """Healthcheck for Product Launch multi-agent service."""
    return {
        "status": "healthy",
        "service": "dnk_product_launch_flow",
        "agents": ["dnk_marketing_cmo", "dnk_shopify", "dnk_video_ai_creator", "dnk_finance_cfo"],
    }
