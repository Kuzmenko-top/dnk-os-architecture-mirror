# --- DNK-MRH-HEADER ---
# mrh_id: "tests_media_test_hardware_acceleration"
# purpose: "Unit & Integration Tests for Hardware Acceleration Manager (DNK-MEDIA-002 Phase 2)"
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
from apps.api.services.hardware_acceleration_manager import (
    HardwareAccelerationManager,
    HardwareAccelType,
    VideoCodec,
    EncoderProfile,
    hardware_acceleration_manager,
)


def test_hardware_acceleration_detection_cpu_fallback():
    # Force mock with only CPU encoders
    mgr = HardwareAccelerationManager()
    mgr._available_encoders_cache = {"libx264", "libx265", "libvpx-vp9", "libaom-av1"}
    
    detected = mgr.detect_best_hardware_acceleration()
    assert detected == HardwareAccelType.CPU


def test_hardware_acceleration_detection_nvenc_priority():
    mgr = HardwareAccelerationManager()
    mgr._available_encoders_cache = {"h264_nvenc", "hevc_nvenc", "h264_videotoolbox", "libx264"}
    
    detected = mgr.detect_best_hardware_acceleration()
    assert detected == HardwareAccelType.NVENC


def test_hardware_acceleration_detection_videotoolbox():
    mgr = HardwareAccelerationManager()
    mgr._available_encoders_cache = {"h264_videotoolbox", "hevc_videotoolbox", "libx264"}
    
    detected = mgr.detect_best_hardware_acceleration()
    assert detected == HardwareAccelType.VIDEOTOOLBOX


def test_hardware_acceleration_detection_vaapi():
    mgr = HardwareAccelerationManager()
    mgr._available_encoders_cache = {"h264_vaapi", "hevc_vaapi", "libx264"}
    
    detected = mgr.detect_best_hardware_acceleration()
    assert detected == HardwareAccelType.VAAPI


def test_encoder_profile_generation_h264_nvenc():
    mgr = HardwareAccelerationManager(force_accel=HardwareAccelType.NVENC)
    mgr._available_encoders_cache = {"h264_nvenc", "hevc_nvenc", "libx264"}

    profile = mgr.get_encoder_profile(
        codec=VideoCodec.H264,
        target_bitrate_kbps=4500,
        gop_size=60,
    )

    assert profile.codec == VideoCodec.H264
    assert profile.hardware_accel == HardwareAccelType.NVENC
    assert profile.ffmpeg_encoder_name == "h264_nvenc"
    assert profile.preset == "p4"
    assert "-b:v" in profile.rate_control_flags
    assert "4500k" in profile.rate_control_flags


def test_encoder_profile_fallback_when_codec_unsupported():
    mgr = HardwareAccelerationManager(force_accel=HardwareAccelType.VIDEOTOOLBOX)
    # VideoToolbox does not support VP9, so it must fall back to CPU libvpx-vp9
    mgr._available_encoders_cache = {"h264_videotoolbox", "hevc_videotoolbox", "libvpx-vp9"}

    profile = mgr.get_encoder_profile(
        codec=VideoCodec.VP9,
        target_bitrate_kbps=2500,
    )

    assert profile.codec == VideoCodec.VP9
    assert profile.hardware_accel == HardwareAccelType.CPU
    assert profile.ffmpeg_encoder_name == "libvpx-vp9"


def test_build_transcode_command():
    mgr = HardwareAccelerationManager()
    mgr._available_encoders_cache = {"libx264", "libx265"}

    profile = mgr.get_encoder_profile(
        codec=VideoCodec.H264,
        target_bitrate_kbps=2500,
        preferred_accel=HardwareAccelType.CPU,
    )

    cmd = mgr.build_transcode_command(
        input_chunk_path="/tmp/chunk_0.mp4",
        output_chunk_path="/tmp/out_720p.mp4",
        profile=profile,
        target_width=1280,
        target_height=720,
    )

    assert cmd[0] == "ffmpeg"
    assert "-i" in cmd
    assert "/tmp/chunk_0.mp4" in cmd
    assert "-c:v" in cmd
    assert "libx264" in cmd
    assert "scale=1280:720" in cmd[cmd.index("-vf") + 1]
    assert cmd[-1] == "/tmp/out_720p.mp4"
