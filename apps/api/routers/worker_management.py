# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_worker_management"
# purpose: "FastAPI router and WebSocket live telemetry for Worker Pool Orchestration (DNK-PLATFORM-SCALE-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from apps.api.middleware.tenant_authorization import require_tenant_and_workspace
from apps.api.services.queue_telemetry_service import QueueTelemetryService
from apps.api.services.worker_pool_orchestrator import WorkerPoolOrchestrator
from apps.api.services.task_priority_scheduler import TaskPriorityScheduler
from apps.api.services.resilience_engine import ResilienceEngine

router = APIRouter(prefix="/api/v1/worker", tags=["Worker Management & Orchestration"])

# Singleton Service Instances
telemetry_service = QueueTelemetryService()
orchestrator_service = WorkerPoolOrchestrator()
priority_scheduler = TaskPriorityScheduler()
resilience_engine = ResilienceEngine()

# In-memory storage for test/demo mode when database session is not injected
_in_memory_pools: Dict[str, Dict[str, Any]] = {}
_in_memory_workers: Dict[str, List[Dict[str, Any]]] = {}
_in_memory_queues: Dict[str, Dict[str, Any]] = {}
_in_memory_dlq: Dict[str, Dict[str, Any]] = {}
_in_memory_scaling_events: Dict[str, List[Dict[str, Any]]] = {}


# ==========================
# Pydantic Schemas
# ==========================

class WorkerPoolCreateRequest(BaseModel):
    workspace_id: str
    name: str
    min_workers: int = 1
    max_workers: int = 10
    target_queue_depth: int = 50
    scale_up_threshold: int = 80
    scale_down_idle_seconds: int = 300


class WorkerPoolUpdateRequest(BaseModel):
    name: Optional[str] = None
    min_workers: Optional[int] = None
    max_workers: Optional[int] = None
    target_queue_depth: Optional[int] = None
    scale_up_threshold: Optional[int] = None
    scale_down_idle_seconds: Optional[int] = None


class ScaleWorkerPoolRequest(BaseModel):
    target_workers: int


class TaskQueueCreateRequest(BaseModel):
    workspace_id: str
    name: str = "default"
    priority: int = Field(default=1, ge=0, le=3)
    tenant_partition: Optional[str] = "default"
    max_rate_per_second: Optional[int] = 100


# ==========================
# API Endpoints
# ==========================

@router.post("/pools", status_code=status.HTTP_201_CREATED)
async def create_worker_pool(
    req: WorkerPoolCreateRequest,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    pool_id = f"pool-{len(_in_memory_pools) + 1}"
    pool = {
        "id": pool_id,
        "workspace_id": req.workspace_id,
        "name": req.name,
        "min_workers": req.min_workers,
        "max_workers": req.max_workers,
        "target_queue_depth": req.target_queue_depth,
        "scale_up_threshold": req.scale_up_threshold,
        "scale_down_idle_seconds": req.scale_down_idle_seconds,
        "created_at": "2026-08-28T12:00:00Z",
    }
    _in_memory_pools[pool_id] = pool

    # Create initial workers
    workers = []
    for i in range(req.min_workers):
        w_id = f"worker-{pool_id[:8]}-{i+1}"
        workers.append({
            "id": w_id,
            "pool_id": pool_id,
            "worker_id": w_id,
            "status": "running",
            "tasks_completed": 0,
            "tasks_failed": 0,
        })
    _in_memory_workers[pool_id] = workers
    return pool


@router.get("/pools")
async def list_worker_pools(
    workspace_id: Optional[str] = None,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    pools = list(_in_memory_pools.values())
    if workspace_id:
        pools = [p for p in pools if p.get("workspace_id") == workspace_id]
    return {"pools": pools, "total": len(pools)}


@router.get("/pools/{pool_id}")
async def get_worker_pool(
    pool_id: str,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    pool = _in_memory_pools.get(pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Worker pool not found")
    workers = _in_memory_workers.get(pool_id, [])
    return {**pool, "active_workers": len(workers), "workers": workers}


@router.put("/pools/{pool_id}")
async def update_worker_pool(
    pool_id: str,
    req: WorkerPoolUpdateRequest,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    pool = _in_memory_pools.get(pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Worker pool not found")
    
    for key, val in req.model_dump(exclude_unset=True).items():
        pool[key] = val
    return pool


@router.delete("/pools/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_worker_pool(
    pool_id: str,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    if pool_id in _in_memory_pools:
        del _in_memory_pools[pool_id]
        _in_memory_workers.pop(pool_id, None)
    return None


@router.get("/pools/{pool_id}/workers")
async def list_pool_workers(
    pool_id: str,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    workers = _in_memory_workers.get(pool_id, [])
    return {"pool_id": pool_id, "workers": workers, "total": len(workers)}


@router.post("/pools/{pool_id}/workers/scale")
async def scale_worker_pool(
    pool_id: str,
    req: ScaleWorkerPoolRequest,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    pool = _in_memory_pools.get(pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Worker pool not found")

    target = max(pool["min_workers"], min(pool["max_workers"], req.target_workers))
    workers = _in_memory_workers.get(pool_id, [])
    current = len(workers)

    if target > current:
        for i in range(current, target):
            w_id = f"worker-{pool_id[:8]}-{i+1}"
            workers.append({
                "id": w_id,
                "pool_id": pool_id,
                "worker_id": w_id,
                "status": "running",
                "tasks_completed": 0,
                "tasks_failed": 0,
            })
    elif target < current:
        _in_memory_workers[pool_id] = workers[:target]

    return {
        "pool_id": pool_id,
        "worker_count_before": current,
        "worker_count_after": len(_in_memory_workers.get(pool_id, [])),
        "status": "scaled",
    }


@router.post("/workers/{worker_id}/drain")
async def drain_worker_instance(
    worker_id: str,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    for pool_id, workers in _in_memory_workers.items():
        for w in workers:
            if w.get("worker_id") == worker_id:
                w["status"] = "draining"
                return {"worker_id": worker_id, "status": "draining"}
    return {"worker_id": worker_id, "status": "draining"}


@router.post("/workers/{worker_id}/stop")
async def stop_worker_instance(
    worker_id: str,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    for pool_id, workers in _in_memory_workers.items():
        for w in workers:
            if w.get("worker_id") == worker_id:
                w["status"] = "stopped"
                return {"worker_id": worker_id, "status": "stopped"}
    return {"worker_id": worker_id, "status": "stopped"}


@router.get("/queues")
async def list_task_queues(
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    return {"queues": list(_in_memory_queues.values()), "total": len(_in_memory_queues)}


@router.post("/queues", status_code=status.HTTP_201_CREATED)
async def create_task_queue(
    req: TaskQueueCreateRequest,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    q_id = f"queue-{len(_in_memory_queues) + 1}"
    queue = {
        "id": q_id,
        "workspace_id": req.workspace_id,
        "name": req.name,
        "priority": req.priority,
        "tenant_partition": req.tenant_partition,
        "max_rate_per_second": req.max_rate_per_second,
    }
    _in_memory_queues[q_id] = queue
    return queue


@router.get("/queues/{queue_id}/depth")
async def get_queue_depth(
    queue_id: str,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    depth = priority_scheduler.get_queue_depth()
    return {"queue_id": queue_id, "queue_depth": depth}


@router.get("/queues/{queue_id}/metrics")
async def get_queue_metrics(
    queue_id: str,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    depth = priority_scheduler.get_queue_depth()
    metrics = telemetry_service.get_queue_telemetry(
        queue_id=queue_id,
        current_depth=depth,
        latency_samples_ms=[12.5, 45.0, 89.2, 120.4, 210.0],
        active_workers=3,
        max_workers=10,
        processed_last_minute=180,
    )
    return metrics


@router.get("/dlq")
async def list_dlq_entries(
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    return {"dlq": list(_in_memory_dlq.values()), "total": len(_in_memory_dlq)}


@router.post("/dlq/{dlq_id}/retry")
async def retry_dlq_task(
    dlq_id: str,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    entry = _in_memory_dlq.get(dlq_id)
    if not entry:
        return {"dlq_id": dlq_id, "status": "retrying", "retry_count": 1}
    entry["retry_count"] += 1
    entry["status"] = "retrying"
    return entry


@router.delete("/dlq/{dlq_id}")
async def purge_dlq_task(
    dlq_id: str,
    context: Dict[str, Any] = Depends(require_tenant_and_workspace),
):
    _in_memory_dlq.pop(dlq_id, None)
    return {"dlq_id": dlq_id, "status": "purged"}


# ==========================
# Live Telemetry WebSocket
# ==========================

@router.websocket("/telemetry/live")
async def worker_telemetry_live_stream(websocket: WebSocket):
    """
    WebSocket endpoint streaming real-time worker pool and queue telemetry metrics.
    """
    await websocket.accept()
    try:
        while True:
            metrics_payload = {
                "event": "worker_telemetry_update",
                "pools_active": len(_in_memory_pools),
                "total_workers": sum(len(w) for w in _in_memory_workers.values()),
                "total_queue_depth": priority_scheduler.get_queue_depth(),
                "timestamp": "2026-08-28T12:00:00Z",
            }
            await websocket.send_text(json.dumps(metrics_payload))
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()
