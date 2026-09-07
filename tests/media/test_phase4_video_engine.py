# --- DNK-MRH-HEADER ---
# mrh_id: "tests/media/test_phase4_video_engine.py"
# purpose: "Unit, Integration and E2E Tests for DNK-MEDIA-001 Phase 4 (API, Job Queue, Cache & Streaming)."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Generator
import pytest
pytest.importorskip("PIL")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.dnk_video_ai_creator.src.cache_manager import CacheManager, CacheEntry
from services.dnk_video_ai_creator.src.progress_streamer import (
    ProgressStreamer,
    ProgressEvent,
    RenderStage,
)
from services.dnk_video_ai_creator.src.job_queue import (
    MediaJobQueue,
    JobType,
    JobStatus,
    MediaJob,
)
from services.dnk_video_ai_creator.src.media_router import router as media_router
from services.dnk_video_ai_creator.src.template_registry import create_default_registry
from services.dnk_video_ai_creator.src.video_composition_schema import (
    VideoCompositionSchema,
    Track,
    Clip,
    ClipType,
)


@pytest.fixture
def temp_cache_dir() -> Generator[str, None, None]:
    tmp_dir = tempfile.mkdtemp(prefix="test_cache_")
    yield tmp_dir
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def sample_composition() -> VideoCompositionSchema:
    return VideoCompositionSchema(
        id="test-p4-comp",
        title="Phase 4 Sample Comp",
        width=320,
        height=240,
        fps=10,
        duration_frames=10,
        tracks=[
            Track(
                id="base",
                name="Base Track",
                clips=[
                    Clip(
                        id="bg",
                        clip_type=ClipType.CANVAS,
                        start_frame=0,
                        duration_frames=10,
                        properties={"color": "#112233"},
                    )
                ]
            )
        ]
    )


# --- 1. Unit Tests: CacheManager ---

def test_cache_manager_basic_put_get(temp_cache_dir: str):
    cache = CacheManager(cache_dir=temp_cache_dir, cdn_base_url="https://cdn.example.com/media")
    dummy_file = Path(temp_cache_dir) / "dummy.mp4"
    dummy_file.write_bytes(b"FAKE_VIDEO_PAYLOAD_12345")

    payload = {"foo": "bar", "num": 42}
    key = cache.compute_key(payload)

    entry = cache.put(key=key, source_file_path=dummy_file, extension="mp4", metadata={"title": "Test"})
    assert entry.key == key
    assert os.path.exists(entry.file_path)
    assert entry.cdn_url == f"https://cdn.example.com/media/{key}.mp4"

    retrieved = cache.get(key, extension="mp4")
    assert retrieved is not None
    assert retrieved.file_size_bytes == len(b"FAKE_VIDEO_PAYLOAD_12345")
    assert retrieved.metadata["title"] == "Test"


def test_cache_manager_invalidation(temp_cache_dir: str):
    cache = CacheManager(cache_dir=temp_cache_dir)
    dummy_file = Path(temp_cache_dir) / "dummy.mp4"
    dummy_file.write_bytes(b"TEST_DATA")

    key = cache.compute_key("payload_to_invalidate")
    cache.put(key=key, source_file_path=dummy_file, extension="mp4", metadata={"template_id": "shopify_product_promo"})

    assert cache.get(key) is not None
    invalidated_count = cache.invalidate_template("shopify_product_promo")
    assert invalidated_count == 1
    assert cache.get(key) is None


def test_cache_manager_stats_and_clear(temp_cache_dir: str, tmp_path: Path):
    cache = CacheManager(cache_dir=temp_cache_dir)
    dummy_file = tmp_path / "dummy.mp4"
    dummy_file.write_bytes(b"DATA")

    key1 = cache.compute_key("k1")
    key2 = cache.compute_key("k2")
    cache.put(key1, dummy_file)
    cache.put(key2, dummy_file)

    stats = cache.get_stats()
    assert stats["cached_entries"] == 2
    assert stats["total_size_bytes"] >= 8

    cleared = cache.clear()
    assert cleared == 2
    assert cache.get(key1) is None
    assert cache.get_stats()["cached_entries"] == 0


# --- 2. Unit Tests: ProgressStreamer ---

@pytest.mark.asyncio
async def test_progress_streamer_pubsub():
    streamer = ProgressStreamer()
    job_id = "job-test-stream-1"
    queue = await streamer.subscribe(job_id)

    await streamer.emit(
        job_id=job_id,
        stage=RenderStage.INITIALIZING,
        progress_pct=10.0,
        message="Starting up",
    )

    event = await asyncio.wait_for(queue.get(), timeout=2.0)
    assert event.job_id == job_id
    assert event.stage == RenderStage.INITIALIZING
    assert event.progress_pct == 10.0
    assert event.message == "Starting up"

    await streamer.unsubscribe(job_id, queue)
    assert len(streamer._listeners[job_id]) == 0


@pytest.mark.asyncio
async def test_progress_streamer_stream_generator():
    streamer = ProgressStreamer()
    job_id = "job-stream-gen"

    async def emit_sequence():
        await asyncio.sleep(0.05)
        await streamer.emit(job_id=job_id, stage=RenderStage.RENDERING_FRAMES, progress_pct=50.0)
        await asyncio.sleep(0.05)
        await streamer.emit(job_id=job_id, stage=RenderStage.COMPLETED, progress_pct=100.0)

    asyncio.create_task(emit_sequence())

    events = []
    async for ev in streamer.stream(job_id, timeout_seconds=2.0):
        events.append(ev)

    assert len(events) >= 2
    assert events[-1].stage == RenderStage.COMPLETED
    assert events[-1].progress_pct == 100.0


# --- 3. Unit & Integration Tests: MediaJobQueue ---

@pytest.mark.asyncio
async def test_job_queue_preview_gif(temp_cache_dir: str, sample_composition: VideoCompositionSchema):
    cache = CacheManager(cache_dir=temp_cache_dir)
    streamer = ProgressStreamer()
    registry = create_default_registry()

    queue = MediaJobQueue(
        cache_manager=cache,
        progress_streamer=streamer,
        template_registry=registry,
        output_dir=temp_cache_dir,
    )

    job = await queue.submit_preview_job(
        composition=sample_composition,
        preview_format="gif",
        use_cache=False,
    )
    assert job.status in (JobStatus.QUEUED, JobStatus.PROCESSING, JobStatus.COMPLETED)

    # Wait for completion
    completed = False
    for _ in range(50):
        current_job = queue.get_job(job.job_id)
        if current_job and current_job.status == JobStatus.COMPLETED:
            completed = True
            break
        await asyncio.sleep(0.1)

    assert completed
    final_job = queue.get_job(job.job_id)
    assert final_job is not None
    assert final_job.output_path is not None
    assert os.path.exists(final_job.output_path)
    assert final_job.progress_pct == 100.0


@pytest.mark.asyncio
async def test_job_queue_template_render(temp_cache_dir: str):
    cache = CacheManager(cache_dir=temp_cache_dir)
    streamer = ProgressStreamer()
    registry = create_default_registry()

    queue = MediaJobQueue(
        cache_manager=cache,
        progress_streamer=streamer,
        template_registry=registry,
        output_dir=temp_cache_dir,
    )

    # Fast duration params for test
    params = {
        "title": "Fast Test Promo",
        "duration_seconds": 5.0,
        "price": "$19.99",
    }

    job = await queue.submit_render_job(
        template_id="shopify_product_promo",
        params=params,
        use_cache=True,
    )
    assert job.job_id is not None

    # Wait for completion
    completed = False
    for _ in range(100):
        j = queue.get_job(job.job_id)
        if j and j.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            completed = True
            break
        await asyncio.sleep(0.1)

    assert completed
    final_job = queue.get_job(job.job_id)
    assert final_job is not None
    if final_job.status == JobStatus.FAILED:
        print("JOB FAILED WITH ERROR:", final_job.error)
    assert final_job.status == JobStatus.COMPLETED
    assert final_job.output_path is not None
    assert os.path.exists(final_job.output_path)


# --- 4. Integration Tests: FastAPI Endpoints ---

@pytest.fixture
def client() -> TestClient:
    app = FastAPI(title="Test DNK Media API")
    app.include_router(media_router)
    return TestClient(app)


def test_api_list_templates(client: TestClient):
    response = client.get("/api/v1/media/templates")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 2
    ids = [t["id"] for t in data["templates"]]
    assert "shopify_product_promo" in ids
    assert "ugc_vertical_reel" in ids


def test_api_list_templates_with_tag(client: TestClient):
    response = client.get("/api/v1/media/templates?tag=shopify")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert data["templates"][0]["id"] == "shopify_product_promo"


def test_api_get_template_detail(client: TestClient):
    response = client.get("/api/v1/media/templates/shopify_product_promo")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "shopify_product_promo"
    assert "title" in data["parameters_schema"]

    # Unknown template 404
    resp_404 = client.get("/api/v1/media/templates/unknown_template_id")
    assert resp_404.status_code == 404


def test_api_create_preview_endpoint(client: TestClient):
    req_body = {
        "template_id": "ugc_vertical_reel",
        "params": {
            "creator_handle": "@dnk_tester",
            "duration_seconds": 1.0,
        },
        "preview_format": "gif",
        "use_cache": False,
    }
    response = client.post("/api/v1/media/preview", json=req_body)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # Poll status
    time.sleep(0.5)
    status_resp = client.get(f"/api/v1/media/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["job_id"] == job_id


def test_api_invalid_render_request(client: TestClient):
    # Missing template_id and composition
    resp = client.post("/api/v1/media/render", json={})
    assert resp.status_code == 400

    # Non-existent template_id
    resp_bad_template = client.post(
        "/api/v1/media/render",
        json={"template_id": "non_existent_random_id"}
    )
    assert resp_bad_template.status_code == 404


def test_api_cache_stats(client: TestClient):
    response = client.get("/api/v1/media/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cached_entries" in data
    assert "total_size_bytes" in data
    assert "cache_dir" in data
