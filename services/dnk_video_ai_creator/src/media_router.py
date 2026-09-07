# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/media_router.py"
# purpose: "FastAPI REST API Router for Video Rendering & Dynamic Templates (DNK-MEDIA-001 Phase 4)."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .cache_manager import CacheManager, get_default_cache_manager
from .progress_streamer import ProgressStreamer, get_default_progress_streamer, RenderStage
from .template_registry import TemplateRegistry, TemplateMetadata, create_default_registry
from .video_composition_schema import VideoCompositionSchema
from .job_queue import MediaJobQueue, JobType, JobStatus, MediaJob, get_default_job_queue

router = APIRouter(prefix="/api/v1/media", tags=["media"])


# --- Request & Response Models ---

class RenderRequest(BaseModel):
    template_id: Optional[str] = Field(None, description="Registered template ID to render")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters to inject into the template")
    composition: Optional[VideoCompositionSchema] = Field(None, description="Raw custom Video Composition AST")
    use_cache: bool = Field(True, description="Whether to check and store in asset cache")


class PreviewRequest(BaseModel):
    template_id: Optional[str] = Field(None, description="Registered template ID to render preview")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters to inject into the template")
    composition: Optional[VideoCompositionSchema] = Field(None, description="Raw custom Video Composition AST")
    output_format: str = Field("gif", description="Preview output format ('gif' or 'mp4')")
    max_frames: int = Field(30, description="Maximum number of frames for fast preview")
    use_cache: bool = Field(True, description="Whether to check and store in asset cache")


class JobResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    progress_pct: float
    stage: str
    template_id: Optional[str] = None
    output_path: Optional[str] = None
    cdn_url: Optional[str] = None
    preview_format: Optional[str] = None
    error: Optional[str] = None
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class TemplateListResponse(BaseModel):
    count: int
    templates: List[TemplateMetadata]


class CacheStatsResponse(BaseModel):
    cached_entries: int
    total_size_bytes: int
    cache_dir: str


# --- Endpoints ---

@router.post("/render", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_render_job(
    request: RenderRequest,
    background_tasks: BackgroundTasks,
) -> JobResponse:
    """
    Launch asynchronous headless video rendering job.
    Supports either pre-registered template_id + params or raw VideoCompositionSchema.
    """
    queue = get_default_job_queue()
    registry = queue.template_registry

    if not request.template_id and not request.composition:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'template_id' or 'composition' must be provided.",
        )

    if request.template_id:
        try:
            # Whitelist verification
            registry.get(request.template_id)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with id '{request.template_id}' is not registered.",
            )

    job = await queue.submit_render_job(
        template_id=request.template_id,
        params=request.params,
        composition=request.composition,
        use_cache=request.use_cache,
    )

    return JobResponse(
        job_id=job.job_id,
        job_type=job.job_type.value,
        status=job.status.value,
        progress_pct=job.progress_pct,
        stage=job.stage.value,
        template_id=job.template_id,
        output_path=job.output_path,
        cdn_url=job.cdn_url,
        preview_format=job.preview_format,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.post("/preview", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_preview_job(
    request: PreviewRequest,
) -> JobResponse:
    """
    Launch fast preview generation job (GIF / short MP4).
    """
    queue = get_default_job_queue()
    registry = queue.template_registry

    if not request.template_id and not request.composition:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'template_id' or 'composition' must be provided.",
        )

    if request.template_id:
        try:
            registry.get(request.template_id)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with id '{request.template_id}' is not registered.",
            )

    fmt = request.output_format.lower()
    if fmt not in ("gif", "mp4"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preview format must be 'gif' or 'mp4'.",
        )

    job = await queue.submit_preview_job(
        template_id=request.template_id,
        params=request.params,
        composition=request.composition,
        preview_format=fmt,
        use_cache=request.use_cache,
    )

    return JobResponse(
        job_id=job.job_id,
        job_type=job.job_type.value,
        status=job.status.value,
        progress_pct=job.progress_pct,
        stage=job.stage.value,
        template_id=job.template_id,
        output_path=job.output_path,
        cdn_url=job.cdn_url,
        preview_format=job.preview_format,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str) -> JobResponse:
    """
    Retrieve rendering job status, progress percentage, and output URLs.
    """
    queue = get_default_job_queue()
    job = queue.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id '{job_id}' not found.",
        )

    return JobResponse(
        job_id=job.job_id,
        job_type=job.job_type.value,
        status=job.status.value,
        progress_pct=job.progress_pct,
        stage=job.stage.value,
        template_id=job.template_id,
        output_path=job.output_path,
        cdn_url=job.cdn_url,
        preview_format=job.preview_format,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """
    Server-Sent Events (SSE) real-time progress stream for a rendering job.
    """
    queue = get_default_job_queue()
    job = queue.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id '{job_id}' not found.",
        )

    streamer = queue.progress_streamer

    async def event_generator():
        async for sse_chunk in streamer.stream_sse(job_id):
            yield sse_chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    tag: Optional[str] = Query(None, description="Optional tag filter (e.g. 'e-commerce', 'ugc')")
) -> TemplateListResponse:
    """
    List all available video templates with parameters and metadata.
    """
    registry = create_default_registry()
    templates = registry.list_templates(tag=tag)
    return TemplateListResponse(
        count=len(templates),
        templates=templates,
    )


@router.get("/templates/{template_id}", response_model=TemplateMetadata)
async def get_template(template_id: str) -> TemplateMetadata:
    """
    Get detailed schema and parameter documentation for a specific template.
    """
    registry = create_default_registry()
    try:
        meta, _ = registry.get(template_id)
        return meta
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id '{template_id}' not found.",
        )


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats() -> CacheStatsResponse:
    """
    Retrieve storage statistics from the asset cache manager.
    """
    cache = get_default_cache_manager()
    stats = cache.get_stats()
    return CacheStatsResponse(**stats)


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel an ongoing or queued rendering job.
    """
    queue = get_default_job_queue()
    cancelled = queue.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job '{job_id}' cannot be cancelled (already completed or not found).",
        )
    return {"message": f"Job {job_id} cancelled successfully."}
