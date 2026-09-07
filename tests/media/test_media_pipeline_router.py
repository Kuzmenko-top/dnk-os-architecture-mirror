# --- DNK-MRH-HEADER ---
# mrh_id: "tests_media_test_media_pipeline_router"
# purpose: "Integration Tests for Video Pipeline FastAPI REST & WebSocket Router (DNK-MEDIA-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_worker_registration_and_heartbeat():
    # Register worker
    res = client.post(
        "/api/v1/media/workers/heartbeat",
        json={
            "worker_id": "worker-gpu-node-01",
            "hostname": "transcode-node-01.infra.dnk-e.internal",
            "ip_address": "10.0.10.45",
            "concurrency_limit": 8,
            "gpu_type": "nvenc",
            "supported_codecs": ["h264", "hevc"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["worker_id"] == "worker-gpu-node-01"
    assert data["status"] == "HEALTHY"

    # List workers
    list_res = client.get("/api/v1/media/workers")
    assert list_res.status_code == 200
    workers = list_res.json()
    assert any(w["worker_id"] == "worker-gpu-node-01" for w in workers)


def test_video_ingest_and_lifecycle():
    # Ingest video
    ingest_payload = {
        "source_uri": "/tmp/test_videos/input_4k_sample.mp4",
        "duration_seconds": 60.0,
        "target_chunk_duration_seconds": 4,
        "codecs": ["h264", "h265"],
    }
    ingest_res = client.post("/api/v1/media/jobs/ingest", json=ingest_payload)
    assert ingest_res.status_code == 201
    job_info = ingest_res.json()
    job_id = job_info["job_id"]

    assert job_info["status"] == "PROCESSING"
    assert job_info["total_chunks"] > 0
    assert job_info["transcoding_tasks_created"] > 0
    assert len(job_info["chunks"]) > 0

    # Get job details
    details_res = client.get(f"/api/v1/media/jobs/{job_id}")
    assert details_res.status_code == 200
    details = details_res.json()
    assert details["job_id"] == job_id
    assert details["total_chunks"] == job_info["total_chunks"]

    # Get progress
    prog_res = client.get(f"/api/v1/media/jobs/{job_id}/progress")
    assert prog_res.status_code == 200
    prog = prog_res.json()
    assert prog["job_id"] == job_id
    assert "h264" in prog["codecs"]

    # Package output into HLS & DASH
    pack_res = client.post(f"/api/v1/media/jobs/{job_id}/package", json={"format": "both"})
    assert pack_res.status_code == 200
    pack_data = pack_res.json()
    assert pack_data["is_valid"] is True
    assert pack_data["hls_master_url"] is not None
    assert pack_data["dash_manifest_url"] is not None

    # Retrieve HLS Master Playlist
    hls_res = client.get(f"/api/v1/media/jobs/{job_id}/hls/master.m3u8")
    assert hls_res.status_code == 200
    assert "#EXTM3U" in hls_res.text
    assert "#EXT-X-STREAM-INF" in hls_res.text

    # Retrieve DASH Manifest
    dash_res = client.get(f"/api/v1/media/jobs/{job_id}/dash/manifest.mpd")
    assert dash_res.status_code == 200
    assert "<MPD" in dash_res.text
    assert "<Period" in dash_res.text


def test_nonexistent_job_404():
    res = client.get("/api/v1/media/jobs/nonexistent_job_999999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
