# --- DNK-MRH-HEADER ---
# mrh_id: "tests_media_test_distributed_transcoding"
# purpose: "Unit & Integration Tests for Distributed Transcoding Worker Pool (DNK-MEDIA-002 Phase 2)"
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
import uuid
from apps.api.services.distributed_transcoding_worker import (
    DistributedTranscodingWorkerPool,
    TaskStatus,
    ABRProfileSpec,
    STANDARD_ABR_LADDER,
    distributed_transcoding_worker_pool,
)
from apps.api.services.hardware_acceleration_manager import (
    HardwareAccelerationManager,
    HardwareAccelType,
    VideoCodec,
)
from apps.api.services.video_chunking_engine import (
    VideoChunkingEngine,
    VideoStreamMetadata,
    VideoChunkSpec,
    ChunkingPlan,
)


@pytest.fixture
def sample_chunking_plan():
    engine = VideoChunkingEngine()
    meta = VideoStreamMetadata(
        duration_seconds=12.0,
        width=1920,
        height=1080,
        fps=30.0,
        total_frames=360,
        codec_name="h264",
        bitrate_kbps=5000,
        keyframe_timestamps=[0.0, 4.0, 8.0, 12.0],
    )
    return engine.build_chunking_plan(
        source_file_path="/tmp/source.mp4",
        metadata=meta,
        target_chunk_duration=4.0,
    )


def test_worker_registration_and_heartbeat():
    pool = DistributedTranscodingWorkerPool()
    worker = pool.register_worker(
        worker_id="worker_gpu_01",
        hostname="node-gpu-1.cluster.local",
        hardware_accel=HardwareAccelType.NVENC,
        concurrency_limit=8,
    )

    assert worker.worker_id == "worker_gpu_01"
    assert worker.hardware_accel == HardwareAccelType.NVENC
    assert worker.concurrency_limit == 8
    assert worker.is_active is True

    heartbeat_ok = pool.heartbeat("worker_gpu_01")
    assert heartbeat_ok is True

    heartbeat_bad = pool.heartbeat("unknown_worker")
    assert heartbeat_bad is False


def test_generate_job_transcode_tasks(sample_chunking_plan):
    pool = DistributedTranscodingWorkerPool()
    job_id = f"job_{uuid.uuid4().hex[:8]}"

    # Request 2 codecs (H264, H265) x 4 ABR resolutions x 3 chunks = 24 tasks
    tasks = pool.generate_job_transcode_tasks(
        job_id=job_id,
        chunking_plan=sample_chunking_plan,
        codecs=[VideoCodec.H264, VideoCodec.H265],
        abr_ladder=STANDARD_ABR_LADDER,
    )

    assert len(tasks) == 24
    assert len(pool.task_queue) == 24
    
    progress = pool.get_job_progress(job_id)
    assert progress["total_tasks"] == 24
    assert progress["completed_tasks"] == 0
    assert progress["progress_percent"] == 0.0
    assert progress["status"] == "in_progress"


def test_task_scheduling_and_dispatch(sample_chunking_plan):
    pool = DistributedTranscodingWorkerPool()
    job_id = "job_test_dispatch"

    w1 = pool.register_worker("w1", "node1", HardwareAccelType.CPU, concurrency_limit=2)
    w2 = pool.register_worker("w2", "node2", HardwareAccelType.CPU, concurrency_limit=2)

    # 3 chunks x 1 codec x 1 resolution = 3 tasks
    single_ladder = [ABRProfileSpec("720p", 1280, 720, 2500)]
    tasks = pool.generate_job_transcode_tasks(
        job_id=job_id,
        chunking_plan=sample_chunking_plan,
        codecs=[VideoCodec.H264],
        abr_ladder=single_ladder,
    )

    assert len(tasks) == 3
    assignments = pool.schedule_next_tasks()

    # All 3 tasks should be assigned across w1 and w2
    assert len(assignments) == 3
    assert len(pool.task_queue) == 0

    assigned_workers = {worker.worker_id for worker, _ in assignments}
    assert "w1" in assigned_workers or "w2" in assigned_workers


def test_task_completion_and_progress_calculation(sample_chunking_plan):
    pool = DistributedTranscodingWorkerPool()
    job_id = "job_progress_test"

    pool.register_worker("w1", "node1", HardwareAccelType.CPU, concurrency_limit=5)
    single_ladder = [ABRProfileSpec("1080p", 1920, 1080, 4500)]
    tasks = pool.generate_job_transcode_tasks(
        job_id=job_id,
        chunking_plan=sample_chunking_plan,
        codecs=[VideoCodec.H264],
        abr_ladder=single_ladder,
    )
    # 3 chunks -> 3 tasks
    pool.schedule_next_tasks()

    # Complete task 1
    pool.complete_task(tasks[0].task_id, duration_ms=250.0)
    p1 = pool.get_job_progress(job_id)
    assert p1["completed_tasks"] == 1
    assert p1["progress_percent"] == 33.33
    assert p1["status"] == "in_progress"

    # Complete task 2 & 3
    pool.complete_task(tasks[1].task_id, duration_ms=240.0)
    pool.complete_task(tasks[2].task_id, duration_ms=260.0)
    p2 = pool.get_job_progress(job_id)
    assert p2["completed_tasks"] == 3
    assert p2["progress_percent"] == 100.0
    assert p2["status"] == "completed"


def test_task_failure_and_retry_mechanism(sample_chunking_plan):
    pool = DistributedTranscodingWorkerPool(max_retries=2)
    job_id = "job_retry_test"

    pool.register_worker("w1", "node1", HardwareAccelType.CPU, concurrency_limit=2)
    single_ladder = [ABRProfileSpec("480p", 854, 480, 1200)]
    tasks = pool.generate_job_transcode_tasks(
        job_id=job_id,
        chunking_plan=sample_chunking_plan,
        codecs=[VideoCodec.H264],
        abr_ladder=single_ladder,
    )
    task_id = tasks[0].task_id

    # Dispatch task
    pool.schedule_next_tasks()

    # First failure -> should retry
    pool.fail_task(task_id, "OOM error")
    assert pool.tasks[task_id].retry_count == 1
    assert pool.tasks[task_id].status == TaskStatus.RETRYING
    assert task_id in pool.task_queue

    # Re-dispatch and second failure -> should retry again
    pool.schedule_next_tasks()
    pool.fail_task(task_id, "Driver timeout")
    assert pool.tasks[task_id].retry_count == 2
    assert pool.tasks[task_id].status == TaskStatus.RETRYING

    # Re-dispatch and third failure -> max retries exceeded, marks FAILED
    pool.schedule_next_tasks()
    pool.fail_task(task_id, "Corrupt chunk data")
    assert pool.tasks[task_id].status == TaskStatus.FAILED
