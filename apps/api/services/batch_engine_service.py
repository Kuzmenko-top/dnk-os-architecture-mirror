# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/batch_engine_service.py"
# purpose: "Distributed Batch Processing Engine, DAG Orchestrator & Worker Pool Service for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import inspect
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from apps.api.db.models.batch_job import BatchJob, BatchJobPriority, BatchJobStatus
from apps.api.db.models.batch_task import BatchTask, BatchTaskStatus
from apps.api.db.models.batch_workflow_dag import BatchWorkflowDAG, DAGNode, DAGStatus
from apps.api.db.models.batch_worker_node import BatchWorkerNode, WorkerStatus
from apps.api.db.models.batch_schedule_rule import BatchScheduleRule
from apps.api.db.models.batch_dead_letter_record import BatchDeadLetterRecord, DLQStatus
from apps.api.services.trace_instrumentation_service import (
    trace_span,
)

logger = logging.getLogger("dnk.batch_engine")


class BatchEngineService:
    """Core distributed batch processing engine orchestrating jobs, DAG workflows, and worker pools."""

    def __init__(self, tenant_id: str = "ws-alpha-001"):
        self.tenant_id = tenant_id
        self._jobs: Dict[str, BatchJob] = {}
        self._tasks: Dict[str, BatchTask] = {}
        self._dags: Dict[str, BatchWorkflowDAG] = {}
        self._workers: Dict[str, BatchWorkerNode] = {}
        self._schedules: Dict[str, BatchScheduleRule] = {}
        self._dlq: Dict[str, BatchDeadLetterRecord] = {}
        self._task_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._lock = asyncio.Lock()
        
        # Register default internal handlers
        self.register_task_handler("generic_compute", self._default_compute_handler)
        self.register_task_handler("python_func", self._default_compute_handler)
        self.register_task_handler("noop", lambda payload: {"status": "ok", "echo": payload})

    # -------------------------------------------------------------------------
    # Handler Registration
    # -------------------------------------------------------------------------
    def register_task_handler(self, task_type: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        """Registers a callable handler for a specific task_type."""
        self._task_handlers[task_type] = handler

    async def _default_compute_handler(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Default compute execution handler simulation."""
        operation = payload.get("op", "noop")
        data = payload.get("data", [])
        if operation == "sum" and isinstance(data, list):
            return {"result": sum(data), "count": len(data)}
        elif operation == "transform":
            return {"transformed": [str(x).upper() for x in data]}
        return {"processed": True, "payload": payload}

    # -------------------------------------------------------------------------
    # Worker Pool Management
    # -------------------------------------------------------------------------
    async def register_worker(
        self,
        hostname: str = "localhost",
        concurrency_slots: int = 4,
        supported_task_types: Optional[List[str]] = None,
        ip_address: str = "127.0.0.1",
    ) -> BatchWorkerNode:
        """Registers a new worker node in the distributed pool."""
        async with self._lock:
            worker = BatchWorkerNode(
                hostname=hostname,
                ip_address=ip_address,
                concurrency_slots=concurrency_slots,
                supported_task_types=supported_task_types or ["*"],
                tenant_id=self.tenant_id,
                status=WorkerStatus.IDLE,
            )
            self._workers[worker.id] = worker
            logger.info("Registered worker node %s (%s slots)", worker.id, concurrency_slots)
            return worker

    async def worker_heartbeat(
        self,
        worker_id: str,
        cpu_usage: Optional[float] = None,
        mem_usage: Optional[float] = None,
    ) -> Optional[BatchWorkerNode]:
        """Updates worker heartbeat and resource metrics."""
        async with self._lock:
            worker = self._workers.get(worker_id)
            if not worker:
                return None
            worker.heartbeat(cpu=cpu_usage, mem=mem_usage)
            return worker

    def list_workers(self, active_only: bool = False) -> List[BatchWorkerNode]:
        """Lists registered workers, optionally filtering only alive/active ones."""
        workers = list(self._workers.values())
        if active_only:
            return [w for w in workers if w.is_alive()]
        return workers

    def _acquire_worker_for_task(self, task: BatchTask) -> Optional[BatchWorkerNode]:
        """Finds an available worker with capacity matching task requirements."""
        for worker in self._workers.values():
            if not worker.is_alive():
                worker.status = WorkerStatus.OFFLINE
                continue
            if "*" in worker.supported_task_types or task.task_type in worker.supported_task_types:
                if worker.has_capacity():
                    return worker
        return None

    # -------------------------------------------------------------------------
    # Job & Task Creation
    # -------------------------------------------------------------------------
    async def submit_job(
        self,
        name: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: BatchJobPriority = BatchJobPriority.NORMAL,
        tasks_spec: Optional[List[Dict[str, Any]]] = None,
        timeout_seconds: int = 3600,
        max_retries: int = 3,
        created_by: str = "system",
        trace_id: Optional[str] = None,
    ) -> BatchJob:
        """Submits a new batch job with optional explicit subtasks."""
        async with self._lock:
            job = BatchJob(
                name=name,
                tenant_id=self.tenant_id,
                priority=priority,
                payload=payload or {},
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                created_by=created_by,
                trace_id=trace_id,
            )
            self._jobs[job.id] = job

            if tasks_spec:
                job.total_tasks = len(tasks_spec)
                for t_spec in tasks_spec:
                    task = BatchTask(
                        job_id=job.id,
                        name=t_spec.get("name", f"task_{uuid.uuid4().hex[:6]}"),
                        tenant_id=self.tenant_id,
                        task_type=t_spec.get("task_type", "generic_compute"),
                        payload=t_spec.get("payload", {}),
                        dependencies=t_spec.get("dependencies", []),
                        max_retries=t_spec.get("max_retries", max_retries),
                        trace_id=trace_id,
                    )
                    self._tasks[task.id] = task

            return job

    async def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Retrieves a batch job by ID."""
        return self._jobs.get(job_id)

    async def get_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves full job details and associated tasks."""
        job = self._jobs.get(job_id)
        if not job:
            return None
        tasks = [t.to_dict() for t in self.get_job_tasks(job_id)]
        res = job.to_dict()
        res["tasks"] = tasks
        return res

    async def cancel_job(self, job_id: str) -> Optional[BatchJob]:
        """Cancels a job and any pending/running tasks."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.status = BatchJobStatus.CANCELLED
            for t in self.get_job_tasks(job_id):
                if t.status in [BatchTaskStatus.PENDING, BatchTaskStatus.QUEUED, BatchTaskStatus.RUNNING]:
                    t.status = BatchTaskStatus.CANCELLED
            return job

    async def list_jobs(
        self,
        status: Optional[BatchJobStatus] = None,
        priority: Optional[BatchJobPriority] = None,
        limit: int = 100,
    ) -> List[BatchJob]:
        """Lists batch jobs with optional filtering."""
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        if priority:
            jobs = [j for j in jobs if j.priority == priority]
        # Sort newest first
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def get_job_tasks(self, job_id: str) -> List[BatchTask]:
        """Returns all tasks associated with a given job."""
        return [t for t in self._tasks.values() if t.job_id == job_id]

    # -------------------------------------------------------------------------
    # DAG Workflow Management & Execution
    # -------------------------------------------------------------------------
    async def create_dag_workflow(
        self,
        name: str,
        description: str = "",
        nodes: Optional[List[Dict[str, Any]]] = None,
        concurrency_limit: int = 5,
    ) -> BatchWorkflowDAG:
        """Creates and validates a new Directed Acyclic Graph (DAG) workflow."""
        dag = BatchWorkflowDAG(
            name=name,
            description=description,
            tenant_id=self.tenant_id,
            concurrency_limit=concurrency_limit,
            status=DAGStatus.ACTIVE,
        )

        if nodes:
            for n_dict in nodes:
                node = DAGNode(
                    node_id=n_dict["node_id"],
                    name=n_dict.get("name", n_dict["node_id"]),
                    task_type=n_dict.get("task_type", "python_func"),
                    dependencies=n_dict.get("dependencies", []),
                    payload=n_dict.get("payload", {}),
                    max_retries=n_dict.get("max_retries", 3),
                )
                dag.add_node(node)

        if dag.has_cycles():
            raise ValueError(f"Workflow '{name}' contains cyclic dependencies and is invalid.")

        async with self._lock:
            self._dags[dag.id] = dag

        return dag

    def get_dag(self, dag_id: str) -> Optional[BatchWorkflowDAG]:
        return self._dags.get(dag_id)

    def list_dags(self) -> List[BatchWorkflowDAG]:
        return list(self._dags.values())

    async def execute_dag_workflow(self, dag_id: str, initial_payload: Optional[Dict[str, Any]] = None) -> BatchJob:
        """Launches execution of a DAG workflow, creating tasks with dependency resolution."""
        dag = self._dags.get(dag_id)
        if not dag:
            raise ValueError(f"DAG workflow with ID '{dag_id}' not found.")

        if dag.has_cycles():
            raise ValueError(f"Cannot execute DAG '{dag_id}': cyclical dependencies detected.")

        # Create parent BatchJob
        job = await self.submit_job(
            name=f"DAG Execution: {dag.name}",
            payload=initial_payload or {},
            priority=BatchJobPriority.HIGH,
        )
        job.workflow_id = dag.id

        # Create tasks corresponding to DAG nodes
        node_id_to_task_id: Dict[str, str] = {}
        created_tasks: List[BatchTask] = []

        for node_id, node in dag.nodes.items():
            task = BatchTask(
                job_id=job.id,
                name=node.name,
                tenant_id=self.tenant_id,
                task_type=node.task_type,
                payload={**node.payload, **(initial_payload or {})},
                max_retries=node.max_retries,
            )
            node_id_to_task_id[node_id] = task.id
            created_tasks.append(task)
            self._tasks[task.id] = task

        # Map dependencies from node_id -> task_id
        for node_id, node in dag.nodes.items():
            task_id = node_id_to_task_id[node_id]
            task = self._tasks[task_id]
            task.dependencies = [node_id_to_task_id[dep] for dep in node.dependencies if dep in node_id_to_task_id]

        job.total_tasks = len(created_tasks)
        return job

    # -------------------------------------------------------------------------
    # Task Execution & Scheduling Engine
    # -------------------------------------------------------------------------
    async def execute_task(self, task_id: str, worker_id: Optional[str] = None) -> BatchTask:
        """Executes a single batch task using registered handler and records metrics."""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task with ID '{task_id}' not found.")

        # Find or assign worker
        worker: Optional[BatchWorkerNode] = None
        if worker_id:
            worker = self._workers.get(worker_id)
        else:
            worker = self._acquire_worker_for_task(task)

        assigned_id = worker.id if worker else "inline-worker"
        if worker:
            worker.status = WorkerStatus.BUSY
            worker.active_tasks_count += 1
            worker.current_task_ids.append(task.id)

        task.mark_running(worker_id=assigned_id)

        # Execute handler with distributed tracing span
        handler = self._task_handlers.get(task.task_type, self._default_compute_handler)

        async with trace_span(
            name=f"batch.task.{task.name}",
            service_name="dnk_batch_engine",
            attributes={"batch.task_id": task.id, "batch.job_id": task.job_id, "batch.task_type": task.task_type},
        ) as span:
            task.trace_id = span.trace_id
            task.span_id = span.span_id

            try:
                if inspect.iscoroutinefunction(handler):
                    result = await handler(task.payload)
                else:
                    result = handler(task.payload)

                task.mark_completed(result=result if isinstance(result, dict) else {"result": result})

                if worker:
                    worker.tasks_processed_total += 1

            except Exception as ex:
                logger.error("Task %s failed: %s", task.id, str(ex))
                task.mark_failed(error=str(ex))
                if worker:
                    worker.tasks_failed_total += 1

                # Handle retry or move to DLQ
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = BatchTaskStatus.RETRYING
                else:
                    # Move to Dead Letter Queue
                    await self._send_to_dlq(task)

            finally:
                if worker:
                    worker.active_tasks_count = max(0, worker.active_tasks_count - 1)
                    if task.id in worker.current_task_ids:
                        worker.current_task_ids.remove(task.id)
                    if worker.active_tasks_count == 0:
                        worker.status = WorkerStatus.IDLE

        return task

    async def execute_job_synchronous(self, job_id: str) -> BatchJob:
        """Synchronously resolves all tasks of a job adhering to dependencies."""
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job with ID '{job_id}' not found.")

        job.mark_started()
        tasks = self.get_job_tasks(job.id)

        completed_task_ids: Set[str] = set()
        failed_task_ids: Set[str] = set()

        while len(completed_task_ids) + len(failed_task_ids) < len(tasks):
            # Find tasks whose dependencies are fully satisfied
            runnable_tasks = [
                t for t in tasks
                if t.status in [BatchTaskStatus.PENDING, BatchTaskStatus.QUEUED, BatchTaskStatus.RETRYING]
                and all(dep in completed_task_ids for dep in t.dependencies)
            ]

            if not runnable_tasks:
                # Deadlock or broken dependencies due to failed prerequisites
                for t in tasks:
                    if t.status in [BatchTaskStatus.PENDING, BatchTaskStatus.QUEUED]:
                        t.status = BatchTaskStatus.SKIPPED
                break

            # Execute runnable tasks concurrently
            exec_coros = [self.execute_task(t.id) for t in runnable_tasks]
            executed = await asyncio.gather(*exec_coros, return_exceptions=True)

            for item in executed:
                if isinstance(item, BatchTask):
                    if item.status == BatchTaskStatus.COMPLETED:
                        completed_task_ids.add(item.id)
                        job.completed_tasks += 1
                    elif item.status in [BatchTaskStatus.FAILED, BatchTaskStatus.RETRYING]:
                        if item.status == BatchTaskStatus.FAILED:
                            failed_task_ids.add(item.id)
                            job.failed_tasks += 1

        # Evaluate final job status
        if job.failed_tasks > 0:
            job.mark_failed(f"{job.failed_tasks} subtasks failed during execution.")
        else:
            job.mark_completed(result={"completed_tasks": job.completed_tasks, "total": job.total_tasks})

        return job

    # -------------------------------------------------------------------------
    # Dead Letter Queue (DLQ)
    # -------------------------------------------------------------------------
    async def _send_to_dlq(self, task: BatchTask) -> BatchDeadLetterRecord:
        """Transfers an exhausted failed task into the Dead Letter Queue."""
        record = BatchDeadLetterRecord(
            task_id=task.id,
            job_id=task.job_id,
            tenant_id=self.tenant_id,
            task_name=task.name,
            payload=task.payload,
            error_message=task.error_message or "Unknown execution failure",
            stack_trace=task.stack_trace,
            retry_count=task.retry_count,
            trace_id=task.trace_id,
            span_id=task.span_id,
        )
        self._dlq[record.id] = record
        logger.warning("Task %s moved to DLQ (Record: %s)", task.id, record.id)
        return record

    def list_dlq_records(self, status: Optional[DLQStatus] = None) -> List[BatchDeadLetterRecord]:
        """Lists records currently held in DLQ."""
        records = list(self._dlq.values())
        if status:
            return [r for r in records if r.status == status]
        return records

    async def replay_dlq_record(self, dlq_id: str) -> BatchTask:
        """Replays a task stored in DLQ by spawning a new task execution."""
        record = self._dlq.get(dlq_id)
        if not record:
            raise ValueError(f"DLQ Record with ID '{dlq_id}' not found.")

        # Create new replay task
        new_task = BatchTask(
            job_id=record.job_id,
            name=f"replay_{record.task_name}",
            tenant_id=self.tenant_id,
            payload=record.payload,
            max_retries=3,
        )
        self._tasks[new_task.id] = new_task
        record.mark_replayed(new_task_id=new_task.id)

        # Execute replayed task
        return await self.execute_task(new_task.id)

    # -------------------------------------------------------------------------
    # Metrics & Summary
    # -------------------------------------------------------------------------
    def get_engine_metrics(self) -> Dict[str, Any]:
        """Returns consolidated health and throughput statistics for the batch engine."""
        jobs_by_status = {}
        for j in self._jobs.values():
            status_str = j.status.value if isinstance(j.status, BatchJobStatus) else str(j.status)
            jobs_by_status[status_str] = jobs_by_status.get(status_str, 0) + 1

        active_workers = [w for w in self._workers.values() if w.is_alive()]
        total_slots = sum(w.concurrency_slots for w in active_workers)
        busy_slots = sum(w.active_tasks_count for w in active_workers)

        return {
            "tenant_id": self.tenant_id,
            "total_jobs": len(self._jobs),
            "jobs_by_status": jobs_by_status,
            "total_tasks": len(self._tasks),
            "active_workers_count": len(active_workers),
            "total_concurrency_slots": total_slots,
            "allocated_slots": busy_slots,
            "capacity_utilization_pct": round((busy_slots / total_slots * 100.0) if total_slots > 0 else 0.0, 2),
            "dlq_unresolved_count": len([r for r in self._dlq.values() if r.status == DLQStatus.UNRESOLVED]),
            "registered_dags_count": len(self._dags),
        }


# Singleton accessor
_default_batch_engine: Optional[BatchEngineService] = None


def get_default_batch_engine() -> BatchEngineService:
    global _default_batch_engine
    if _default_batch_engine is None:
        _default_batch_engine = BatchEngineService()
    return _default_batch_engine
