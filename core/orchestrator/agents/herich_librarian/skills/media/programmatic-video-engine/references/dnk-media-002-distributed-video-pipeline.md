# DNK-MEDIA-002: Distributed Video Processing & Transcoding Pipeline

## Overview
DNK-MEDIA-002 provides a high-performance, fault-tolerant, GOP-aligned distributed video processing and adaptive bitrate packaging engine for DNK OS.

## 1. GOP-Aligned Video Chunking Engine (`apps/api/services/video_chunking_engine.py`)
- **Keyframe Analysis (`ffprobe`)**:
  - Probes video file streams for IDR/I-frame timestamps (`select_streams=v:0`, `show_frames`).
  - Calculates GOP duration and optimal split points aligned strictly to keyframes.
- **FFmpeg Split Commands**:
  - Command: `ffmpeg -ss {start_pts} -to {end_time} -i {input_path} -c copy -avoid_negative_ts make_zero {chunk_path}`
  - Guarantees zero negative PTS and frame continuity without boundary artifacts.

## 2. Hardware Acceleration Auto-Detection & Fallback Matrix (`apps/api/services/hardware_acceleration_manager.py`)
- **Hardware Probing**:
  - Probes available hardware encoders via `ffmpeg -encoders`.
  - Detection map:
    - **NVIDIA**: `h264_nvenc`, `hevc_nvenc`, `av1_nvenc`
    - **Apple**: `h264_videotoolbox`, `hevc_videotoolbox`
    - **Linux VAAPI**: `h264_vaapi`, `hevc_vaapi`, `vp9_vaapi`, `av1_vaapi`
    - **AMD AMF**: `h264_amf`, `hevc_amf`
- **Graceful Fallback Matrix**:
  - If a hardware encoder is unavailable for a target codec (e.g. Apple VideoToolbox lacking VP9/AV1 support), falls back to tuned CPU encoders (`libvpx-vp9`, `libaom-av1`, `libx264`, `libx265`).

## 3. Distributed Transcoding Worker Pool (`apps/api/services/distributed_transcoding_worker.py`)
- **Task Queue & State Machine**:
  - Redis Streams-style async task queue with state transitions: `PENDING` -> `PROCESSING` -> `COMPLETED` / `RETRYING` / `FAILED`.
  - Concurrency control via bounded worker semaphores (`concurrency_limit`).
  - Heartbeat monitoring and automatic re-queuing of stale tasks.
  - Exponential backoff retry logic ($t_{\text{backoff}} = \text{base\_delay} \times 2^{\text{retry\_count}}$).

## 4. ABR Packaging Engine (`apps/api/services/video_packaging_engine.py`)
- **HLS Master & Variant Playlists (`master.m3u8`, `index.m3u8`)**:
  - Includes `#EXT-X-STREAM-INF` tags with `BANDWIDTH`, `RESOLUTION`, `CODECS` (RFC 6381: `avc1.640028`, `hvc1.1.6.L120.90`, `vp09.00.41.08`, `av01.0.08M.08`).
  - Muxed composite bandwidth calculation: $B_{\text{total}} = (B_{\text{video}} + B_{\text{audio}}) \times 1.05$.
- **MPEG-DASH Manifest (`manifest.mpd`)**:
  - Schema-compliant XML generation using `xml.etree.ElementTree`.
  - Position-based `ET.SubElement(parent, "Period")` syntax to prevent `TypeError`.

## 5. Object Storage & Presigned URLs (`apps/api/services/media_storage_manager.py`)
- S3 / MinIO integration with SHA-256 key hashing.
- Generation of TTL-constrained Presigned PUT/GET URLs.
- In-memory LRU cache with hit/miss metric tracking.

## 6. FastAPI Video Router & WebSockets (`apps/api/services/media_pipeline_router.py`)
- REST endpoints: Ingestion, Chunking, Transcoding, Packaging, Worker Registration, Health.
- Real-time WebSocket streaming (`/api/v1/media/jobs/{job_id}/ws`) broadcasting job progress and chunk completion events.
