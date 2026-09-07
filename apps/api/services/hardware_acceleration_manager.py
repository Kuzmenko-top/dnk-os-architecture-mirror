# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_hardware_acceleration_manager"
# purpose: "Hardware Acceleration Auto-Detection & Encoder Optimization Manager (DNK-MEDIA-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import subprocess
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set

logger = logging.getLogger("dnk.media.hardware_accel")


class HardwareAccelType(str, Enum):
    NVENC = "nvenc"              # NVIDIA GPU
    VIDEOTOOLBOX = "videotoolbox"  # Apple Silicon / macOS
    VAAPI = "vaapi"              # Intel / AMD Linux
    AMF = "amf"                  # AMD Windows/Linux
    CPU = "cpu"                  # Pure Software fallback


class VideoCodec(str, Enum):
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    AV1 = "av1"


@dataclass
class EncoderProfile:
    codec: VideoCodec
    hardware_accel: HardwareAccelType
    ffmpeg_encoder_name: str
    preset: str
    rate_control_flags: List[str]
    pixel_format: str = "yuv420p"
    extra_flags: List[str] = field(default_factory=list)


class HardwareAccelerationManager:
    """
    Auto-detects available GPU/ASIC hardware encoders and provides optimized FFmpeg parameters
    with deterministic fallback to high-quality CPU encoders.
    """

    # Mapping of (Codec, HardwareAccelType) -> FFmpeg encoder name
    ENCODER_MAPPING = {
        (VideoCodec.H264, HardwareAccelType.NVENC): "h264_nvenc",
        (VideoCodec.H265, HardwareAccelType.NVENC): "hevc_nvenc",
        (VideoCodec.AV1, HardwareAccelType.NVENC): "av1_nvenc",

        (VideoCodec.H264, HardwareAccelType.VIDEOTOOLBOX): "h264_videotoolbox",
        (VideoCodec.H265, HardwareAccelType.VIDEOTOOLBOX): "hevc_videotoolbox",

        (VideoCodec.H264, HardwareAccelType.VAAPI): "h264_vaapi",
        (VideoCodec.H265, HardwareAccelType.VAAPI): "hevc_vaapi",
        (VideoCodec.VP9, HardwareAccelType.VAAPI): "vp9_vaapi",
        (VideoCodec.AV1, HardwareAccelType.VAAPI): "av1_vaapi",

        (VideoCodec.H264, HardwareAccelType.AMF): "h264_amf",
        (VideoCodec.H265, HardwareAccelType.AMF): "hevc_amf",

        # Fallback CPU Encoders
        (VideoCodec.H264, HardwareAccelType.CPU): "libx264",
        (VideoCodec.H265, HardwareAccelType.CPU): "libx265",
        (VideoCodec.VP9, HardwareAccelType.CPU): "libvpx-vp9",
        (VideoCodec.AV1, HardwareAccelType.CPU): "libaom-av1",
    }

    def __init__(self, force_accel: Optional[HardwareAccelType] = None):
        self._force_accel = force_accel
        self._available_encoders_cache: Optional[Set[str]] = None
        self._detected_accel_type: Optional[HardwareAccelType] = None

    def probe_available_ffmpeg_encoders(self) -> Set[str]:
        """Queries FFmpeg for compiled-in and accessible video encoders."""
        if self._available_encoders_cache is not None:
            return self._available_encoders_cache

        encoders: Set[str] = set()
        try:
            cmd = ["ffmpeg", "-encoders", "-v", "quiet"]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            if proc.returncode == 0:
                for line in proc.stdout.splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[0].startswith("V"):
                        encoders.add(parts[1])
        except Exception as err:
            logger.debug(f"Failed to probe FFmpeg encoders: {err}")

        # If empty or not installed, provide standard CPU fallback encoders
        if not encoders:
            encoders = {"libx264", "libx265", "libvpx-vp9", "libaom-av1"}

        self._available_encoders_cache = encoders
        return encoders

    def detect_best_hardware_acceleration(self) -> HardwareAccelType:
        """Determines the highest throughput hardware acceleration available."""
        if self._force_accel:
            return self._force_accel

        if self._detected_accel_type is not None:
            return self._detected_accel_type

        encoders = self.probe_available_ffmpeg_encoders()

        # Priority 1: NVENC (NVIDIA)
        if "h264_nvenc" in encoders:
            self._detected_accel_type = HardwareAccelType.NVENC
            return HardwareAccelType.NVENC

        # Priority 2: VideoToolbox (macOS Apple Silicon / Intel)
        if "h264_videotoolbox" in encoders:
            self._detected_accel_type = HardwareAccelType.VIDEOTOOLBOX
            return HardwareAccelType.VIDEOTOOLBOX

        # Priority 3: VAAPI (Intel / AMD Linux)
        if "h264_vaapi" in encoders:
            self._detected_accel_type = HardwareAccelType.VAAPI
            return HardwareAccelType.VAAPI

        # Priority 4: AMF (AMD)
        if "h264_amf" in encoders:
            self._detected_accel_type = HardwareAccelType.AMF
            return HardwareAccelType.AMF

        # Fallback: Pure CPU
        self._detected_accel_type = HardwareAccelType.CPU
        return HardwareAccelType.CPU

    def get_encoder_profile(
        self,
        codec: VideoCodec,
        target_bitrate_kbps: int,
        target_fps: float = 30.0,
        gop_size: int = 60,
        preferred_accel: Optional[HardwareAccelType] = None,
    ) -> EncoderProfile:
        """
        Builds optimized encoder profile flags based on target bitrate, resolution, and hardware.
        Automatically falls back to CPU if hardware acceleration is unavailable for the requested codec.
        """
        accel = preferred_accel or self.detect_best_hardware_acceleration()
        encoders = self.probe_available_ffmpeg_encoders()

        # Check if hardware encoder exists for this codec
        encoder_name = self.ENCODER_MAPPING.get((codec, accel))
        if not encoder_name or encoder_name not in encoders:
            # Fallback to CPU for this codec
            accel = HardwareAccelType.CPU
            encoder_name = self.ENCODER_MAPPING[(codec, HardwareAccelType.CPU)]

        rate_flags: List[str] = []
        extra_flags: List[str] = []
        preset = "medium"

        if accel == HardwareAccelType.NVENC:
            preset = "p4"  # Balance speed/quality on NVENC
            rate_flags = [
                "-b:v", f"{target_bitrate_kbps}k",
                "-maxrate", f"{int(target_bitrate_kbps * 1.5)}k",
                "-bufsize", f"{target_bitrate_kbps * 2}k",
                "-spatial-aq", "1",
                "-temporal-aq", "1",
            ]
            extra_flags = ["-g", str(gop_size), "-keyint_min", str(gop_size)]

        elif accel == HardwareAccelType.VIDEOTOOLBOX:
            preset = "medium"
            rate_flags = [
                "-b:v", f"{target_bitrate_kbps}k",
                "-maxrate", f"{int(target_bitrate_kbps * 1.5)}k",
                "-bufsize", f"{target_bitrate_kbps * 2}k",
            ]
            extra_flags = ["-g", str(gop_size), "-keyint_min", str(gop_size), "-realtime", "0"]

        elif accel == HardwareAccelType.VAAPI:
            preset = "medium"
            rate_flags = [
                "-b:v", f"{target_bitrate_kbps}k",
                "-maxrate", f"{int(target_bitrate_kbps * 1.5)}k",
                "-bufsize", f"{target_bitrate_kbps * 2}k",
            ]
            extra_flags = ["-g", str(gop_size)]

        elif accel == HardwareAccelType.CPU:
            if codec == VideoCodec.H264:
                preset = "veryfast"
                rate_flags = [
                    "-b:v", f"{target_bitrate_kbps}k",
                    "-maxrate", f"{int(target_bitrate_kbps * 1.5)}k",
                    "-bufsize", f"{target_bitrate_kbps * 2}k",
                ]
                extra_flags = ["-g", str(gop_size), "-keyint_min", str(gop_size), "-sc_threshold", "0"]
            elif codec == VideoCodec.H265:
                preset = "fast"
                rate_flags = [
                    "-b:v", f"{target_bitrate_kbps}k",
                    "-maxrate", f"{int(target_bitrate_kbps * 1.5)}k",
                    "-bufsize", f"{target_bitrate_kbps * 2}k",
                ]
                extra_flags = ["-g", str(gop_size), "-x265-params", f"keyint={gop_size}:min-keyint={gop_size}:no-open-gop=1"]
            elif codec == VideoCodec.VP9:
                preset = "good"
                rate_flags = [
                    "-b:v", f"{target_bitrate_kbps}k",
                    "-minrate", f"{int(target_bitrate_kbps * 0.7)}k",
                    "-maxrate", f"{int(target_bitrate_kbps * 1.3)}k",
                ]
                extra_flags = ["-g", str(gop_size), "-quality", "good", "-speed", "4"]
            elif codec == VideoCodec.AV1:
                preset = "8"  # Fast SVT-AV1 / libaom preset
                rate_flags = [
                    "-b:v", f"{target_bitrate_kbps}k",
                ]
                extra_flags = ["-g", str(gop_size), "-cpu-used", "6"]

        return EncoderProfile(
            codec=codec,
            hardware_accel=accel,
            ffmpeg_encoder_name=encoder_name,
            preset=preset,
            rate_control_flags=rate_flags,
            pixel_format="yuv420p",
            extra_flags=extra_flags,
        )

    def build_transcode_command(
        self,
        input_chunk_path: str,
        output_chunk_path: str,
        profile: EncoderProfile,
        target_width: int,
        target_height: int,
    ) -> List[str]:
        """Constructs full FFmpeg command for transcoding a single video chunk."""
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_chunk_path,
            "-c:v", profile.ffmpeg_encoder_name,
            "-vf", f"scale={target_width}:{target_height}",
            "-pix_fmt", profile.pixel_format,
        ]

        if profile.preset:
            if profile.hardware_accel == HardwareAccelType.NVENC:
                cmd.extend(["-preset", profile.preset])
            elif profile.hardware_accel == HardwareAccelType.CPU and profile.codec in (VideoCodec.H264, VideoCodec.H265):
                cmd.extend(["-preset", profile.preset])

        cmd.extend(profile.rate_control_flags)
        cmd.extend(profile.extra_flags)
        # Audio pass-through / transcode
        cmd.extend(["-c:a", "aac", "-b:a", "128k", "-ac", "2", output_chunk_path])
        return cmd


hardware_acceleration_manager = HardwareAccelerationManager()
