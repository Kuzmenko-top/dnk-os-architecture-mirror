# --- DNK-MRH-HEADER ---
# mrh_id: "tests_media_test_video_packaging"
# purpose: "Comprehensive Unit & Integration Tests for HLS & MPEG-DASH Packaging Engine and S3 Storage Manager (DNK-MEDIA-002)"
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
from apps.api.services.video_packaging_engine import (
    video_packaging_engine,
    PackagingFormat,
    SegmentInfo,
    VariantPlaylistSpec,
)
from apps.api.services.hardware_acceleration_manager import VideoCodec
from apps.api.services.distributed_transcoding_worker import (
    STANDARD_ABR_LADDER,
    ABRProfileSpec,
)
from apps.api.services.media_storage_manager import (
    media_storage_manager,
    MediaStorageManager,
    StorageConfig,
)


def test_hls_variant_playlist_generation():
    segments = [
        SegmentInfo(segment_index=0, uri="seg_0000.ts", duration_seconds=4.004, byte_size=1024 * 500),
        SegmentInfo(segment_index=1, uri="seg_0001.ts", duration_seconds=4.004, byte_size=1024 * 520),
        SegmentInfo(segment_index=2, uri="seg_0002.ts", duration_seconds=3.980, byte_size=1024 * 490),
    ]

    variant = VariantPlaylistSpec(
        codec=VideoCodec.H264,
        profile=STANDARD_ABR_LADDER[0],
        relative_playlist_path="h264_1080p/index.m3u8",
        segments=segments,
        target_duration=5,
    )

    playlist = video_packaging_engine.generate_hls_variant_playlist(variant_spec=variant)

    assert "#EXTM3U" in playlist
    assert "#EXT-X-VERSION:6" in playlist
    assert "#EXT-X-TARGETDURATION:5" in playlist
    assert "#EXTINF:4.004" in playlist
    assert "seg_0000.ts" in playlist
    assert "seg_0001.ts" in playlist
    assert "seg_0002.ts" in playlist
    assert "#EXT-X-ENDLIST" in playlist


def test_hls_master_playlist_generation():
    variants = [
        VariantPlaylistSpec(
            codec=VideoCodec.H264,
            profile=STANDARD_ABR_LADDER[0],
            relative_playlist_path="h264_1080p/index.m3u8",
            segments=[],
            target_duration=5,
        ),
        VariantPlaylistSpec(
            codec=VideoCodec.H265,
            profile=STANDARD_ABR_LADDER[1],
            relative_playlist_path="hevc_720p/index.m3u8",
            segments=[],
            target_duration=5,
        ),
    ]

    master_m3u8 = video_packaging_engine.generate_hls_master_playlist(variants=variants)

    assert "#EXTM3U" in master_m3u8
    assert "#EXT-X-VERSION:6" in master_m3u8
    assert master_m3u8.count("#EXT-X-STREAM-INF") == 2
    assert "BANDWIDTH=" in master_m3u8
    assert "RESOLUTION=1920x1080" in master_m3u8
    assert "h264_1080p/index.m3u8" in master_m3u8
    assert "hevc_720p/index.m3u8" in master_m3u8


def test_dash_manifest_generation():
    variants = [
        VariantPlaylistSpec(
            codec=VideoCodec.H264,
            profile=STANDARD_ABR_LADDER[0],
            relative_playlist_path="h264_1080p/index.m3u8",
            segments=[],
            target_duration=5,
        ),
        VariantPlaylistSpec(
            codec=VideoCodec.VP9,
            profile=STANDARD_ABR_LADDER[1],
            relative_playlist_path="vp9_720p/index.m3u8",
            segments=[],
            target_duration=5,
        ),
    ]

    mpd_xml = video_packaging_engine.generate_dash_manifest(
        job_id="test_job_dash",
        duration_seconds=120.0,
        variants=variants,
    )

    assert 'xmlns="urn:mpeg:dash:schema:mpd:2011"' in mpd_xml
    assert 'mediaPresentationDuration="PT120.00S"' in mpd_xml
    assert '<Period id="period_test_job_dash"' in mpd_xml
    assert '<AdaptationSet' in mpd_xml
    assert 'mimeType="video/mp4"' in mpd_xml
    assert 'codecs="avc1.640028"' in mpd_xml
    assert 'codecs="vp09.00.41.08"' in mpd_xml
    assert '<Representation id="video_1080p_h264"' in mpd_xml
    assert 'bandwidth="4500000"' in mpd_xml


def test_full_packaging_job_output():
    job_id = "job_pack_test"
    segments = [
        SegmentInfo(segment_index=i, uri=f"chunk_{i:04d}.ts", duration_seconds=4.0, byte_size=500000)
        for i in range(5)
    ]
    transcoded_map = {
        "h264_1080p": segments,
        "h264_720p": segments,
    }

    result = video_packaging_engine.package_job_outputs(
        job_id=job_id,
        total_duration_seconds=20.0,
        transcoded_chunks_map=transcoded_map,
        codecs=[VideoCodec.H264],
        packaging_format=PackagingFormat.BOTH,
    )

    assert result.job_id == job_id
    assert result.is_valid is True
    assert result.hls_master_playlist_content is not None
    assert result.dash_manifest_content is not None
    assert len(result.variant_playlists) == 2


def test_media_storage_manager_lifecycle():
    storage = MediaStorageManager()
    job_id = "test_s3_job"

    # Upload artifact
    test_bytes = b"#EXTM3U\n#EXT-X-VERSION:6\n"
    artifact = storage.upload_bytes(
        job_id=job_id,
        relative_path="master.m3u8",
        data=test_bytes,
        content_type="application/vnd.apple.mpegurl",
        artifact_type="packaged",
    )

    assert artifact.byte_size == len(test_bytes)
    assert artifact.etag != ""

    # Download back
    key = artifact.key
    downloaded = storage.download_bytes(key=key)
    assert downloaded == test_bytes

    # Presigned URLs
    get_url = storage.generate_presigned_get_url(key, expires_in=3600)
    assert key in get_url

    put_info = storage.generate_presigned_put_url(job_id=job_id, relative_path="raw/source.mp4", expires_in=1800)
    assert "source.mp4" in put_info["upload_url"]

    # List artifacts
    artifacts = storage.list_job_artifacts(job_id)
    assert len(artifacts) == 1

    # Delete job artifacts
    deleted_count = storage.delete_job_artifacts(job_id)
    assert deleted_count == 1
    assert len(storage.list_job_artifacts(job_id)) == 0
