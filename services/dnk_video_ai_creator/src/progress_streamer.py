# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/progress_streamer.py"
# purpose: "Real-time Asynchronous Progress Streamer for DNK-MEDIA-001 (Phase 4)."
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
Progress Streamer for dnk_video_ai_creator.
Provides real-time event broadcasting, progress tracking (0-100%), ETA calculation,
and SSE/Async event streaming.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from enum import Enum
from typing import AsyncGenerator, Dict, List, Optional, Set


class RenderStage(str, Enum):
    """Lifecycle stages for video rendering jobs."""
    QUEUED = "queued"
    INITIALIZING = "initializing"
    RENDERING_FRAMES = "rendering_frames"
    ENCODING_VIDEO = "encoding_video"
    UPLOADING_CDN = "uploading_cdn"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressEvent:
    """Encapsulates a single progress event for a render job."""
    job_id: str
    stage: RenderStage
    progress_pct: float
    current_frame: int = 0
    total_frames: int = 0
    fps: float = 30.0
    message: str = ""
    eta_seconds: Optional[float] = None
    output_url: Optional[str] = None
    cdn_url: Optional[str] = None
    error: Optional[str] = None
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        self.progress_pct = max(0.0, min(100.0, round(self.progress_pct, 2)))

    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary with stringified enum."""
        data = asdict(self)
        data["stage"] = self.stage.value if isinstance(self.stage, RenderStage) else str(self.stage)
        return data


class ProgressStreamer:
    """
    Centralized asynchronous progress tracker & event broadcaster for media render jobs.
    Supports pub/sub subscriptions for Server-Sent Events (SSE) and WebSocket dispatch.
    """

    def __init__(self) -> None:
        self._listeners: Dict[str, Set[asyncio.Queue[ProgressEvent]]] = defaultdict(set)
        self._latest_events: Dict[str, ProgressEvent] = {}
        self._event_history: Dict[str, List[ProgressEvent]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def emit(
        self,
        job_id: str,
        stage: RenderStage | str,
        progress_pct: float,
        current_frame: int = 0,
        total_frames: int = 0,
        fps: float = 30.0,
        message: str = "",
        eta_seconds: Optional[float] = None,
        output_url: Optional[str] = None,
        cdn_url: Optional[str] = None,
        error: Optional[str] = None,
    ) -> ProgressEvent:
        """
        Emit a progress event for a job and broadcast to all active subscribers.
        """
        if isinstance(stage, str):
            stage = RenderStage(stage)

        event = ProgressEvent(
            job_id=job_id,
            stage=stage,
            progress_pct=progress_pct,
            current_frame=current_frame,
            total_frames=total_frames,
            fps=fps,
            message=message,
            eta_seconds=eta_seconds,
            output_url=output_url,
            cdn_url=cdn_url,
            error=error,
            timestamp=time.time(),
        )

        async with self._lock:
            self._latest_events[job_id] = event
            self._event_history[job_id].append(event)
            queues = list(self._listeners.get(job_id, set()))

        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

        return event

    def get_latest(self, job_id: str) -> Optional[ProgressEvent]:
        """Get the most recent progress event for a given job."""
        return self._latest_events.get(job_id)

    def get_history(self, job_id: str) -> List[ProgressEvent]:
        """Get all emitted progress events for a given job."""
        return list(self._event_history.get(job_id, []))

    async def subscribe(self, job_id: str, max_queue_size: int = 100) -> asyncio.Queue[ProgressEvent]:
        """
        Subscribe to progress events for a specific job_id.

        Returns:
            asyncio.Queue yielding ProgressEvents in real time.
        """
        q: asyncio.Queue[ProgressEvent] = asyncio.Queue(maxsize=max_queue_size)
        async with self._lock:
            self._listeners[job_id].add(q)
            # Push latest event immediately if available
            if job_id in self._latest_events:
                q.put_nowait(self._latest_events[job_id])
        return q

    async def unsubscribe(self, job_id: str, queue: asyncio.Queue[ProgressEvent]) -> None:
        """Unregister a listener queue."""
        async with self._lock:
            if job_id in self._listeners and queue in self._listeners[job_id]:
                self._listeners[job_id].remove(queue)
                if not self._listeners[job_id]:
                    del self._listeners[job_id]

    async def stream(
        self,
        job_id: str,
        timeout_seconds: float = 600.0,
    ) -> AsyncGenerator[ProgressEvent, None]:
        """
        Asynchronous generator streaming events for a job until completion, failure, or timeout.
        """
        q = await self.subscribe(job_id)
        start_time = time.time()
        try:
            while True:
                remaining_time = timeout_seconds - (time.time() - start_time)
                if remaining_time <= 0:
                    break

                try:
                    event = await asyncio.wait_for(q.get(), timeout=min(5.0, remaining_time))
                    yield event
                    if event.stage in (RenderStage.COMPLETED, RenderStage.FAILED, RenderStage.CANCELLED):
                        break
                except asyncio.TimeoutError:
                    # Check if latest status is terminal
                    latest = self.get_latest(job_id)
                    if latest and latest.stage in (RenderStage.COMPLETED, RenderStage.FAILED, RenderStage.CANCELLED):
                        yield latest
                        break
        finally:
            await self.unsubscribe(job_id, q)


    async def stream_sse(self, job_id: str, timeout_seconds: float = 300.0) -> AsyncGenerator[str, None]:
        """
        Stream events as Server-Sent Events (SSE) formatted text.
        """
        async for event in self.stream(job_id, timeout_seconds=timeout_seconds):
            data_json = json.dumps(event.to_dict())
            yield f"event: progress\ndata: {data_json}\n\n"


# Global default progress streamer instance
default_progress_streamer = ProgressStreamer()


def get_default_progress_streamer() -> ProgressStreamer:
    """Get the default global ProgressStreamer instance."""
    global default_progress_streamer
    return default_progress_streamer
