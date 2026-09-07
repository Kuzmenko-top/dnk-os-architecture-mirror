# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_video_audit"
# purpose: "Video audit router with SSRF protection and ingestion validation"
# author: "DNK-e.com Maksym & Gerych"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# --- END DNK-MRH-HEADER ---

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from ..lib.ssrf_guard import SSRFGuard

router = APIRouter(tags=["video-audit"])


class VideoAuditRequest(BaseModel):
    video_url: str = Field(..., description="External URL of video to audit")
    content_length: Optional[int] = Field(None, description="Expected content length in bytes")
    duration: Optional[float] = Field(None, description="Expected video duration in seconds")


@router.post("/api/v1/canvas/video/audit")
async def audit_video(
    video_url: Optional[str] = Query(None, description="Direct URL query parameter"),
    payload: Optional[VideoAuditRequest] = None,
):
    target_url = (payload.video_url if payload and payload.video_url else video_url) or ""
    if not target_url:
        raise HTTPException(status_code=400, detail="Missing required 'video_url'")

    # 1. SSRF URL validation
    is_allowed, error_msg = SSRFGuard.is_allowed_url(target_url)
    if not is_allowed:
        raise HTTPException(status_code=403, detail=f"SSRF blocked: {error_msg}")

    # 2. Upload limits validation
    content_length = payload.content_length if payload else None
    duration = payload.duration if payload else None
    is_valid_limits, limit_err = SSRFGuard.validate_upload_limits(content_length, duration)
    if not is_valid_limits:
        raise HTTPException(status_code=413, detail=f"Upload limits exceeded: {limit_err}")

    return {
        "status": "ok",
        "video_url": target_url,
        "validation": "passed",
        "ssrf_check": "clean",
    }
