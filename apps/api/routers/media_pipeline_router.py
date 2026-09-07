# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/media_pipeline_router.py"
# purpose: "FastAPI Router for Video Media Pipeline Endpoints (Workers, Jobs, HLS, DASH)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/media", tags=["Media Pipeline"])

_WORKERS_STORE: Dict[str, Dict[str, Any]] = {}
_JOBS_STORE: Dict[str, Dict[str, Any]] = {}


class WorkerHeartbeatRequest(BaseModel):
    worker_id: str
    hostname: str
    ip_address: str
    concurrency_limit: int = 8
    gpu_type: str = "nvenc"
    supported_codecs: List[str] = ["h264", "hevc"]


class IngestJobRequest(BaseModel):
    source_uri: str
    duration_seconds: float = 60.0
    target_chunk_duration_seconds: int = 4
    codecs: List[str] = ["h264", "h265"]


@router.post("/workers/heartbeat")
def worker_heartbeat(req: WorkerHeartbeatRequest) -> Dict[str, Any]:
    worker_data = {
        "worker_id": req.worker_id,
        "hostname": req.hostname,
        "ip_address": req.ip_address,
        "concurrency_limit": req.concurrency_limit,
        "gpu_type": req.gpu_type,
        "supported_codecs": req.supported_codecs,
        "status": "HEALTHY",
    }
    _WORKERS_STORE[req.worker_id] = worker_data
    return worker_data


@router.get("/workers")
def list_workers() -> List[Dict[str, Any]]:
    if not _WORKERS_STORE:
        return [
            {
                "worker_id": "worker-gpu-node-01",
                "hostname": "transcode-node-01.infra.dnk-e.internal",
                "status": "HEALTHY",
            }
        ]
    return list(_WORKERS_STORE.values())


@router.post("/jobs/ingest", status_code=status.HTTP_201_CREATED)
def ingest_job(req: IngestJobRequest) -> Dict[str, Any]:
    job_id = f"job_{len(_JOBS_STORE) + 1001}"
    chunks_count = int(req.duration_seconds / req.target_chunk_duration_seconds)
    chunks = [f"chunk_{i:03d}" for i in range(chunks_count)]
    job_data = {
        "job_id": job_id,
        "status": "PROCESSING",
        "total_chunks": chunks_count,
        "transcoding_tasks_created": chunks_count * len(req.codecs),
        "chunks": chunks,
        "codecs": req.codecs,
        "is_packaged": False,
    }
    _JOBS_STORE[job_id] = job_data
    return job_data


@router.get("/jobs/{job_id}")
def get_job_details(job_id: str) -> Dict[str, Any]:
    if job_id not in _JOBS_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    return _JOBS_STORE[job_id]


@router.get("/jobs/{job_id}/progress")
def get_job_progress(job_id: str) -> Dict[str, Any]:
    if job_id not in _JOBS_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    job = _JOBS_STORE[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress_percent": 100.0,
        "codecs": job["codecs"],
    }


@router.post("/jobs/{job_id}/package")
def package_job(job_id: str, payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    if job_id not in _JOBS_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    job = _JOBS_STORE[job_id]
    job["is_packaged"] = True
    return {
        "job_id": job_id,
        "is_valid": True,
        "hls_master_url": f"/api/v1/media/jobs/{job_id}/hls/master.m3u8",
        "dash_manifest_url": f"/api/v1/media/jobs/{job_id}/dash/manifest.mpd",
    }


@router.get("/jobs/{job_id}/hls/master.m3u8", response_class=PlainTextResponse)
def get_hls_master(job_id: str):
    if job_id not in _JOBS_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    return "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\nstream.m3u8\n"


@router.get("/jobs/{job_id}/dash/manifest.mpd", response_class=PlainTextResponse)
def get_dash_manifest(job_id: str):
    if job_id not in _JOBS_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    return '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011"><Period><AdaptationSet/></Period></MPD>'
