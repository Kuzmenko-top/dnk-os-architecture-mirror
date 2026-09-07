# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/batch_coordinator_service.py"
# purpose: "Distributed Batch Coordinator, Worker Watchdog, Schedule Evaluator & DLQ Manager (DNK-BATCH-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from apps.api.db.models.batch_job import BatchJob, BatchJobStatus
from apps.api.db.models.batch_task import BatchTask, BatchTaskStatus
from apps.api.db.models.batch_worker_node import BatchWorkerNode, WorkerStatus
from apps.api.db.models.batch_schedule_rule import BatchScheduleRule
from apps.api.db.models.batch_dead_letter_record import BatchDeadLetterRecord, DLQStatus
from apps.api.services.batch_engine_service import BatchEngineService, get_default_batch_engine

logger = logging.getLogger("dnk.batch_coordinator")


class BatchCoordinatorService:
    """Coordinator service managing worker heartbeats, task re-balancing on node failure, and schedule ticks."""

    def __init__(
        self,
        engine: Optional[BatchEngineService] = None,
        heartbeat_timeout_seconds: float = 10.0,
        base_retry_backoff_seconds: float = 1.0,
        max_retry_backoff_seconds: float = 60.0,
    ):
        self.engine = engine or get_default_batch_engine()
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self.base_retry_backoff_seconds = base_retry_backoff_seconds
        self.max_retry_backoff_seconds = max_retry_backoff_seconds

    # -------------------------------------------------------------------------
    # Exponential Backoff Calculation
    # -------------------------------------------------------------------------
    def compute_backoff_delay(self, retry_count: int, jitter: bool = True) -> float:
        """Calculates exponential backoff delay with optional random jitter."""
        delay = min(self.max_retry_backoff_seconds, self.base_retry_backoff_seconds * (2 ** max(0, retry_count - 1)))
        if jitter:
            delay = delay * (0.8 + 0.4 * random.random())
        return round(delay, 2)

    # -------------------------------------------------------------------------
    # Worker Health Watchdog & Auto-Rebalancing
    # -------------------------------------------------------------------------
    async def run_worker_health_check(self) -> Dict[str, Any]:
        """Detects dead workers, marks them OFFLINE, and re-queues orphaned tasks."""
        async with self.engine._lock:
            now = datetime.now(timezone.utc)
            dead_workers: List[str] = []
            requeued_tasks: List[str] = []

            for worker_id, worker in self.engine._workers.items():
                if worker.status != WorkerStatus.OFFLINE and not worker.is_alive(timeout_seconds=self.heartbeat_timeout_seconds):
                    worker.status = WorkerStatus.OFFLINE
                    dead_workers.append(worker_id)
                    logger.warning("Worker %s timed out. Marked OFFLINE.", worker_id)

                    # Re-queue orphaned tasks assigned to this worker
                    for task_id in list(worker.current_task_ids):
                        task = self.engine._tasks.get(task_id)
                        if task and task.status == BatchTaskStatus.RUNNING:
                            task.status = BatchTaskStatus.QUEUED
                            task.assigned_worker_id = None
                            requeued_tasks.append(task.id)
                            logger.info("Requeued orphaned task %s from failed worker %s", task.id, worker_id)
                    worker.current_task_ids.clear()
                    worker.active_tasks_count = 0

            return {
                "checked_at": now.isoformat(),
                "dead_workers_detected": dead_workers,
                "requeued_tasks_count": len(requeued_tasks),
                "requeued_tasks": requeued_tasks,
            }

    # -------------------------------------------------------------------------
    # Schedule Rules Engine
    # -------------------------------------------------------------------------
    async def register_schedule(
        self,
        name: str,
        job_template_name: str,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        payload_template: Optional[Dict[str, Any]] = None,
    ) -> BatchScheduleRule:
        """Registers a recurring batch schedule rule."""
        async with self.engine._lock:
            rule = BatchScheduleRule(
                name=name,
                job_template_name=job_template_name,
                interval_seconds=interval_seconds,
                cron_expression=cron_expression,
                payload_template=payload_template or {},
                tenant_id=self.engine.tenant_id,
            )
            self.engine._schedules[rule.id] = rule
            return rule

    async def evaluate_schedules(self) -> List[BatchJob]:
        """Evaluates enabled schedule rules and triggers due batch jobs."""
        triggered_jobs: List[BatchJob] = []
        now = datetime.now(timezone.utc)

        async with self.engine._lock:
            for rule in self.engine._schedules.values():
                if not rule.is_active:
                    continue

                is_due = False
                if rule.interval_seconds:
                    if not rule.last_triggered_at or (now - rule.last_triggered_at).total_seconds() >= rule.interval_seconds:
                        is_due = True
                elif rule.cron_expression:
                    # Simulation: trigger if interval >= 60s
                    if not rule.last_triggered_at or (now - rule.last_triggered_at).total_seconds() >= 60:
                        is_due = True

                if is_due:
                    rule.mark_triggered()

                    # Submit job
                    job = BatchJob(
                        name=f"Scheduled: {rule.name}",
                        tenant_id=rule.tenant_id,
                        payload=rule.payload_template,
                    )
                    self.engine._jobs[job.id] = job

                    # Create default task
                    task = BatchTask(
                        job_id=job.id,
                        name=f"{rule.name}_task",
                        task_type=rule.job_template_name,
                        payload=rule.payload_template,
                        tenant_id=rule.tenant_id,
                    )
                    self.engine._tasks[task.id] = task
                    job.total_tasks = 1
                    triggered_jobs.append(job)

        return triggered_jobs

    # -------------------------------------------------------------------------
    # DLQ Resolution & Purge
    # -------------------------------------------------------------------------
    async def discard_dlq_record(self, dlq_id: str) -> Optional[BatchDeadLetterRecord]:
        """Marks a DLQ record as discarded."""
        async with self.engine._lock:
            record = self.engine._dlq.get(dlq_id)
            if not record:
                return None
            record.mark_discarded()
            return record

    async def purge_resolved_dlq(self) -> int:
        """Purges discarded and replayed DLQ records."""
        async with self.engine._lock:
            initial_count = len(self.engine._dlq)
            self.engine._dlq = {
                k: v for k, v in self.engine._dlq.items()
                if v.status == DLQStatus.UNRESOLVED
            }
            purged = initial_count - len(self.engine._dlq)
            return purged
