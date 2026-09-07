# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_worker_pool_orchestrator"
# purpose: "Worker Pool Orchestrator & Auto-scaling Engine (DNK-PLATFORM-SCALE-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from apps.api.db.models.worker_pool import WorkerPoolModel
from apps.api.db.models.worker_instance import WorkerInstanceModel
from apps.api.db.models.scaling_event import ScalingEventModel


class WorkerPoolOrchestrator:
    """
    Manages worker pools, worker instances, scale-up/scale-down decisions,
    graceful drains, emergency stops, and records audit scaling events.
    """

    def create_pool(
        self,
        db: Session,
        workspace_id: str,
        name: str,
        min_workers: int = 1,
        max_workers: int = 10,
        target_queue_depth: int = 50,
        scale_up_threshold: int = 80,
        scale_down_idle_seconds: int = 300,
    ) -> WorkerPoolModel:
        pool = WorkerPoolModel(
            workspace_id=workspace_id,
            name=name,
            min_workers=min_workers,
            max_workers=max_workers,
            target_queue_depth=target_queue_depth,
            scale_up_threshold=scale_up_threshold,
            scale_down_idle_seconds=scale_down_idle_seconds,
        )
        db.add(pool)
        db.commit()
        db.refresh(pool)

        # Initialize min_workers instances
        for i in range(min_workers):
            self._spawn_worker(db, pool.id)

        return pool

    def _spawn_worker(self, db: Session, pool_id: str) -> WorkerInstanceModel:
        worker_id = f"worker-{pool_id[:8]}-{uuid.uuid4().hex[:6]}"
        instance = WorkerInstanceModel(
            pool_id=pool_id,
            worker_id=worker_id,
            status="running",
            last_heartbeat=datetime.now(timezone.utc),
            started_at=datetime.now(timezone.utc),
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    def evaluate_scaling(
        self,
        db: Session,
        pool_id: str,
        current_queue_depth: int,
        idle_seconds_max: int = 0,
    ) -> Dict[str, Any]:
        pool = db.query(WorkerPoolModel).filter(WorkerPoolModel.id == pool_id).first()
        if not pool:
            raise ValueError(f"Worker pool {pool_id} not found")

        active_workers = (
            db.query(WorkerInstanceModel)
            .filter(WorkerInstanceModel.pool_id == pool_id, WorkerInstanceModel.status == "running")
            .all()
        )
        current_count = len(active_workers)
        decision = "none"
        new_count = current_count
        reason = "queue depth within normal bounds"

        # Scale Up Condition: depth > scale_up_threshold AND workers < max_workers
        if current_queue_depth >= pool.scale_up_threshold and current_count < pool.max_workers:
            needed = min(pool.max_workers - current_count, max(1, current_queue_depth // pool.target_queue_depth))
            for _ in range(needed):
                self._spawn_worker(db, pool_id)
            decision = "scale_up"
            new_count = current_count + needed
            reason = f"queue depth {current_queue_depth} >= threshold {pool.scale_up_threshold}"

        # Scale Down Condition: depth == 0 AND idle > scale_down_idle_seconds AND workers > min_workers
        elif (
            current_queue_depth == 0
            and idle_seconds_max >= pool.scale_down_idle_seconds
            and current_count > pool.min_workers
        ):
            to_remove = min(current_count - pool.min_workers, 1)
            for inst in active_workers[:to_remove]:
                inst.status = "stopped"
                inst.stopped_at = datetime.now(timezone.utc)
            db.commit()
            decision = "scale_down"
            new_count = current_count - to_remove
            reason = f"idle timeout {idle_seconds_max}s >= threshold {pool.scale_down_idle_seconds}s"

        if decision != "none":
            event = ScalingEventModel(
                pool_id=pool_id,
                event_type=decision,
                worker_count_before=current_count,
                worker_count_after=new_count,
                trigger_reason=reason,
                metadata_json={"queue_depth": current_queue_depth, "idle_seconds": idle_seconds_max},
            )
            db.add(event)
            db.commit()

        return {
            "pool_id": pool_id,
            "decision": decision,
            "worker_count_before": current_count,
            "worker_count_after": new_count,
            "trigger_reason": reason,
        }

    def manual_scale(self, db: Session, pool_id: str, target_workers: int) -> Dict[str, Any]:
        pool = db.query(WorkerPoolModel).filter(WorkerPoolModel.id == pool_id).first()
        if not pool:
            raise ValueError(f"Worker pool {pool_id} not found")

        target_workers = max(pool.min_workers, min(pool.max_workers, target_workers))
        active_workers = (
            db.query(WorkerInstanceModel)
            .filter(WorkerInstanceModel.pool_id == pool_id, WorkerInstanceModel.status == "running")
            .all()
        )
        current_count = len(active_workers)

        if target_workers > current_count:
            for _ in range(target_workers - current_count):
                self._spawn_worker(db, pool_id)
            event_type = "scale_up"
        elif target_workers < current_count:
            to_stop = current_count - target_workers
            for inst in active_workers[:to_stop]:
                inst.status = "stopped"
                inst.stopped_at = datetime.now(timezone.utc)
            db.commit()
            event_type = "scale_down"
        else:
            return {"pool_id": pool_id, "status": "unchanged", "worker_count": current_count}

        event = ScalingEventModel(
            pool_id=pool_id,
            event_type=event_type,
            worker_count_before=current_count,
            worker_count_after=target_workers,
            trigger_reason="manual_scale_command",
        )
        db.add(event)
        db.commit()

        return {
            "pool_id": pool_id,
            "event_type": event_type,
            "worker_count_before": current_count,
            "worker_count_after": target_workers,
        }

    def graceful_drain_worker(self, db: Session, worker_id: str) -> Optional[WorkerInstanceModel]:
        instance = db.query(WorkerInstanceModel).filter(WorkerInstanceModel.worker_id == worker_id).first()
        if instance:
            instance.status = "draining"
            db.commit()
            db.refresh(instance)
        return instance

    def emergency_stop_worker(self, db: Session, worker_id: str) -> Optional[WorkerInstanceModel]:
        instance = db.query(WorkerInstanceModel).filter(WorkerInstanceModel.worker_id == worker_id).first()
        if instance:
            instance.status = "stopped"
            instance.stopped_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(instance)
        return instance
