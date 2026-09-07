# --- DNK-MRH-HEADER ---
# mrh_id: "tests_media_test_video_chunking"
# purpose: "Comprehensive Unit and Integration Tests for GOP-Aligned Video Chunking Engine (DNK-MEDIA-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
import pytest
from apps.api.services.video_chunking_engine import (
    VideoChunkingEngine,
    VideoStreamMetadata,
    video_chunking_engine,
)
from apps.api.db.models import (
    MediaVideoProcessingJobModel,
    MediaVideoChunkModel,
    MediaTranscodingTaskModel,
    MediaPackagingOutputModel,
    MediaWebhookConfigModel,
)


def test_metadata_analysis_and_fallback():
    engine = VideoChunkingEngine()
    meta = engine.analyze_source_metadata(
        file_path="/tmp/non_existent.mp4",
        simulated_duration=120.0,
        simulated_fps=60.0,
        simulated_resolution=(3840, 2160),
        simulated_codec="hevc",
    )

    assert meta.duration_seconds == 120.0
    assert meta.fps == 60.0
    assert meta.width == 3840
    assert meta.height == 2160
    assert meta.total_frames == 7200
    assert meta.codec_name == "hevc"
    assert len(meta.keyframe_timestamps) > 0


def test_gop_aligned_chunking_plan():
    engine = VideoChunkingEngine(default_target_chunk_duration=4.0)
    meta = engine.analyze_source_metadata(
        file_path="/tmp/sample.mp4",
        simulated_duration=30.0,
        simulated_fps=30.0,
    )

    plan = engine.build_chunking_plan(
        source_file_path="/tmp/sample.mp4",
        metadata=meta,
        target_chunk_duration=4.0,
        output_dir="/tmp/chunks",
    )

    assert plan.is_valid is True
    assert plan.validation_error is None
    assert plan.total_chunks > 0

    # Verify continuity
    for i in range(len(plan.chunks)):
        chunk = plan.chunks[i]
        assert chunk.chunk_index == i
        assert chunk.duration_seconds > 0
        assert chunk.output_chunk_path.startswith("/tmp/chunks/chunk_")
        if i > 0:
            assert abs(plan.chunks[i - 1].end_time_seconds - chunk.start_time_seconds) < 0.001

    assert plan.chunks[0].start_time_seconds == 0.0
    assert plan.chunks[-1].end_time_seconds == meta.duration_seconds


def test_ffmpeg_split_command_generation():
    engine = VideoChunkingEngine()
    meta = engine.analyze_source_metadata(
        file_path="/tmp/input.mov",
        simulated_duration=10.0,
    )
    plan = engine.build_chunking_plan(
        source_file_path="/tmp/input.mov",
        metadata=meta,
        target_chunk_duration=4.0,
    )

    assert len(plan.chunks) >= 2
    first_cmd = plan.chunks[0].ffmpeg_split_command
    assert first_cmd[0] == "ffmpeg"
    assert "-ss" in first_cmd
    assert "-to" in first_cmd
    assert "-c" in first_cmd
    assert "copy" in first_cmd
    assert "-avoid_negative_ts" in first_cmd
    assert "make_zero" in first_cmd


def test_short_video_chunking():
    engine = VideoChunkingEngine()
    # Video shorter than target chunk duration
    meta = engine.analyze_source_metadata(
        file_path="/tmp/short.mp4",
        simulated_duration=2.5,
    )
    plan = engine.build_chunking_plan(
        source_file_path="/tmp/short.mp4",
        metadata=meta,
        target_chunk_duration=6.0,
    )

    assert plan.is_valid is True
    assert plan.total_chunks == 1
    assert plan.chunks[0].duration_seconds == 2.5
    assert plan.chunks[0].start_time_seconds == 0.0
    assert plan.chunks[0].end_time_seconds == 2.5


def test_invalid_duration_handling():
    engine = VideoChunkingEngine()
    meta = VideoStreamMetadata(
        duration_seconds=0.0,
        width=1920,
        height=1080,
        fps=30.0,
        total_frames=0,
        codec_name="h264",
        bitrate_kbps=0,
    )
    plan = engine.build_chunking_plan(
        source_file_path="/tmp/empty.mp4",
        metadata=meta,
    )
    assert plan.is_valid is False
    assert plan.total_chunks == 0


def test_db_models_instantiation():
    workspace_id = str(uuid.uuid4())
    job = MediaVideoProcessingJobModel(
        workspace_id=workspace_id,
        source_file_path="/storage/raw/source.mp4",
        source_file_size_bytes=104857600,
        source_duration_seconds=120.50,
        status="pending",
    )
    assert job.workspace_id == workspace_id
    assert job.status == "pending"
    assert job.source_file_size_bytes == 104857600

    chunk = MediaVideoChunkModel(
        job_id=job.id,
        chunk_index=0,
        start_frame=0,
        end_frame=120,
        start_time_seconds=0.0,
        end_time_seconds=4.0,
        chunk_file_path="/storage/chunks/chunk_0.mp4",
        status="pending",
    )
    assert chunk.job_id == job.id
    assert chunk.chunk_index == 0

    task = MediaTranscodingTaskModel(
        chunk_id=chunk.id,
        job_id=job.id,
        codec="h264",
        resolution="1080p",
        target_bitrate_kbps=4500,
        hardware_acceleration="videotoolbox",
    )
    assert task.codec == "h264"
    assert task.resolution == "1080p"
    assert task.hardware_acceleration == "videotoolbox"

    packaging = MediaPackagingOutputModel(
        job_id=job.id,
        packaging_type="hls",
        playlist_file_path="/storage/hls/master.m3u8",
        variant_resolutions=["1080p", "720p", "480p"],
    )
    assert packaging.packaging_type == "hls"
    assert len(packaging.variant_resolutions) == 3

    webhook = MediaWebhookConfigModel(
        workspace_id=workspace_id,
        webhook_url="https://api.example.com/webhooks/video",
        secret_token="secret-key-123",
        enabled=True,
    )
    assert webhook.enabled is True
    assert webhook.secret_token == "secret-key-123"
