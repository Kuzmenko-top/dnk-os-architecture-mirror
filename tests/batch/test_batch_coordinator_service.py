# --- DNK-MRH-HEADER ---
# mrh_id: "tests/batch/test_batch_coordinator_service.py"
# purpose: "Unit tests for DNK-BATCH-001 Batch Coordinator, Watchdog, Exponential Backoff & DLQ Purge."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from apps.api.db.models.batch_task import BatchTask, BatchTaskStatus
from apps.api.db.models.batch_worker_node import BatchWorkerNode, WorkerStatus
from apps.api.db.models.batch_dead_letter_record import BatchDeadLetterRecord, DLQStatus
from apps.api.services.batch_engine_service import BatchEngineService
from apps.api.services.batch_coordinator_service import BatchCoordinatorService


@pytest.mark.asyncio
class TestBatchCoordinatorService:
    async def test_exponential_backoff_calculation(self):
        coord = BatchCoordinatorService(base_retry_backoff_seconds=1.0, max_retry_backoff_seconds=30.0)
        
        # Retry 1
        delay1 = coord.compute_backoff_delay(1, jitter=False)
        assert delay1 == 1.0

        # Retry 2
        delay2 = coord.compute_backoff_delay(2, jitter=False)
        assert delay2 == 2.0

        # Retry 4
        delay4 = coord.compute_backoff_delay(4, jitter=False)
        assert delay4 == 8.0

        # Max cap
        delay_large = coord.compute_backoff_delay(10, jitter=False)
        assert delay_large == 30.0

    async def test_worker_health_watchdog_and_task_requeuing(self):
        engine = BatchEngineService(tenant_id="test-ws")
        coord = BatchCoordinatorService(engine=engine, heartbeat_timeout_seconds=0.1)

        # Register worker
        worker = await engine.register_worker(hostname="failing-node", concurrency_slots=2)
        
        # Create a task assigned to this worker
        job = await engine.submit_job(name="Test Job")
        task = BatchTask(
            job_id=job.id,
            name="orphaned_task",
            status=BatchTaskStatus.RUNNING,
            assigned_worker_id=worker.id,
            tenant_id="test-ws",
        )
        engine._tasks[task.id] = task
        worker.current_task_ids.append(task.id)
        worker.active_tasks_count = 1

        # Simulate heartbeat timeout
        worker.last_heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=1)

        # Run watchdog check
        report = await coord.run_worker_health_check()
        assert worker.id in report["dead_workers_detected"]
        assert worker.status == WorkerStatus.OFFLINE
        assert task.id in report["requeued_tasks"]
        assert task.status == BatchTaskStatus.QUEUED
        assert task.assigned_worker_id is None

    async def test_schedule_evaluation_and_trigger(self):
        engine = BatchEngineService(tenant_id="test-ws")
        coord = BatchCoordinatorService(engine=engine)

        rule = await coord.register_schedule(
            name="Hourly Aggregation",
            job_template_name="generic_compute",
            interval_seconds=10,
            payload_template={"op": "sum", "data": [1, 2, 3]},
        )
        assert rule.is_active is True
        assert rule.total_runs_count == 0

        # Evaluate schedules
        triggered = await coord.evaluate_schedules()
        assert len(triggered) == 1
        assert triggered[0].name == "Scheduled: Hourly Aggregation"
        assert rule.total_runs_count == 1

    async def test_dlq_discard_and_purge(self):
        engine = BatchEngineService(tenant_id="test-ws")
        coord = BatchCoordinatorService(engine=engine)

        # Insert DLQ items
        rec1 = BatchDeadLetterRecord(
            task_id="t1", job_id="j1", task_name="task1", error_message="Fatal error 1"
        )
        rec2 = BatchDeadLetterRecord(
            task_id="t2", job_id="j2", task_name="task2", error_message="Fatal error 2"
        )
        engine._dlq[rec1.id] = rec1
        engine._dlq[rec2.id] = rec2

        # Discard rec1
        discarded = await coord.discard_dlq_record(rec1.id)
        assert discarded is not None
        assert discarded.status == DLQStatus.DISCARDED

        # Purge
        purged = await coord.purge_resolved_dlq()
        assert purged == 1
        assert len(engine._dlq) == 1
        assert rec2.id in engine._dlq
