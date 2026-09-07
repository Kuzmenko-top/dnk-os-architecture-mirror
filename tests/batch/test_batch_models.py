# --- DNK-MRH-HEADER ---
# mrh_id: "tests/batch/test_batch_models.py"
# purpose: "Unit tests for DNK-BATCH-001 Batch Processing ORM Models and DAG cycle validation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.db.models.batch_job import BatchJob, BatchJobStatus, BatchJobPriority
from apps.api.db.models.batch_task import BatchTask, BatchTaskStatus
from apps.api.db.models.batch_workflow_dag import BatchWorkflowDAG, DAGNode, DAGStatus
from apps.api.db.models.batch_worker_node import BatchWorkerNode, WorkerStatus
from apps.api.db.models.batch_schedule_rule import BatchScheduleRule
from apps.api.db.models.batch_dead_letter_record import BatchDeadLetterRecord, DLQStatus


class TestBatchModels:
    def test_batch_job_lifecycle(self):
        job = BatchJob(name="Data Export Job", payload={"entity": "orders"})
        assert job.status == BatchJobStatus.PENDING
        assert job.priority == BatchJobPriority.NORMAL
        
        job.mark_started()
        assert job.status == BatchJobStatus.RUNNING
        assert job.started_at is not None
        
        job.mark_completed(result={"exported_rows": 1000})
        assert job.status == BatchJobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.result["exported_rows"] == 1000
        
        d = job.to_dict()
        assert d["name"] == "Data Export Job"
        assert d["status"] == "COMPLETED"

    def test_batch_task_lifecycle(self):
        task = BatchTask(
            job_id="job-123",
            name="fetch_chunk_0",
            payload={"offset": 0, "limit": 100},
        )
        assert task.status == BatchTaskStatus.PENDING
        
        task.mark_queued()
        assert task.status == BatchTaskStatus.QUEUED
        
        task.mark_running(worker_id="worker-01")
        assert task.status == BatchTaskStatus.RUNNING
        assert task.assigned_worker_id == "worker-01"
        
        task.mark_completed(result={"count": 100})
        assert task.status == BatchTaskStatus.COMPLETED
        assert task.duration_ms >= 0.0
        
        d = task.to_dict()
        assert d["job_id"] == "job-123"
        assert d["status"] == "COMPLETED"

    def test_batch_task_failure(self):
        task = BatchTask(job_id="job-123", name="failing_task")
        task.mark_running()
        task.mark_failed(error="Connection timeout", stack="Traceback...")
        assert task.status == BatchTaskStatus.FAILED
        assert task.error_message == "Connection timeout"
        assert task.stack_trace == "Traceback..."

    def test_batch_workflow_dag_topological_sort(self):
        dag = BatchWorkflowDAG(name="ETL Pipeline")
        
        node_extract = DAGNode(node_id="extract", name="Extract Data")
        node_transform = DAGNode(node_id="transform", name="Transform Data", dependencies=["extract"])
        node_load = DAGNode(node_id="load", name="Load Data", dependencies=["transform"])
        
        dag.add_node(node_extract)
        dag.add_node(node_transform)
        dag.add_node(node_load)
        
        assert not dag.has_cycles()
        order = dag.get_topological_order()
        assert order == ["extract", "transform", "load"]
        
        root_nodes = dag.get_root_nodes()
        assert len(root_nodes) == 1
        assert root_nodes[0].node_id == "extract"

    def test_batch_workflow_dag_cycle_detection(self):
        dag = BatchWorkflowDAG(name="Cyclic Pipeline")
        
        node_a = DAGNode(node_id="a", name="Node A", dependencies=["b"])
        node_b = DAGNode(node_id="b", name="Node B", dependencies=["a"])
        
        dag.add_node(node_a)
        dag.add_node(node_b)
        
        assert dag.has_cycles() is True
        with pytest.raises(ValueError, match="circular dependencies"):
            dag.get_topological_order()

    def test_batch_worker_node_lifecycle(self):
        worker = BatchWorkerNode(
            hostname="worker-node-1",
            concurrency_slots=4,
        )
        assert worker.status == WorkerStatus.IDLE
        assert worker.has_capacity() is True
        assert worker.is_alive() is True
        
        worker.heartbeat(cpu=45.2, mem=1024.0)
        assert worker.cpu_usage_percent == 45.2
        assert worker.memory_usage_mb == 1024.0

    def test_batch_schedule_and_dlq(self):
        schedule = BatchScheduleRule(
            name="Hourly Sync",
            job_template_name="sync_catalog",
            interval_seconds=3600,
        )
        schedule.mark_triggered()
        assert schedule.total_runs_count == 1
        assert schedule.last_triggered_at is not None
        
        dlq = BatchDeadLetterRecord(
            task_id="task-99",
            job_id="job-99",
            task_name="failed_api_call",
            error_message="HTTP 500 Internal Error",
        )
        assert dlq.status == DLQStatus.UNRESOLVED
        
        dlq.mark_replayed(new_task_id="task-100")
        assert dlq.status == DLQStatus.REPLAYED
        assert dlq.replayed_task_id == "task-100"
