# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_video_packaging_engine"
# purpose: "HLS & MPEG-DASH Adaptive Bitrate Packaging Engine (DNK-MEDIA-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from apps.api.services.distributed_transcoding_worker import (
    ABRProfileSpec,
    STANDARD_ABR_LADDER,
)
from apps.api.services.hardware_acceleration_manager import VideoCodec


class PackagingFormat(str, Enum):
    HLS = "hls"
    DASH = "dash"
    BOTH = "both"


@dataclass
class SegmentInfo:
    segment_index: int
    uri: str
    duration_seconds: float
    byte_size: Optional[int] = None


@dataclass
class VariantPlaylistSpec:
    codec: VideoCodec
    profile: ABRProfileSpec
    relative_playlist_path: str
    segments: List[SegmentInfo]
    target_duration: int
    media_sequence: int = 0


@dataclass
class PackagingResult:
    job_id: str
    format: PackagingFormat
    hls_master_playlist_path: Optional[str] = None
    hls_master_playlist_content: Optional[str] = None
    dash_manifest_path: Optional[str] = None
    dash_manifest_content: Optional[str] = None
    variant_playlists: Dict[str, str] = field(default_factory=dict)
    is_valid: bool = True
    error_message: Optional[str] = None


class VideoPackagingEngine:
    """
    Enterprise HLS & MPEG-DASH Adaptive Bitrate Packaging Engine.
    Generates RFC 8216 compliant HLS master playlists (#EXT-X-STREAM-INF) and ISO/IEC 23009-1 compliant DASH MPD manifests.
    """

    def generate_hls_variant_playlist(
        self,
        variant_spec: VariantPlaylistSpec,
    ) -> str:
        """
        Generates RFC 8216 HLS Media Playlist (.m3u8).
        """
        lines = [
            "#EXTM3U",
            "#EXT-X-VERSION:6",
            f"#EXT-X-TARGETDURATION:{variant_spec.target_duration}",
            f"#EXT-X-MEDIA-SEQUENCE:{variant_spec.media_sequence}",
            "#EXT-X-PLAYLIST-TYPE:VOD",
        ]

        for seg in variant_spec.segments:
            lines.append(f"#EXTINF:{seg.duration_seconds:.4f},")
            lines.append(seg.uri)

        lines.append("#EXT-X-ENDLIST")
        return "\n".join(lines) + "\n"

    def generate_hls_master_playlist(
        self,
        variants: List[VariantPlaylistSpec],
    ) -> str:
        """
        Generates RFC 8216 HLS Master Multivariant Playlist (#EXT-X-STREAM-INF).
        """
        lines = [
            "#EXTM3U",
            "#EXT-X-VERSION:6",
            "#EXT-X-INDEPENDENT-SEGMENTS",
        ]

        # Codec string helper
        def get_codec_rfc(codec: VideoCodec) -> str:
            if codec == VideoCodec.H264:
                return "avc1.640028,mp4a.40.2"
            elif codec == VideoCodec.H265:
                return "hvc1.1.6.L120.90,mp4a.40.2"
            elif codec == VideoCodec.VP9:
                return "vp09.00.41.08,mp4a.40.2"
            elif codec == VideoCodec.AV1:
                return "av01.0.08M.08,mp4a.40.2"
            return "avc1.4d401f,mp4a.40.2"

        for v in variants:
            bandwidth = (v.profile.bitrate_kbps + v.profile.audio_bitrate_kbps) * 1000
            codecs_str = get_codec_rfc(v.codec)
            res_str = f"{v.profile.width}x{v.profile.height}"
            fps_str = f"{v.profile.fps:.3f}".rstrip("0").rstrip(".")

            stream_inf = (
                f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},AVERAGE-BANDWIDTH={bandwidth},'
                f'RESOLUTION={res_str},FRAME-RATE={fps_str},CODECS="{codecs_str}"'
            )
            lines.append(stream_inf)
            lines.append(v.relative_playlist_path)

        return "\n".join(lines) + "\n"

    def generate_dash_manifest(
        self,
        job_id: str,
        duration_seconds: float,
        variants: List[VariantPlaylistSpec],
        min_buffer_time_seconds: float = 2.0,
    ) -> str:
        """
        Generates ISO/IEC 23009-1 compliant MPEG-DASH XML MPD manifest.
        """
        mpd = ET.Element(
            "MPD",
            xmlns="urn:mpeg:dash:schema:mpd:2011",
            profiles="urn:mpeg:dash:profile:isoff-on-demand:2011",
            type="static",
            mediaPresentationDuration=f"PT{duration_seconds:.2f}S",
            minBufferTime=f"PT{min_buffer_time_seconds:.1f}S",
        )

        period = ET.SubElement(mpd, "Period", id=f"period_{job_id}", start="PT0S", duration=f"PT{duration_seconds:.2f}S")

        # Video AdaptationSet
        video_adapt = ET.SubElement(
            period,
            "AdaptationSet",
            id="video",
            contentType="video",
            mimeType="video/mp4",
            segmentAlignment="true",
            subsegmentAlignment="true",
            startWithSAP="1",
        )

        def get_dash_codec(c: VideoCodec) -> str:
            if c == VideoCodec.H264:
                return "avc1.640028"
            elif c == VideoCodec.H265:
                return "hvc1.1.6.L120.90"
            elif c == VideoCodec.VP9:
                return "vp09.00.41.08"
            elif c == VideoCodec.AV1:
                return "av01.0.08M.08"
            return "avc1.640028"

        for idx, v in enumerate(variants):
            bandwidth = v.profile.bitrate_kbps * 1000
            rep = ET.SubElement(
                video_adapt,
                "Representation",
                id=f"video_{v.profile.resolution_name}_{v.codec.value}",
                bandwidth=str(bandwidth),
                width=str(v.profile.width),
                height=str(v.profile.height),
                frameRate=str(int(v.profile.fps)),
                codecs=get_dash_codec(v.codec),
            )
            base_url = ET.SubElement(rep, "BaseURL")
            base_url.text = f"{v.codec.value}/{v.profile.resolution_name}/"

            seg_list = ET.SubElement(rep, "SegmentList", timescale="1000", duration=str(int(v.target_duration * 1000)))
            for seg in v.segments:
                ET.SubElement(seg_list, "SegmentURL", media=seg.uri)

        # Audio AdaptationSet
        audio_adapt = ET.SubElement(
            period,
            "AdaptationSet",
            id="audio",
            contentType="audio",
            mimeType="audio/mp4",
            codecs="mp4a.40.2",
            lang="en",
            segmentAlignment="true",
            startWithSAP="1",
        )
        audio_rep = ET.SubElement(
            audio_adapt,
            "Representation",
            id="audio_en_128k",
            bandwidth="128000",
            audioSamplingRate="48000",
        )
        audio_channel = ET.SubElement(audio_rep, "AudioChannelConfiguration", schemeIdUri="urn:mpeg:dash:23003:3:audio_channel_configuration:2011", value="2")

        # Convert to string with XML declaration
        xml_str = ET.tostring(mpd, encoding="utf-8").decode("utf-8")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}\n'

    def package_job_outputs(
        self,
        job_id: str,
        total_duration_seconds: float,
        transcoded_chunks_map: Dict[str, List[SegmentInfo]],
        codecs: Optional[List[VideoCodec]] = None,
        ladder: Optional[List[ABRProfileSpec]] = None,
        packaging_format: PackagingFormat = PackagingFormat.BOTH,
        output_dir: str = "/tmp/packaged_media",
    ) -> PackagingResult:
        """
        Orchestrates packaging of all transcoded chunks into HLS and DASH delivery structures.
        """
        target_codecs = codecs or [VideoCodec.H264]
        target_ladder = ladder or STANDARD_ABR_LADDER
        variants: List[VariantPlaylistSpec] = []
        variant_contents: Dict[str, str] = {}

        job_dir = f"{output_dir}/{job_id}"
        os.makedirs(job_dir, exist_ok=True)

        for codec in target_codecs:
            for abr in target_ladder:
                key = f"{codec.value}_{abr.resolution_name}"
                segments = transcoded_chunks_map.get(key, [])
                if not segments:
                    continue

                rel_playlist_path = f"{codec.value}/{abr.resolution_name}/index.m3u8"
                target_dur = max([int(round(s.duration_seconds)) for s in segments] + [4])

                var_spec = VariantPlaylistSpec(
                    codec=codec,
                    profile=abr,
                    relative_playlist_path=rel_playlist_path,
                    segments=segments,
                    target_duration=target_dur,
                )
                variants.append(var_spec)

                # Generate variant playlist content
                var_content = self.generate_hls_variant_playlist(var_spec)
                variant_contents[rel_playlist_path] = var_content

        if not variants:
            return PackagingResult(
                job_id=job_id,
                format=packaging_format,
                is_valid=False,
                error_message="No valid transcoded chunks found to package",
            )

        master_hls_path = None
        master_hls_content = None
        dash_path = None
        dash_content = None

        if packaging_format in (PackagingFormat.HLS, PackagingFormat.BOTH):
            master_hls_content = self.generate_hls_master_playlist(variants)
            master_hls_path = f"{job_dir}/master.m3u8"

        if packaging_format in (PackagingFormat.DASH, PackagingFormat.BOTH):
            dash_content = self.generate_dash_manifest(
                job_id=job_id,
                duration_seconds=total_duration_seconds,
                variants=variants,
            )
            dash_path = f"{job_dir}/manifest.mpd"

        return PackagingResult(
            job_id=job_id,
            format=packaging_format,
            hls_master_playlist_path=master_hls_path,
            hls_master_playlist_content=master_hls_content,
            dash_manifest_path=dash_path,
            dash_manifest_content=dash_content,
            variant_playlists=variant_contents,
            is_valid=True,
        )


video_packaging_engine = VideoPackagingEngine()
