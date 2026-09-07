# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/job_queue.py"
# purpose: "Asynchronous Media Rendering Job Queue & Background Worker for DNK-MEDIA-001 (Phase 4)."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

"""
Asynchronous Job Queue & Background Task Orchestrator for dnk_video_ai_creator.
Manages non-blocking render submissions, progress tracking, asset caching,
and multi-worker rendering.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cache_manager import CacheManager
from .ffmpeg_orchestrator import FFmpegOrchestrator
from .headless_renderer import HeadlessRenderer
from .progress_streamer import ProgressStreamer, RenderStage, default_progress_streamer
from .template_registry import TemplateRegistry, default_registry
from .video_composition_schema import VideoCompositionSchema


class JobType(str, Enum):
    """Types of media jobs."""
    RENDER = "render"
    PREVIEW = "preview"


class JobStatus(str, Enum):
    """Status states for jobs in queue."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class MediaJob:
    """Encapsulates a media generation/rendering job."""
    job_id: str
    job_type: JobType
    template_id: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    composition: Optional[VideoCompositionSchema] = None
    status: JobStatus = JobStatus.QUEUED
    progress_pct: float = 0.0
    stage: RenderStage = RenderStage.QUEUED
    output_path: Optional[str] = None
    cdn_url: Optional[str] = None
    preview_format: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    use_cache: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to serialized dictionary."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type.value,
            "template_id": self.template_id,
            "params": self.params,
            "status": self.status.value,
            "progress_pct": self.progress_pct,
            "stage": self.stage.value,
            "output_path": self.output_path,
            "cdn_url": self.cdn_url,
            "preview_format": self.preview_format,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "use_cache": self.use_cache,
            "metadata": self.metadata,
        }


class MediaJobQueue:
    """
    Asynchronous Worker Queue for executing media composition renders and preview generation.
    Supports concurrency throttling, cache hits, and real-time event streaming.
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        progress_streamer: Optional[ProgressStreamer] = None,
        template_registry: Optional[TemplateRegistry] = None,
        max_concurrency: int = 4,
        output_dir: str = "./output/media",
    ) -> None:
        self.cache_manager = cache_manager or CacheManager()
        self.progress_streamer = progress_streamer or default_progress_streamer
        self.template_registry = template_registry or default_registry
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._jobs: Dict[str, MediaJob] = {}
        self._async_queue: asyncio.Queue[str] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._workers: List[asyncio.Task[None]] = []
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self, num_workers: int = 2) -> None:
        """Start background worker tasks."""
        if self._running:
            return
        self._running = True
        for i in range(num_workers):
            task = asyncio.create_task(self._worker_loop(i), name=f"media_worker_{i}")
            self._workers.append(task)

    async def stop(self) -> None:
        """Stop background worker tasks gracefully."""
        self._running = False
        for task in self._workers:
            task.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def submit_render_job(
        self,
        template_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        composition: Optional[VideoCompositionSchema] = None,
        use_cache: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MediaJob:
        """
        Submit a new video rendering job to the queue.
        Returns immediately with a QUEUED MediaJob.
        """
        if not template_id and not composition:
            raise ValueError("Either template_id or composition must be provided.")

        job_id = f"render_{uuid.uuid4().hex[:12]}"
        job = MediaJob(
            job_id=job_id,
            job_type=JobType.RENDER,
            template_id=template_id,
            params=params or {},
            composition=composition,
            use_cache=use_cache,
            metadata=metadata or {},
        )

        if not self._running:
            await self.start()

        async with self._lock:
            self._jobs[job_id] = job

        await self.progress_streamer.emit(
            job_id=job_id,
            stage=RenderStage.QUEUED,
            progress_pct=0.0,
            message="Job queued for processing",
        )

        await self._async_queue.put(job_id)
        return job

    async def submit_preview_job(
        self,
        template_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        composition: Optional[VideoCompositionSchema] = None,
        preview_format: str = "gif",
        use_cache: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MediaJob:
        """
        Submit a preview generation job (GIF or lightweight MP4).
        """
        if not template_id and not composition:
            raise ValueError("Either template_id or composition must be provided.")

        job_id = f"prev_{uuid.uuid4().hex[:12]}"
        job = MediaJob(
            job_id=job_id,
            job_type=JobType.PREVIEW,
            template_id=template_id,
            params=params or {},
            composition=composition,
            preview_format=preview_format.lower(),
            use_cache=use_cache,
            metadata=metadata or {},
        )

        if not self._running:
            await self.start()

        async with self._lock:
            self._jobs[job_id] = job

        await self.progress_streamer.emit(
            job_id=job_id,
            stage=RenderStage.QUEUED,
            progress_pct=0.0,
            message="Preview job queued for processing",
        )

        await self._async_queue.put(job_id)
        return job

    def get_job(self, job_id: str) -> Optional[MediaJob]:
        """Look up a job by its unique ID."""
        return self._jobs.get(job_id)

    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 50) -> List[MediaJob]:
        """List jobs filtered optionally by status."""
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job."""
        job = self._jobs.get(job_id)
        if not job:
            return False
        if job.status == JobStatus.QUEUED:
            job.status = JobStatus.CANCELLED
            job.stage = RenderStage.CANCELLED
            await self.progress_streamer.emit(
                job_id=job_id,
                stage=RenderStage.CANCELLED,
                progress_pct=job.progress_pct,
                message="Job was cancelled by user",
            )
            return True
        return False

    async def _worker_loop(self, worker_id: int) -> None:
        """Internal background worker loop."""
        while self._running:
            try:
                job_id = await self._async_queue.get()
                job = self._jobs.get(job_id)
                if not job or job.status == JobStatus.CANCELLED:
                    self._async_queue.task_done()
                    continue

                async with self._semaphore:
                    await self._process_job(job)

                self._async_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.5)

    async def process_job_now(self, job_id: str) -> MediaJob:
        """Synchronously/directly process a job in the current async context (useful for testing/direct calls)."""
        job = self._jobs.get(job_id)
        if not job:
            raise KeyError(f"Job {job_id} not found.")
        await self._process_job(job)
        return job

    async def _process_job(self, job: MediaJob) -> None:
        """Process a single render or preview job."""
        job.status = JobStatus.PROCESSING
        job.started_at = time.time()
        job.stage = RenderStage.INITIALIZING

        await self.progress_streamer.emit(
            job_id=job.job_id,
            stage=RenderStage.INITIALIZING,
            progress_pct=5.0,
            message="Initializing rendering pipeline",
        )

        temp_workdir = None
        try:
            # Step 1: Build / Validate Composition
            comp: VideoCompositionSchema
            if job.composition:
                comp = job.composition
            elif job.template_id:
                comp = self.template_registry.create_composition(job.template_id, job.params)
            else:
                raise ValueError("No composition or template provided.")

            duration_sec = comp.duration_frames / comp.fps

            # Step 2: Cache check
            extension = "gif" if (job.job_type == JobType.PREVIEW and job.preview_format == "gif") else "mp4"
            cache_payload = {
                "comp": comp.model_dump(),
                "job_type": job.job_type.value,
                "preview_format": job.preview_format,
            }
            cache_key = self.cache_manager.compute_key(cache_payload)

            if job.use_cache:
                cached_entry = self.cache_manager.get(cache_key, extension=extension)
                if cached_entry:
                    job.output_path = cached_entry.file_path
                    job.cdn_url = cached_entry.cdn_url
                    job.status = JobStatus.COMPLETED
                    job.stage = RenderStage.COMPLETED
                    job.progress_pct = 100.0
                    job.completed_at = time.time()
                    await self.progress_streamer.emit(
                        job_id=job.job_id,
                        stage=RenderStage.COMPLETED,
                        progress_pct=100.0,
                        output_url=job.output_path,
                        cdn_url=job.cdn_url,
                        message="Completed (Cache Hit)",
                    )
                    return

            # Step 3: Rendering Pipeline
            temp_workdir = tempfile.mkdtemp(prefix=f"render_{job.job_id}_")
            final_output_file = Path(temp_workdir) / f"output.{extension}"

            if extension == "gif":
                # GIF preview path
                frames_dir = Path(temp_workdir) / "frames"
                frames_dir.mkdir(parents=True, exist_ok=True)
                max_frames = min(comp.duration_frames, int(comp.fps * 2))

                renderer = HeadlessRenderer(comp)
                rendered_images = []
                for frame_idx in range(max_frames):
                    img = renderer.render_frame(frame_idx)
                    rendered_images.append(img.convert("RGB"))
                    if frame_idx % max(1, max_frames // 5) == 0:
                        pct = 10.0 + ((frame_idx + 1) / max_frames) * 70.0
                        await self.progress_streamer.emit(
                            job_id=job.job_id,
                            stage=RenderStage.RENDERING_FRAMES,
                            progress_pct=pct,
                            current_frame=frame_idx + 1,
                            total_frames=max_frames,
                            fps=comp.fps,
                            message=f"Rendering preview frames ({frame_idx + 1}/{max_frames})",
                        )
                        await asyncio.sleep(0)

                duration_ms = int(1000 / comp.fps)
                rendered_images[0].save(
                    final_output_file,
                    save_all=True,
                    append_images=rendered_images[1:],
                    optimize=True,
                    duration=duration_ms,
                    loop=0,
                )
            else:
                # Full MP4 video path via FFmpeg Orchestrator
                orchestrator = FFmpegOrchestrator()
                await self.progress_streamer.emit(
                    job_id=job.job_id,
                    stage=RenderStage.RENDERING_FRAMES,
                    progress_pct=30.0,
                    message="Orchestrating video rendering chunks",
                )

                render_res = orchestrator.render_composition(
                    composition=comp,
                    output_file=final_output_file,
                )
                if not render_res.success:
                    raise RuntimeError(f"FFmpeg encoding failed: {render_res.error_message}")

            # Step 4: Cache & CDN Storage
            job.stage = RenderStage.UPLOADING_CDN
            await self.progress_streamer.emit(
                job_id=job.job_id,
                stage=RenderStage.UPLOADING_CDN,
                progress_pct=90.0,
                message="Finalizing asset and caching",
            )

            cache_entry = self.cache_manager.put(
                key=cache_key,
                source_file_path=final_output_file,
                extension=extension,
                metadata={
                    "job_id": job.job_id,
                    "template_id": job.template_id,
                    "duration_seconds": duration_sec,
                    "width": comp.width,
                    "height": comp.height,
                    "fps": comp.fps,
                },
            )

            job.output_path = cache_entry.file_path
            job.cdn_url = cache_entry.cdn_url
            job.status = JobStatus.COMPLETED
            job.stage = RenderStage.COMPLETED
            job.progress_pct = 100.0
            job.completed_at = time.time()

            await self.progress_streamer.emit(
                job_id=job.job_id,
                stage=RenderStage.COMPLETED,
                progress_pct=100.0,
                output_url=job.output_path,
                cdn_url=job.cdn_url,
                message="Video rendered successfully",
            )

        except Exception as e:
            job.status = JobStatus.FAILED
            job.stage = RenderStage.FAILED
            job.error = str(e)
            job.completed_at = time.time()
            await self.progress_streamer.emit(
                job_id=job.job_id,
                stage=RenderStage.FAILED,
                progress_pct=job.progress_pct,
                error=str(e),
                message=f"Rendering failed: {str(e)}",
            )
        finally:
            if temp_workdir and os.path.exists(temp_workdir):
                shutil.rmtree(temp_workdir, ignore_errors=True)


# Global default job queue instance
default_job_queue = MediaJobQueue()


def get_default_job_queue() -> MediaJobQueue:
    """Get the default global MediaJobQueue instance."""
    global default_job_queue
    return default_job_queue
