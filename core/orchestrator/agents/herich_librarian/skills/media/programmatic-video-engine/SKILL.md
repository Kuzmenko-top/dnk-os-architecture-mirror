---
name: programmatic-video-engine
description: Use when building programmatic video engines.
version: 1.0.0
author: DNK-e.com Maksym
license: DNK-INTERNAL
category: media
metadata:
  hermes:
    tags: [video, animation, remotion, ffmpeg, dsl]
    related_skills: [ascii-video, ffmpeg]
---

# Programmatic Video Engine Architecture

## When to Use
Use when building or extending programmatic video rendering engines, timeline AST schemas, keyframe interpolators, headless frame renderers, or FFmpeg chunk-rendering pipelines.

## 📐 Core Architecture & Invariants

1. **AST DSL Schema Layer**:
   - Represent compositions as declarative AST objects (`VideoCompositionSchema`, `Track`, `Clip`, `Keyframe`, `Transition`).
   - Support distinct clip types (`text`, `canvas`, `svg`, `video`, `audio`, `image`).
   - Enforce deterministic FPS standards (`24`, `30`, `60`).

2. **Easing & Physics Interpolation**:
   - Standard curves: `linear`, `quad_in/out/in_out`, `cubic_in/out/in_out`.
   - **Cubic Bezier**: Newton-Raphson root finding for $t \in [0, 1]$ on control points $(x_1, y_1, x_2, y_2)$.
   - **Spring Physics**: Analytical damped harmonic oscillator solution ($x(t) = 1 - e^{-\zeta \omega_0 t} \cdot (\cos(\omega_d t) + \frac{\zeta \omega_0}{\omega_d} \sin(\omega_d t))$).
   - RGBA color blending: Interpolate channels individually in float space, format back to `#RRGGBB` / `#RRGGBBAA`.

3. **FPS Controller & SMPTE Timecode (Zero-Drift)**:
   - Calculate frame timestamps strictly from integer frame division to guarantee zero time drift.
   - Convert bidirectionally between frame index and SMPTE timecode (`HH:MM:SS:FF`).
   - Partition total frames into deterministic chunk intervals `[(start, end), ...]` for parallel or batch rendering.

4. **Headless Layered RGBA Frame Renderer**:
   - Render frames onto an RGBA canvas background using Pillow (`PIL.Image`, `PIL.ImageDraw`).
   - Sort clips across tracks by `layer` z-index before alpha blending.
   - Support layer types:
     - `text`: Custom font sizes, colors, positioning, opacity.
     - `canvas`: Vector primitives (rectangles, circles, corner radii, stroke, fill).
     - `image`: Resizing, opacity scaling, and alpha mask compositing.
   - Render chunks to disk as sequential PNG files (`frame_%06d.png`) to keep RAM consumption constant.

5. **FFmpeg Orchestration & Security Boundary**:
   - **Zero Shell Injection Invariant**: NEVER use `shell=True`. Execute FFmpeg strictly via list argument vectors (`subprocess.run(args, ...)`).
   - **Path & Resource Validation**: Enforce fail-closed path validation (`validate_resource_path`), path traversal rejection (`..`), and file extension whitelists (`.png`, `.jpg`, `.mp4`, `.mov`, `.mp3`, `.wav`, `.ttf`, `.otf`, `.svg`).
   - **Audio Muxing & Encoding**: Mux background/clip audio tracks with `-c:a aac -b:a 192k -shortest` and produce web-optimized video with `-c:v libx264 -preset veryfast -pix_fmt yuv420p -movflags +faststart`.

6. **Audio-First Ingestion & Gemini 3.5 Transcribe Pipelines**:
   - Local audio extraction via FFmpeg (16kHz mono Opus) before cloud upload saves ~98% bandwidth on large archives (1000+ GB).
   - Use `google-genai` (v2.0.0+) Interactions API with `gemini-3.5-transcribe` (`mode="smart"`, `word_timestamps=True`, `diarization=True`).
   - Calculate inter-word gap $\Delta t$ to identify silences (>1.2s) and filler words for auto-cut jumpcut assembly.
   - For technical details and code snippets, see `references/gemini-transcribe-media-pipeline.md`.

7. **SHA-256 Ingestion Pipeline, Deduplication & Database Persistence (DNK-STD-0082)**:
   - **SHA-256 Hash Pre-Check**: Calculate file content SHA-256 hash before running expensive FFmpeg probes or encoding. Check against `Footage` table (`file_hash` unique index) for instant duplicate detection.
   - **FFprobe Video Probe**: Extract duration, resolution, fps, and codecs from incoming media files into structured metadata objects (`VideoMetadata`).
   - **Audio Extraction & Chunking**: Extract 16kHz mono audio and partition long recordings into 30–45 minute chunk files for chunked AI transcription.
   - **Model Registration Invariant**: Always import all declarative models (e.g. `from db.models.footage import Footage`) BEFORE executing `Base.metadata.create_all(bind=engine)` so table schemas are registered in `Base.metadata`.

8. **Composable Dynamic Templates & Extensible Registry**:
   - **Composable Builders**: Implement templates as pure functions/builders producing deterministic `VideoCompositionSchema` AST instances without hard-coded state.
   - **Shopify Product Promo**: 9:16 layout (1080x1920, 30fps), featuring dynamic title, original/promo price drop badge, 3D product spin/zoom keyframes, and kinetic CTA.
   - **UGC Vertical Reel**: 9:16 format (TikTok / Reels / Shorts), featuring creator profile header, timed kinetic subtitles, and scene transitions (`glitch`, `crossfade`, `slide_left`, `kinetic_zoom`).
   - **Template Registry**: Manage template metadata (`TemplateMetadata`), tag-based catalog discovery, input parameter schemas, and thread-safe dynamic composition creation.
   - For architecture details and schema specs, see `references/phase3-ecommerce-ugc-templates.md`.

9. **REST API, Worker Queue, Asset Cache & Progress Streamer (Phase 4)**:
   - **Non-blocking REST API**: `POST /api/v1/media/render` and `POST /api/v1/media/preview` return immediate job tracking IDs (`job_id`) without blocking HTTP response threads.
   - **Async Job Queue**: `MediaJobQueue` executes jobs with bounded concurrency (`asyncio.Semaphore`), transition status (`QUEUED` -> `PROCESSING` -> `COMPLETED` / `FAILED`), and safe exception handling.
   - **Deterministic Asset Caching**: `CacheManager` hashes composition structures using SHA-256 to avoid redundant renders, serving cached video paths with CDN-ready URLs.
   - **Real-time SSE Progress Streaming**: `ProgressStreamer` broadcasts progress percentages (0–100%) and current execution phase over Server-Sent Events (`GET /api/v1/media/jobs/{job_id}/stream`).

10. **Auto Cut Decision Engine, Silence & Filler Detection (DNK-STD-0084)**:
   - **Filler Word Detection**: Standardize patterns across languages (`um`, `uh`, `er`, `hmm`, `like`, `basically` for EN; `ну`, `типу`, `е-е`, `коротше`, `значить`, `отже` for UA) and filter transcript words via regex sanitization (`re.sub(r"[^\w\s-]", "", word).strip().lower()`).
   - **Silence Pause Detection**: Measure gaps between adjacent sorted words ($\Delta t = \text{word}_{i+1}.\text{start} - \text{word}_i.\text{end}$). Gaps $\ge \text{threshold\_sec}$ (default 1.2s) generate pause cut ranges.
   - **Merged Cut Decision List**: Combine filler and pause cut ranges, merging adjacent ranges within `merge_threshold_sec` (default 0.5s) to avoid micro-jumpcut stutter.
   - **Timeline Keep Ranges**: Invert merged cut ranges against total video duration (`total_duration_sec`) to construct clean timeline segment lists (`KeepRange(start, end, duration_sec)`) for FFmpeg filtergraph or timeline assembly.

11. **SCONES Memory Vault, Vector Embeddings & Semantic Search (DNK-STD-0085)**:
   - **SQLAlchemy Reserved Attribute Name Invariant**: On models inheriting from Declarative Base, NEVER name a relationship or column attribute `metadata` (it conflicts with `DeclarativeBase.metadata`, causing `AttributeError: Attribute name 'metadata' is reserved`). Always use `metadata_rel` or explicit names like `footage_metadata`.
   - **Cross-Database `VectorColumn` Fallback**: When using `pgvector.sqlalchemy.Vector(1024)`, wrap the column type in a custom `TypeDecorator` that renders `Vector(1024)` on PostgreSQL dialect and `JSON` on SQLite dialects, enabling seamless SQLite in-memory test execution without requiring `pgvector` binaries.
   - **L2-Normalized Deterministic Hash Vector Generator**: Compute 1024-dim floating point vectors by hashing word N-grams into index bins and applying L2 normalization ($v_{\text{norm}} = v / \|v\|_2$). This preserves cosine distance metrics ($\cos(\theta) = \mathbf{a} \cdot \mathbf{b}$) and semantic relevance ranking during offline unit testing without external ML dependencies.

12. **Autonomous Social Video Agent & REST Pipeline Integration (DNK-VIDEO-006)**:
   - **Autonomous Video Creator Agent (`DnkVideoAiCreator`)**: Orchestrates footage metadata analysis, auto-cut cleaning, and viral hook score evaluation (`analyze_hook` evaluating `hook_score`, `insight_score`, `punchline_score`, `viral_potential`) to partition footage into vertical social shorts (`ShortVideo(footage_id, start, end, duration_sec, title, description)`).
   - **End-to-End Pipeline Integration (`run_pipeline.py`)**: Chains media ingestion (`POST /api/video/ingest`), chunked STT transcription (`POST /api/video/transcribe/{footage_id}`), silence/filler jumpcut generation (`POST /api/video/cut/{footage_id}`), and vector memory indexing (`FootageIndexer.index_footage`) into a unified workflow.
   - **FastAPI ASGI Test Harness**: Verify full multi-step video pipelines in async test suites without opening network sockets by configuring `httpx.ASGITransport(app=app)` with `httpx.AsyncClient(transport=transport, base_url="http://test")`.

13. **Docker Multi-Stage Build, Celery Task Worker & Production Rollout (DNK-STD-0086)**:
   - **Multi-Stage Build & Non-Root User**: Use 2-stage build (`builder` -> `runtime` based on `python:3.12-slim`) with pre-installed system binaries (`ffmpeg`, `ffprobe`, `libmagic1`). Run as non-privileged system user (`appuser` / `groupadd -r appuser`) to meet security compliance.
   - **Celery & Redis Worker Queue**: Offload CPU-intensive media processing, FFmpeg rendering, and Gemini transcription to Celery workers backed by Redis (`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`).
   - **Database Initialization & Vector Extension**: Automatically initialize `pgvector` extension via `init-db.sql` on database startup (`/docker-entrypoint-initdb.d/`). Provision `IVFFlat` vector distance indexes (`lists = 100`) and GIN metadata indexes.
   - **Container Orchestration & Health Checks**: Define multi-container setup (`docker-compose.yml` and `docker-compose.prod.yml`) coordinating `api`, `db`, `redis`, and `worker` services with health check scripts (`scripts/docker/healthcheck.sh`) and production resource limits (CPU/RAM).
   - For architecture, Dockerfile templates, and Celery setup details, see `references/docker-deployment-production-rollout.md`.

14. **Next.js 14 Web UI Dashboard, Reverse Proxy & Local Media Processing (DNK-STD-0092)**:
   - **Next.js Reverse Proxy (`app/api/proxy/[...path]/route.ts`)**: Route browser requests to backend (`http://api:8000`) dynamically while bypassing CORS and supporting multipart streaming (`duplex: 'half'`).
   - **Interactive 4-Stage Pipeline**: Front-end state machine coordinating Ingest (35%) -> Transcribe (70%) -> AutoCut (95%) -> Index (100%).
   - **High-Capacity Volume Mount (`/data/video_archive`)**: Mount host directories directly into containers for headless batch CLI processing on 1000+ GB archives without web upload bottlenecks.
   - For complete proxy code and setup instructions, see `references/nextjs-webui-media-dashboard.md`.

15. **Local System Launch, Health Verification & E2E Testing (DNK-VIDEO-009 / DNK-STD-0093)**:
   - **Environment Provisioning**: Maintain `.env.example` SSOT template for local runtime environment variables (`DB_USER`, `DB_PASSWORD`, `DATABASE_URL`, `REDIS_URL`, `GOOGLE_API_KEY`, `STORAGE_DIR`).
   - **Full Stack Container Orchestration**: Orchestrate 5 Docker services (`db`, `redis`, `api`, `worker`, `frontend`) via `docker-compose up -d --build` for complete offline e2e workflow testing.
   - **System Health Verification**: Execute `scripts/docker/healthcheck.sh` to validate DB, Redis, API `/health` endpoints, and Celery worker connectivity.
   - **Master Quality Gate**: Ensure `bash scripts/verify_all.sh` achieves 100% Green pass rate before certifying local release artifacts.

16. **GOP-Aligned Keyframe Video Ingestion & Distributed Chunking (DNK-MEDIA-002)**:
   - **GOP & Keyframe Boundary Precision**: Always split video segments strictly on I-frames (IDR keyframes) to ensure each chunk can be decoded, transcoded, and packaged independently without inter-frame decoding drift or boundary macroblocking artifacts.
   - **FFmpeg Zero-Drift Split Flags**: When slicing chunks with `-c copy`, always include `-avoid_negative_ts make_zero` alongside `-ss {start_time} -to {end_time}` to prevent negative presentation timestamps (PTS) and audio/video desynchronization.
   - **Chunk Continuity Validation**: Enforce continuous chunk interval invariants (`chunk[i].end_time == chunk[i+1].start_time` and `chunk[i].end_frame + 1 == chunk[i+1].start_frame`) with $\sum \text{chunk\_durations} = \text{total\_duration}$ before dispatching transcoding tasks to worker pools.

17. **Hardware Acceleration Auto-Detection & Distributed Transcoding Worker Pool (DNK-MEDIA-002 Phase 2)**:
   - **Multi-Backend HW Auto-Detection**: Probe available FFmpeg encoders via `ffmpeg -encoders` and map backend capabilities (`NVENC` -> `h264_nvenc`/`hevc_nvenc`/`av1_nvenc`, `VideoToolbox` -> `h264_videotoolbox`/`hevc_videotoolbox`, `VAAPI` -> `h264_vaapi`/`hevc_vaapi`/`vp9_vaapi`/`av1_vaapi`, `AMF` -> `h264_amf`/`hevc_amf`).
   - **Per-Codec Graceful Fallback**: If a target hardware backend does not support a specific codec (e.g. Apple VideoToolbox does not support VP9 or AV1), immediately fall back to optimized CPU encoders (`libvpx-vp9`, `libaom-av1`) with tuned speed flags (`-speed 4`, `-cpu-used 6`) rather than failing the transcoding job.
   - **ABR Ladder Matrix Generation**: Automatically expand incoming video chunk tasks into multi-bitrate/multi-resolution tuples (`1080p@4500k`, `720p@2500k`, `480p@1200k`, `360p@600k`) across target codecs (`H.264`, `H.265`, `VP9`, `AV1`).
   - **Distributed Task Dispatch & Health Watchdog**: Route chunk transcoding tasks to least-loaded active worker nodes with heartbeat timeouts, bounded concurrency (`concurrency_limit`), exponential backoff retries, and atomic progress percentage aggregation.

18. **HLS & MPEG-DASH Adaptive Bitrate Packaging, S3 Storage & Real-Time Pipeline (DNK-MEDIA-002 Phase 3)**:
   - **HLS Master & Variant Playlist Generation**: Build compliant HLS Master playlists (`master.m3u8`) with `#EXT-X-STREAM-INF` containing `BANDWIDTH`, `RESOLUTION`, `CODECS` (RFC 6381 strings like `avc1.640028`, `hvc1.1.6.L120.90`), and `FRAME-RATE`. Calculate total stream bandwidth with audio muxing overhead ($(\text{bitrate}_v + \text{bitrate}_a) \times 1.05$).
   - **MPEG-DASH XML MPD Generation**: Generate schema-compliant MPD manifests with dynamic `<Period>`, `<AdaptationSet mimeType="video/mp4">`, codec mapping (`vp09.00.41.08`, `av01.0.08M.08`), `<Representation>`, and `<SegmentTemplate>`.
   - **S3 & MinIO Storage Management**: Handle multi-part uploads, key hashing, TTL presigned PUT/GET URLs, and local mock filesystem fallbacks for offline test suites.
   - **FastAPI REST & WebSocket Orchestration**: Provide non-blocking endpoints for ingestion, chunk status polling, ABR packaging, worker node heartbeats, and real-time WebSocket progress broadcasts.
   - For architecture, GOP chunking specs, hardware fallback matrix, and packaging engine details, see `references/dnk-media-002-distributed-video-pipeline.md`.

19. **Generative AI Video Ingestion & Google Veo / Gemini Omni Integration**:
   - **Prompt-to-Video Engine**: Wrap Google Veo / Gemini Video Generation endpoints with deterministic task tracking (`job_id`), aspect ratio parameters (`16:9`, `9:16`, `1:1`), resolution specifications (`720p`, `1080p`), and frame duration clamps (`1..60s`).
   - **GCS Asset Ingestion & Storage**: Store raw AI-generated video outputs in Google Cloud Storage buckets with deterministic content hashing (`gs://<bucket>/videos/{hash}.mp4`) and generate signed URLs or local mock paths for canvas node consumption.
   - **Canvas Video Generation Node Integration**: Expose lightweight REST/JSON endpoints (`POST /api/v1/video/generate`) consumed by Infinite Canvas `VideoGenerationNode.tsx` with progress polling and direct download actions.

## ⚠️ Common Pitfalls

- **DASH Manifest XML Namespaces & ElementTree SubElement Ordering**: In Python's `xml.etree.ElementTree`, `ET.SubElement(parent, tag, ...)` requires `parent` as the first positional argument. Passing keyword arguments like `ET.SubElement(period=..., tag=...)` raises `TypeError: SubElement missing required argument 'parent'`. Always pass `parent` as the first positional argument.

- **HLS Audio/Video Composite Bandwidth Discrepancy**: Omitting the audio bitrate (e.g. 128 kbps) or encoding container overhead from the `#EXT-X-STREAM-INF:BANDWIDTH` tag leads to aggressive buffer underruns in player ABR algorithms (like Hls.js or ExoPlayer) on constrained mobile networks. Always factor in audio bitrate and a safety margin (e.g. $(\text{bitrate}_v + 128000) \times 1.05$).

- **Hardware Acceleration Codec Incompatibility & Crash**: Assuming a detected hardware acceleration framework supports all modern codecs (e.g. attempting to invoke `hevc_videotoolbox` on older Intel Macs or `vp9_videotoolbox`/`av1_videotoolbox` which are not supported by Apple VideoToolbox) causes FFmpeg to exit with error code 1 (`Unknown encoder`). **Fix**: Always verify per-codec availability via encoder probing and gracefully fall back to optimized CPU encoders (`libvpx-vp9`, `libaom-av1`) with appropriate speed presets.

- **FFmpeg Keyframe Boundary Drift & Negative PTS**: Slicing video chunks without `-avoid_negative_ts make_zero` or slicing on non-keyframe boundaries leads to negative presentation timestamps, frame stutter, and audio-video desynchronization. Always align chunk splits on IDR keyframes and apply `-avoid_negative_ts make_zero`.

- **SQLAlchemy Boolean Default Constructor Omission**: Defining `Column(Boolean, nullable=False, default=True)` only applies the default on database INSERT/flush, not when instantiating the model object directly in Python in-memory tests (`model = MediaWebhookConfigModel(...)`). Always pass `enabled=True` explicitly in test fixtures or define a default parameter in `__init__`.

- **Pytest `pyproject.toml` Rootdir Import Errors**: Running `pytest -c path/to/pyproject.toml` sets pytest `rootdir` to the directory containing `pyproject.toml`. If imports reference root-level directories (e.g., `import apps...`), pytest will raise `ModuleNotFoundError`. **Fix**: Ensure `pythonpath` in `pyproject.toml` includes `".."`, `"."`, and needed relative paths (e.g. `pythonpath = ["..", ".", "DNK OS", "apps/api"]`).

- **SQLAlchemy `metadata` Reserved Attribute Conflict**: Defining `metadata = relationship(...)` or `metadata = Column(...)` on a class inheriting from SQLAlchemy `DeclarativeBase` raises `AttributeError: Attribute name 'metadata' is reserved when using the Declarative API`. Always name the relationship/attribute `metadata_rel` or `footage_metadata`.

- **Cut Range Overlap Stutter in Auto-Cut Pipelines**: Merging raw filler word timestamps and pause segments without a merge threshold window (`merge_threshold_sec`) results in dozens of sub-100ms micro-edits and audio popping artifacts during FFmpeg render. Always pass raw cuts through a merge threshold filter (`generate_cut_ranges`) before computing keep ranges.

- **FastAPI `app.dependency_overrides` Scope Leaks in Multi-Module Test Suites**: Setting `app.dependency_overrides[get_db] = override_get_db` at the module level in one test file causes the override to leak globally across all subsequent test files in the `pytest` runner session. In test suites with isolated in-memory test databases (`test_engine`), this leads to `sqlite3.OperationalError: no such table` in sibling test files. **Fix**: Always set `app.dependency_overrides` inside a `pytest` fixture with `autouse=True` (or explicitly) and clear it during teardown (`app.dependency_overrides.clear()`).

- **Negative Frame Duration in Dynamic Clips**: When deriving element start or duration frames from total composition length (`total_frames - offset`), always clamp with `max(1, total_frames - offset)` so short render durations (e.g. 0.5s previews or unit tests) do not compute negative frame counts and fail Pydantic validation.

- **Non-deterministic Seeds**: Avoid unseeded random numbers during keyframe generation or chunk rendering.
- **Shell Injection Vulnerabilities**: Never format FFmpeg CLI strings for shell execution (`shell=True`). Always pass explicit string argument lists to `subprocess.run`.
- **Path Traversal Vulnerabilities**: Always validate `clip.src` before handing asset paths to sub-processes or Canvas decoders.
- **Float Frame Rounding**: Compute frame indices strictly as integers to prevent frame-skipping artifacts in FFmpeg stitching.
- **Unbounded RAM Consumption**: Avoid accumulating rendered RGBA Pillow `Image` objects in memory. Stream or write chunks to temporary disk paths and flush RAM between chunks.
- **SQLite In-Memory Test Isolation (`sqlite:///:memory:`)**: Standard `sqlite:///:memory:` creates a separate empty database per connection. When testing FastAPI endpoints or SQLAlchemy sessions, use `StaticPool` (`from sqlalchemy.pool import StaticPool` with `poolclass=StaticPool`) to share a single in-memory database instance across sessions.
- **Unimported Model Registrations**: Failing to import SQLAlchemy model files before `Base.metadata.create_all()` results in `sqlite3.OperationalError: no such table` errors because SQLAlchemy metadata is unaware of unimported model classes.
