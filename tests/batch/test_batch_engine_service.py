# --- DNK-MRH-HEADER ---
# mrh_id: "tests/batch/test_batch_engine_service.py"
# purpose: "Unit tests for DNK-BATCH-001 Batch Engine, DAG Orchestration & Worker Pool Service."
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
from apps.api.db.models.batch_job import BatchJobPriority, BatchJobStatus
from apps.api.db.models.batch_task import BatchTaskStatus
from apps.api.db.models.batch_workflow_dag import DAGNode, DAGStatus
from apps.api.db.models.batch_worker_node import WorkerStatus
from apps.api.db.models.batch_dead_letter_record import DLQStatus
from apps.api.services.batch_engine_service import BatchEngineService


@pytest.mark.asyncio
class TestBatchEngineService:
    async def test_worker_registration_and_heartbeat(self):
        engine = BatchEngineService(tenant_id="test-ws")
        worker = await engine.register_worker(hostname="worker-01", concurrency_slots=8)
        assert worker.hostname == "worker-01"
        assert worker.concurrency_slots == 8
        assert worker.status == WorkerStatus.IDLE

        # Heartbeat
        updated = await engine.worker_heartbeat(worker.id, cpu_usage=25.4, mem_usage=42.1)
        assert updated is not None
        assert updated.cpu_usage_percent == 25.4
        assert updated.memory_usage_mb == 42.1

        active = engine.list_workers(active_only=True)
        assert len(active) == 1

    async def test_submit_and_execute_single_task_job(self):
        engine = BatchEngineService(tenant_id="test-ws")
        worker = await engine.register_worker(hostname="worker-01", concurrency_slots=4)

        job = await engine.submit_job(
            name="Sum Computation",
            tasks_spec=[
                {
                    "name": "calc_sum",
                    "task_type": "generic_compute",
                    "payload": {"op": "sum", "data": [10, 20, 30]},
                }
            ],
        )
        assert job.total_tasks == 1
        assert job.status == BatchJobStatus.PENDING

        tasks = engine.get_job_tasks(job.id)
        assert len(tasks) == 1

        # Execute
        resolved_job = await engine.execute_job_synchronous(job.id)
        assert resolved_job.status == BatchJobStatus.COMPLETED
        assert resolved_job.completed_tasks == 1

        task = engine.get_job_tasks(job.id)[0]
        assert task.status == BatchTaskStatus.COMPLETED
        assert task.result == {"result": 60, "count": 3}
        assert task.trace_id is not None

    async def test_dag_workflow_execution_with_dependencies(self):
        engine = BatchEngineService(tenant_id="test-ws")
        await engine.register_worker(hostname="worker-01", concurrency_slots=4)

        # Create DAG: A -> B -> C
        dag = await engine.create_dag_workflow(
            name="ETL Pipeline",
            nodes=[
                {"node_id": "extract", "task_type": "generic_compute", "payload": {"op": "noop", "data": [1, 2, 3]}},
                {"node_id": "transform", "task_type": "generic_compute", "payload": {"op": "transform", "data": ["a", "b"]}, "dependencies": ["extract"]},
                {"node_id": "load", "task_type": "generic_compute", "payload": {"op": "noop"}, "dependencies": ["transform"]},
            ],
        )
        assert dag.status == DAGStatus.ACTIVE
        assert len(dag.nodes) == 3

        # Execute DAG
        job = await engine.execute_dag_workflow(dag.id)
        assert job.total_tasks == 3

        resolved_job = await engine.execute_job_synchronous(job.id)
        assert resolved_job.status == BatchJobStatus.COMPLETED
        assert resolved_job.completed_tasks == 3
        assert resolved_job.failed_tasks == 0

    async def test_task_failure_and_dlq_routing(self):
        engine = BatchEngineService(tenant_id="test-ws")
        await engine.register_worker(hostname="worker-01", concurrency_slots=2)

        # Custom failing handler
        def failing_handler(payload):
            raise RuntimeError("Database connection timeout")

        engine.register_task_handler("flaky_service", failing_handler)

        job = await engine.submit_job(
            name="Failing Task Job",
            tasks_spec=[
                {
                    "name": "flaky_task",
                    "task_type": "flaky_service",
                    "payload": {"data": "test"},
                    "max_retries": 1,
                }
            ],
        )

        resolved_job = await engine.execute_job_synchronous(job.id)
        assert resolved_job.status == BatchJobStatus.FAILED
        assert resolved_job.failed_tasks == 1

        # Check DLQ
        dlq_records = engine.list_dlq_records()
        assert len(dlq_records) == 1
        record = dlq_records[0]
        assert record.status == DLQStatus.UNRESOLVED
        assert "Database connection timeout" in record.error_message

        # Replay DLQ record after fixing handler
        engine.register_task_handler("flaky_service", lambda p: {"recovered": True})
        replayed_task = await engine.replay_dlq_record(record.id)
        assert replayed_task.status == BatchTaskStatus.COMPLETED
        assert record.status == DLQStatus.REPLAYED

    async def test_engine_metrics_and_capacity_utilization(self):
        engine = BatchEngineService(tenant_id="test-ws")
        await engine.register_worker(hostname="w1", concurrency_slots=10)
        await engine.register_worker(hostname="w2", concurrency_slots=10)

        await engine.submit_job(name="Job 1")
        await engine.submit_job(name="Job 2")

        metrics = engine.get_engine_metrics()
        assert metrics["tenant_id"] == "test-ws"
        assert metrics["total_jobs"] == 2
        assert metrics["active_workers_count"] == 2
        assert metrics["total_concurrency_slots"] == 20
        assert metrics["capacity_utilization_pct"] == 0.0
