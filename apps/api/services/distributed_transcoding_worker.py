# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_distributed_transcoding_worker"
# purpose: "Distributed Transcoding Worker Pool & Task Orchestration Engine (DNK-MEDIA-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum

from apps.api.services.hardware_acceleration_manager import (
    HardwareAccelerationManager,
    HardwareAccelType,
    VideoCodec,
    EncoderProfile,
    hardware_acceleration_manager,
)
from apps.api.services.video_chunking_engine import VideoChunkSpec, ChunkingPlan

logger = logging.getLogger("dnk.media.worker_pool")


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class ABRProfileSpec:
    resolution_name: str
    width: int
    height: int
    bitrate_kbps: int
    fps: float = 30.0
    audio_bitrate_kbps: int = 128


STANDARD_ABR_LADDER: List[ABRProfileSpec] = [
    ABRProfileSpec("1080p", 1920, 1080, 4500, 30.0, 192),
    ABRProfileSpec("720p", 1280, 720, 2500, 30.0, 128),
    ABRProfileSpec("480p", 854, 480, 1200, 30.0, 96),
    ABRProfileSpec("360p", 640, 360, 600, 30.0, 64),
]


@dataclass
class ChunkTranscodeTask:
    task_id: str
    job_id: str
    chunk_index: int
    input_chunk_path: str
    output_chunk_path: str
    codec: VideoCodec
    abr_profile: ABRProfileSpec
    status: TaskStatus = TaskStatus.PENDING
    assigned_worker_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    transcode_duration_ms: float = 0.0
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    ffmpeg_command: List[str] = field(default_factory=list)


@dataclass
class WorkerNodeInfo:
    worker_id: str
    hostname: str
    hardware_accel: HardwareAccelType
    concurrency_limit: int = 4
    active_tasks: int = 0
    total_processed: int = 0
    total_failed: int = 0
    last_heartbeat: float = field(default_factory=time.time)
    is_active: bool = True


class DistributedTranscodingWorkerPool:
    """
    High-throughput distributed transcoding orchestrator.
    Manages worker dispatch, task queuing (Redis Streams style), progress tracking,
    hardware acceleration routing, and automatic error self-healing/retries.
    """

    def __init__(
        self,
        accel_mgr: Optional[HardwareAccelerationManager] = None,
        max_retries: int = 3,
    ):
        self.accel_mgr = accel_mgr or hardware_acceleration_manager
        self.max_retries = max_retries
        self.workers: Dict[str, WorkerNodeInfo] = {}
        self.tasks: Dict[str, ChunkTranscodeTask] = {}
        self.task_queue: List[str] = []  # Task IDs pending dispatch
        self.job_progress: Dict[str, Dict[str, Any]] = {}

    def register_worker(
        self,
        worker_id: str,
        hostname: str,
        hardware_accel: Optional[HardwareAccelType] = None,
        concurrency_limit: int = 4,
    ) -> WorkerNodeInfo:
        """Registers a transcoding worker node in the active pool."""
        accel = hardware_accel or self.accel_mgr.detect_best_hardware_acceleration()
        worker = WorkerNodeInfo(
            worker_id=worker_id,
            hostname=hostname,
            hardware_accel=accel,
            concurrency_limit=concurrency_limit,
        )
        self.workers[worker_id] = worker
        logger.info(f"Worker {worker_id} ({hostname}) registered with accel={accel.value}")
        return worker

    def unregister_worker(self, worker_id: str) -> None:
        """Removes a worker node from the pool and re-queues active tasks."""
        if worker_id in self.workers:
            self.workers[worker_id].is_active = False
            # Requeue active tasks
            for task in self.tasks.values():
                if task.assigned_worker_id == worker_id and task.status == TaskStatus.PROCESSING:
                    task.status = TaskStatus.PENDING
                    task.assigned_worker_id = None
                    self.task_queue.insert(0, task.task_id)

    def heartbeat(self, worker_id: str) -> bool:
        """Updates worker heartbeat timestamp."""
        if worker_id in self.workers:
            self.workers[worker_id].last_heartbeat = time.time()
            return True
        return False

    def generate_job_transcode_tasks(
        self,
        job_id: str,
        chunking_plan: ChunkingPlan,
        codecs: Optional[List[VideoCodec]] = None,
        abr_ladder: Optional[List[ABRProfileSpec]] = None,
        output_base_dir: str = "/tmp/transcoded_chunks",
    ) -> List[ChunkTranscodeTask]:
        """
        Generates individual transcode tasks for all chunks across all target codecs and ABR profiles.
        """
        target_codecs = codecs or [VideoCodec.H264]
        target_ladder = abr_ladder or STANDARD_ABR_LADDER
        created_tasks: List[ChunkTranscodeTask] = []

        for chunk in chunking_plan.chunks:
            for codec in target_codecs:
                for abr in target_ladder:
                    task_id = f"task_{job_id}_{chunk.chunk_index:04d}_{codec.value}_{abr.resolution_name}"
                    out_path = (
                        f"{output_base_dir}/{job_id}/{codec.value}/{abr.resolution_name}/"
                        f"chunk_{chunk.chunk_index:04d}.mp4"
                    )

                    # Build FFmpeg command for the chunk
                    profile = self.accel_mgr.get_encoder_profile(
                        codec=codec,
                        target_bitrate_kbps=abr.bitrate_kbps,
                        target_fps=abr.fps,
                    )
                    cmd = self.accel_mgr.build_transcode_command(
                        input_chunk_path=chunk.output_chunk_path,
                        output_chunk_path=out_path,
                        profile=profile,
                        target_width=abr.width,
                        target_height=abr.height,
                    )

                    task = ChunkTranscodeTask(
                        task_id=task_id,
                        job_id=job_id,
                        chunk_index=chunk.chunk_index,
                        input_chunk_path=chunk.output_chunk_path,
                        output_chunk_path=out_path,
                        codec=codec,
                        abr_profile=abr,
                        ffmpeg_command=cmd,
                        max_retries=self.max_retries,
                    )

                    self.tasks[task_id] = task
                    self.task_queue.append(task_id)
                    created_tasks.append(task)

        # Initialize job progress record
        self.job_progress[job_id] = {
            "total_tasks": len(created_tasks),
            "completed_tasks": 0,
            "failed_tasks": 0,
            "progress_percent": 0.0,
            "status": "in_progress",
        }

        return created_tasks

    def schedule_next_tasks(self) -> List[Tuple[WorkerNodeInfo, ChunkTranscodeTask]]:
        """
        Dispatches pending tasks to available worker nodes based on capacity and hardware capability.
        """
        assignments: List[Tuple[WorkerNodeInfo, ChunkTranscodeTask]] = []
        if not self.task_queue:
            return assignments

        # Active workers with remaining capacity
        available_workers = [
            w for w in self.workers.values()
            if w.is_active and (w.concurrency_limit - w.active_tasks) > 0
        ]

        if not available_workers:
            return assignments

        # Sort workers by least active load
        available_workers.sort(key=lambda w: w.active_tasks)

        remaining_queue: List[str] = []
        for task_id in self.task_queue:
            task = self.tasks.get(task_id)
            if not task or task.status not in (TaskStatus.PENDING, TaskStatus.RETRYING):
                continue

            assigned = False
            for worker in available_workers:
                if worker.active_tasks < worker.concurrency_limit:
                    task.status = TaskStatus.PROCESSING
                    task.assigned_worker_id = worker.worker_id
                    worker.active_tasks += 1
                    assignments.append((worker, task))
                    assigned = True
                    break

            if not assigned:
                remaining_queue.append(task_id)

        self.task_queue = remaining_queue
        return assignments

    def complete_task(
        self,
        task_id: str,
        duration_ms: float = 100.0,
    ) -> bool:
        """Records task completion and updates job progress."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        task.transcode_duration_ms = duration_ms

        if task.assigned_worker_id and task.assigned_worker_id in self.workers:
            worker = self.workers[task.assigned_worker_id]
            worker.active_tasks = max(0, worker.active_tasks - 1)
            worker.total_processed += 1

        # Update job progress
        self._update_job_progress(task.job_id)
        return True

    def fail_task(
        self,
        task_id: str,
        error_message: str,
    ) -> bool:
        """Handles task failure, applies retry logic or marks permanently failed."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.error_message = error_message
        if task.assigned_worker_id and task.assigned_worker_id in self.workers:
            worker = self.workers[task.assigned_worker_id]
            worker.active_tasks = max(0, worker.active_tasks - 1)
            worker.total_failed += 1

        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.RETRYING
            task.assigned_worker_id = None
            self.task_queue.append(task_id)
            logger.warning(f"Retrying task {task_id} (attempt {task.retry_count}/{task.max_retries})")
        else:
            task.status = TaskStatus.FAILED
            logger.error(f"Task {task_id} failed permanently: {error_message}")

        self._update_job_progress(task.job_id)
        return True

    def _update_job_progress(self, job_id: str) -> None:
        """Calculates aggregated progress percentage for a video job."""
        if job_id not in self.job_progress:
            return

        job_tasks = [t for t in self.tasks.values() if t.job_id == job_id]
        if not job_tasks:
            return

        total = len(job_tasks)
        completed = sum(1 for t in job_tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in job_tasks if t.status == TaskStatus.FAILED)

        percent = round((completed / total) * 100.0, 2)
        status = "in_progress"
        if completed == total:
            status = "completed"
        elif failed > 0 and (completed + failed) == total:
            status = "failed"

        self.job_progress[job_id] = {
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "progress_percent": percent,
            "status": status,
        }

    def get_job_progress(self, job_id: str) -> Dict[str, Any]:
        """Returns the real-time progress metrics for a job."""
        return self.job_progress.get(
            job_id,
            {"total_tasks": 0, "completed_tasks": 0, "failed_tasks": 0, "progress_percent": 0.0, "status": "unknown"}
        )


distributed_transcoding_worker_pool = DistributedTranscodingWorkerPool()
