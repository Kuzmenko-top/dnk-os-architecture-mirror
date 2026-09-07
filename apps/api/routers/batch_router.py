# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/batch_router.py"
# purpose: "REST API Router for DNK-BATCH-001 Distributed Batch Processing Engine & DAG Workflows."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from apps.api.db.models.batch_job import BatchJob, BatchJobStatus, BatchJobPriority
from apps.api.db.models.batch_workflow_dag import BatchWorkflowDAG, DAGNode
from apps.api.db.models.batch_worker_node import BatchWorkerNode
from apps.api.db.models.batch_dead_letter_record import BatchDeadLetterRecord, DLQStatus
from apps.api.services.batch_engine_service import BatchEngineService, get_default_batch_engine

logger = logging.getLogger("dnk.batch_router")

router = APIRouter(prefix="/api/v1/batch", tags=["Batch Processing Engine"])


# -----------------------------------------------------------------------------
# Request / Response Schemas
# -----------------------------------------------------------------------------
class SubmitJobRequest(BaseModel):
    name: str = Field(..., description="Job title")
    priority: BatchJobPriority = Field(default=BatchJobPriority.NORMAL)
    payload: Dict[str, Any] = Field(default_factory=dict)
    tasks_spec: Optional[List[Dict[str, Any]]] = None
    timeout_seconds: int = Field(default=3600)
    max_retries: int = Field(default=3)


class SubmitDAGWorkflowRequest(BaseModel):
    name: str = Field(..., description="Workflow title")
    description: str = Field(default="")
    nodes: List[Dict[str, Any]] = Field(..., description="List of DAG nodes [{node_id, name, task_type, dependencies, payload}]")
    concurrency_limit: int = Field(default=5)


class RegisterWorkerRequest(BaseModel):
    hostname: str = Field(default="localhost")
    concurrency_slots: int = Field(default=4)
    supported_task_types: Optional[List[str]] = None
    ip_address: str = Field(default="127.0.0.1")


class HeartbeatRequest(BaseModel):
    cpu_usage_percent: Optional[float] = None
    memory_usage_mb: Optional[float] = None


# -----------------------------------------------------------------------------
# Job Management Endpoints
# -----------------------------------------------------------------------------
@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def submit_batch_job(
    request: SubmitJobRequest,
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Submits a new batch job for asynchronous execution."""
    job = await engine.submit_job(
        name=request.name,
        priority=request.priority,
        payload=request.payload,
        tasks_spec=request.tasks_spec,
        timeout_seconds=request.timeout_seconds,
        max_retries=request.max_retries,
    )
    return {"status": "SUBMITTED", "job": job.to_dict()}


@router.get("/jobs")
async def list_batch_jobs(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, NORMAL, HIGH, CRITICAL)"),
    limit: int = Query(50, ge=1, le=200),
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Lists batch jobs with optional status and priority filtering."""
    status_filter = BatchJobStatus(status) if status else None
    priority_filter = BatchJobPriority(priority) if priority else None
    jobs = await engine.list_jobs(status=status_filter, priority=priority_filter, limit=limit)
    return {"total": len(jobs), "jobs": [j.to_dict() for j in jobs]}


@router.get("/jobs/{job_id}")
async def get_batch_job(
    job_id: str,
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Retrieves full job details and task execution breakdown."""
    details = await engine.get_job_details(job_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return details


@router.post("/jobs/{job_id}/cancel")
async def cancel_batch_job(
    job_id: str,
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Cancels a pending or running batch job."""
    job = await engine.cancel_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"status": "CANCELLED", "job": job.to_dict()}


# -----------------------------------------------------------------------------
# DAG Workflow Endpoints
# -----------------------------------------------------------------------------
@router.post("/workflows/dag", status_code=status.HTTP_201_CREATED)
async def create_dag_workflow(
    request: SubmitDAGWorkflowRequest,
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Creates a Directed Acyclic Graph (DAG) workflow with cycle validation."""
    try:
        dag = await engine.create_dag_workflow(
            name=request.name,
            description=request.description,
            nodes=request.nodes,
            concurrency_limit=request.concurrency_limit,
        )
        return {"status": "CREATED", "dag": dag.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflows/dag/{dag_id}")
async def get_dag_workflow(
    dag_id: str,
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Retrieves DAG workflow definition."""
    dag = engine.get_dag(dag_id)
    if not dag:
        raise HTTPException(status_code=404, detail=f"Workflow DAG {dag_id} not found")
    return {"dag": dag.to_dict()}


@router.post("/workflows/dag/{dag_id}/execute", status_code=status.HTTP_201_CREATED)
async def execute_dag_workflow(
    dag_id: str,
    payload: Optional[Dict[str, Any]] = None,
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Launches execution of a DAG workflow."""
    try:
        job = await engine.execute_dag_workflow(dag_id=dag_id, initial_payload=payload)
        return {"status": "EXECUTED", "job": job.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------------
# Worker Pool Endpoints
# -----------------------------------------------------------------------------
@router.get("/workers")
async def list_workers(
    active_only: bool = Query(False),
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Lists registered worker nodes and resource usage."""
    workers = engine.list_workers(active_only=active_only)
    return {"total": len(workers), "workers": [w.to_dict() for w in workers]}


@router.post("/workers/register", status_code=status.HTTP_201_CREATED)
async def register_worker(
    request: RegisterWorkerRequest,
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Registers a distributed worker node into the pool."""
    worker = await engine.register_worker(
        hostname=request.hostname,
        concurrency_slots=request.concurrency_slots,
        supported_task_types=request.supported_task_types,
        ip_address=request.ip_address,
    )
    return {"status": "REGISTERED", "worker": worker.to_dict()}


@router.post("/workers/{worker_id}/heartbeat")
async def worker_heartbeat(
    worker_id: str,
    request: HeartbeatRequest,
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Records worker heartbeat and metric snapshot."""
    worker = await engine.worker_heartbeat(
        worker_id=worker_id,
        cpu_usage=request.cpu_usage_percent,
        mem_usage=request.memory_usage_mb,
    )
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker {worker_id} not found")
    return {"status": "HEARTBEAT_ACK", "worker": worker.to_dict()}


# -----------------------------------------------------------------------------
# Dead-Letter Queue (DLQ) & Metrics
# -----------------------------------------------------------------------------
@router.get("/dlq")
async def list_dlq(
    status: Optional[str] = Query(None, description="Filter by status (UNRESOLVED, REPLAYED, DISCARDED)"),
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Lists Dead Letter Queue records."""
    dlq_status = DLQStatus(status) if status else None
    records = engine.list_dlq_records(status=dlq_status)
    return {"total": len(records), "dlq_records": [r.to_dict() for r in records]}


@router.post("/dlq/{dlq_id}/replay")
async def replay_dlq_task(
    dlq_id: str,
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Replays a failed task from the Dead Letter Queue."""
    try:
        task = await engine.replay_dlq_record(dlq_id)
        return {"status": "REPLAYED", "task": task.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/metrics")
async def get_batch_metrics(
    engine: BatchEngineService = Depends(get_default_batch_engine),
) -> Dict[str, Any]:
    """Retrieves operational metrics, queue depth and capacity utilization."""
    metrics = engine.get_engine_metrics()
    return {"metrics": metrics}
