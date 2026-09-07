# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_media_pipeline_router"
# purpose: "FastAPI REST & WebSocket Router for Video Ingest, Transcoding, Packaging & Progress Tracking (DNK-MEDIA-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
import time
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response, status
from pydantic import BaseModel, Field

from apps.api.services.video_chunking_engine import (
    video_chunking_engine,
    VideoStreamMetadata,
    ChunkingPlan,
)
from apps.api.services.hardware_acceleration_manager import (
    hardware_acceleration_manager,
    VideoCodec,
    HardwareAccelType,
)
from apps.api.services.distributed_transcoding_worker import (
    distributed_transcoding_worker_pool,
    STANDARD_ABR_LADDER,
    TaskStatus,
)
from apps.api.services.video_packaging_engine import (
    video_packaging_engine,
    PackagingFormat,
    SegmentInfo,
)
from apps.api.services.media_storage_manager import media_storage_manager


media_router = APIRouter(prefix="/api/v1/media", tags=["Distributed Video Pipeline"])


# --- Request & Response Schemas ---

class VideoIngestRequest(BaseModel):
    source_uri: str = Field(..., description="Source video file path or S3 URI")
    duration_seconds: Optional[float] = Field(None, description="Optional pre-known duration")
    target_chunk_duration_seconds: int = Field(4, description="Target chunk duration in seconds")
    codecs: List[str] = Field(default=["h264"], description="List of target codecs: h264, h265, vp9, av1")
    webhook_url: Optional[str] = Field(None, description="Optional completion webhook URL")


class VideoIngestResponse(BaseModel):
    job_id: str
    status: str
    source_uri: str
    duration_seconds: float
    total_chunks: int
    chunks: List[Dict[str, Any]]
    transcoding_tasks_created: int


class TranscodingJobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress_percent: float
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    codecs: List[str]
    created_at_epoch: float


class WorkerHeartbeatRequest(BaseModel):
    worker_id: str
    hostname: str = "worker-node-1"
    ip_address: str = "10.0.0.10"
    concurrency_limit: int = 4
    gpu_type: Optional[str] = None
    supported_codecs: List[str] = ["h264", "h265"]


class PackagingRequest(BaseModel):
    format: str = Field("both", description="Packaging format: hls, dash, or both")


# --- In-Memory State for Realtime Tracking ---
_JOBS_STORE: Dict[str, Dict[str, Any]] = {}
_ACTIVE_WEBSOCKETS: Dict[str, List[WebSocket]] = {}


@media_router.post("/jobs/ingest", response_model=VideoIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_video(request: VideoIngestRequest):
    """
    Ingests video, executes GOP-aligned keyframe analysis, splits into chunk plan, and queues transcoding tasks.
    """
    job_id = f"job_{int(time.time()*1000)}"

    # Metadata extraction
    metadata = video_chunking_engine.analyze_source_metadata(
        file_path=request.source_uri,
        simulated_duration=request.duration_seconds or 120.0,
    )

    # Chunking plan
    plan = video_chunking_engine.build_chunking_plan(
        source_file_path=request.source_uri,
        metadata=metadata,
        target_chunk_duration=float(request.target_chunk_duration_seconds),
    )

    # Map codecs
    target_codecs: List[VideoCodec] = []
    for c_str in request.codecs:
        try:
            target_codecs.append(VideoCodec(c_str.lower()))
        except ValueError:
            target_codecs.append(VideoCodec.H264)

    # Generate tasks in worker pool
    tasks = distributed_transcoding_worker_pool.generate_job_transcode_tasks(
        job_id=job_id,
        chunking_plan=plan,
        codecs=target_codecs,
    )

    _JOBS_STORE[job_id] = {
        "job_id": job_id,
        "source_uri": request.source_uri,
        "metadata": metadata,
        "plan": plan,
        "target_codecs": target_codecs,
        "status": "PROCESSING",
        "created_at_epoch": time.time(),
        "packaging_result": None,
    }

    chunks_data = [
        {
            "chunk_index": c.chunk_index,
            "start_time": c.start_time_seconds,
            "end_time": c.end_time_seconds,
            "duration": c.duration_seconds,
        }
        for c in plan.chunks
    ]

    return VideoIngestResponse(
        job_id=job_id,
        status="PROCESSING",
        source_uri=request.source_uri,
        duration_seconds=metadata.duration_seconds,
        total_chunks=plan.total_chunks,
        chunks=chunks_data,
        transcoding_tasks_created=len(tasks),
    )


@media_router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_details(job_id: str):
    """
    Retrieves complete metadata, chunking breakdown, and execution status of a video job.
    """
    if job_id not in _JOBS_STORE:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    job_data = _JOBS_STORE[job_id]
    progress = distributed_transcoding_worker_pool.get_job_progress(job_id)

    return {
        "job_id": job_id,
        "status": job_data["status"],
        "source_uri": job_data["source_uri"],
        "duration_seconds": job_data["metadata"].duration_seconds,
        "total_chunks": job_data["plan"].total_chunks,
        "progress": progress,
        "has_packaging": job_data["packaging_result"] is not None,
    }


@media_router.get("/jobs/{job_id}/progress", response_model=TranscodingJobStatusResponse)
async def get_job_progress(job_id: str):
    """
    Retrieves aggregated real-time transcoding progress across all ABR profiles and workers.
    """
    if job_id not in _JOBS_STORE:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    job_data = _JOBS_STORE[job_id]
    progress = distributed_transcoding_worker_pool.get_job_progress(job_id)

    return TranscodingJobStatusResponse(
        job_id=job_id,
        status=job_data["status"],
        progress_percent=progress.get("progress_percent", 0.0),
        total_tasks=progress.get("total_tasks", 0),
        completed_tasks=progress.get("completed_tasks", 0),
        failed_tasks=progress.get("failed_tasks", 0),
        codecs=[c.value for c in job_data["target_codecs"]],
        created_at_epoch=job_data["created_at_epoch"],
    )


@media_router.post("/jobs/{job_id}/package", response_model=Dict[str, Any])
async def package_job(job_id: str, request: PackagingRequest):
    """
    Packages transcoded chunks into HLS Multivariant Playlists (.m3u8) and MPEG-DASH Manifests (.mpd).
    """
    if job_id not in _JOBS_STORE:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    job_data = _JOBS_STORE[job_id]
    plan: ChunkingPlan = job_data["plan"]
    codecs = job_data["target_codecs"]

    # Build simulated/actual segment maps
    segment_map: Dict[str, List[SegmentInfo]] = {}
    for c in codecs:
        for abr in STANDARD_ABR_LADDER:
            key = f"{c.value}_{abr.resolution_name}"
            seg_list = []
            for chunk in plan.chunks:
                seg_list.append(
                    SegmentInfo(
                        segment_index=chunk.chunk_index,
                        uri=f"segment_{chunk.chunk_index:04d}.ts",
                        duration_seconds=chunk.duration_seconds,
                        byte_size=1024 * 512,
                    )
                )
            segment_map[key] = seg_list

    pkg_format = PackagingFormat(request.format.lower()) if request.format in ("hls", "dash", "both") else PackagingFormat.BOTH

    result = video_packaging_engine.package_job_outputs(
        job_id=job_id,
        total_duration_seconds=job_data["metadata"].duration_seconds,
        transcoded_chunks_map=segment_map,
        codecs=codecs,
        packaging_format=pkg_format,
    )

    job_data["packaging_result"] = result
    job_data["status"] = "COMPLETED"

    # Store master playlist artifact in media storage manager
    if result.hls_master_playlist_content:
        media_storage_manager.upload_bytes(
            job_id=job_id,
            relative_path="master.m3u8",
            data=result.hls_master_playlist_content.encode(),
            content_type="application/vnd.apple.mpegurl",
            artifact_type="packaged",
        )

    if result.dash_manifest_content:
        media_storage_manager.upload_bytes(
            job_id=job_id,
            relative_path="manifest.mpd",
            data=result.dash_manifest_content.encode(),
            content_type="application/dash+xml",
            artifact_type="packaged",
        )

    return {
        "job_id": job_id,
        "format": result.format.value,
        "hls_master_url": f"/api/v1/media/jobs/{job_id}/hls/master.m3u8" if result.hls_master_playlist_content else None,
        "dash_manifest_url": f"/api/v1/media/jobs/{job_id}/dash/manifest.mpd" if result.dash_manifest_content else None,
        "variants_count": len(result.variant_playlists),
        "is_valid": result.is_valid,
    }


@media_router.get("/jobs/{job_id}/hls/master.m3u8")
async def get_hls_master_playlist(job_id: str):
    """
    Streams the HLS Master Multivariant Playlist for HLS.js / Safari native player.
    """
    if job_id not in _JOBS_STORE or not _JOBS_STORE[job_id]["packaging_result"]:
        raise HTTPException(status_code=404, detail="HLS Master playlist not found or job not packaged yet")

    content = _JOBS_STORE[job_id]["packaging_result"].hls_master_playlist_content
    return Response(content=content, media_type="application/vnd.apple.mpegurl")


@media_router.get("/jobs/{job_id}/dash/manifest.mpd")
async def get_dash_manifest(job_id: str):
    """
    Streams the MPEG-DASH XML MPD manifest for Dash.js / Video.js.
    """
    if job_id not in _JOBS_STORE or not _JOBS_STORE[job_id]["packaging_result"]:
        raise HTTPException(status_code=404, detail="DASH Manifest not found or job not packaged yet")

    content = _JOBS_STORE[job_id]["packaging_result"].dash_manifest_content
    return Response(content=content, media_type="application/dash+xml")


@media_router.get("/workers", response_model=List[Dict[str, Any]])
async def list_workers():
    """
    Lists all registered transcoding worker nodes, GPU specs, and current queue load.
    """
    workers = [w for w in distributed_transcoding_worker_pool.workers.values() if w.is_active]
    return [
        {
            "worker_id": w.worker_id,
            "hostname": w.hostname,
            "is_active": w.is_active,
            "active_tasks": w.active_tasks,
            "concurrency_limit": w.concurrency_limit,
            "hardware_accel": w.hardware_accel.value if w.hardware_accel else None,
            "last_heartbeat_epoch": w.last_heartbeat,
        }
        for w in workers
    ]


@media_router.post("/workers/heartbeat", response_model=Dict[str, Any])
async def worker_heartbeat(request: WorkerHeartbeatRequest):
    """
    Processes worker node heartbeats and capacity updates.
    """
    gpu_type = HardwareAccelType.CPU
    if request.gpu_type:
        try:
            gpu_type = HardwareAccelType(request.gpu_type.lower())
        except ValueError:
            gpu_type = HardwareAccelType.CPU

    worker = distributed_transcoding_worker_pool.register_worker(
        worker_id=request.worker_id,
        hostname=request.hostname,
        concurrency_limit=request.concurrency_limit,
        hardware_accel=gpu_type,
    )
    distributed_transcoding_worker_pool.heartbeat(request.worker_id)

    return {
        "worker_id": worker.worker_id,
        "status": "HEALTHY",
        "acknowledged_epoch": time.time(),
    }


@media_router.websocket("/jobs/{job_id}/ws")
async def websocket_job_progress(websocket: WebSocket, job_id: str):
    """
    Real-time WebSocket connection streaming transcoding and packaging progress to frontend clients.
    """
    await websocket.accept()
    if job_id not in _ACTIVE_WEBSOCKETS:
        _ACTIVE_WEBSOCKETS[job_id] = []
    _ACTIVE_WEBSOCKETS[job_id].append(websocket)

    try:
        while True:
            if job_id in _JOBS_STORE:
                progress = distributed_transcoding_worker_pool.get_job_progress(job_id)
                await websocket.send_json({
                    "job_id": job_id,
                    "status": _JOBS_STORE[job_id]["status"],
                    "progress": progress,
                    "timestamp": time.time(),
                })
            await asyncio.sleep(1.0)
    except (WebSocketDisconnect, Exception):
        if job_id in _ACTIVE_WEBSOCKETS and websocket in _ACTIVE_WEBSOCKETS[job_id]:
            _ACTIVE_WEBSOCKETS[job_id].remove(websocket)
