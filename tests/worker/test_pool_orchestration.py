# --- DNK-MRH-HEADER ---
# mrh_id: "tests_worker_test_pool_orchestration"
# purpose: "Unit & Integration Tests for Worker Pool Orchestration (DNK-PLATFORM-SCALE-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.db.models.worker_pool import WorkerPoolModel
from apps.api.db.models.worker_instance import WorkerInstanceModel
from apps.api.db.models.scaling_event import ScalingEventModel
from apps.api.services.worker_pool_orchestrator import WorkerPoolOrchestrator


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    WorkerPoolModel.__table__.create(engine)
    WorkerInstanceModel.__table__.create(engine)
    ScalingEventModel.__table__.create(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_create_worker_pool_and_spawn_initial(db_session):
    orchestrator = WorkerPoolOrchestrator()
    workspace_id = str(uuid.uuid4())

    pool = orchestrator.create_pool(
        db=db_session,
        name="test-pool-1",
        workspace_id=workspace_id,
        min_workers=2,
        max_workers=5,
        target_queue_depth=50,
        scale_up_threshold=80
    )

    assert pool is not None
    assert pool.name == "test-pool-1"
    assert pool.min_workers == 2

    workers = db_session.query(WorkerInstanceModel).filter(WorkerInstanceModel.pool_id == pool.id).all()
    assert len(workers) == 2
    for w in workers:
        assert w.status == "running"


def test_evaluate_scaling_scale_up(db_session):
    orchestrator = WorkerPoolOrchestrator()
    workspace_id = str(uuid.uuid4())

    pool = orchestrator.create_pool(
        db=db_session,
        name="scale-up-pool",
        workspace_id=workspace_id,
        min_workers=1,
        max_workers=4,
        scale_up_threshold=50
    )

    # Trigger scale up with queue_depth = 120 (> 50)
    event = orchestrator.evaluate_scaling(db=db_session, pool_id=str(pool.id), current_queue_depth=120)
    assert event is not None
    assert event["decision"] == "scale_up"
    assert event["worker_count_after"] > event["worker_count_before"]


def test_evaluate_scaling_scale_down(db_session):
    orchestrator = WorkerPoolOrchestrator()
    workspace_id = str(uuid.uuid4())

    pool = orchestrator.create_pool(
        db=db_session,
        name="scale-down-pool",
        workspace_id=workspace_id,
        min_workers=1,
        max_workers=5,
        scale_up_threshold=50
    )

    # First scale up
    orchestrator.evaluate_scaling(db=db_session, pool_id=str(pool.id), current_queue_depth=150)
    workers_before = db_session.query(WorkerInstanceModel).filter(
        WorkerInstanceModel.pool_id == pool.id, WorkerInstanceModel.status == "running"
    ).all()
    assert len(workers_before) > 1

    # Trigger scale down with queue_depth = 0 and force idle
    event = orchestrator.evaluate_scaling(db=db_session, pool_id=str(pool.id), current_queue_depth=0, idle_seconds_max=350)
    assert event is not None
    assert event["decision"] == "scale_down"


def test_drain_and_emergency_stop(db_session):
    orchestrator = WorkerPoolOrchestrator()
    workspace_id = str(uuid.uuid4())

    pool = orchestrator.create_pool(
        db=db_session,
        name="drain-pool",
        workspace_id=workspace_id,
        min_workers=2,
        max_workers=3
    )

    workers = db_session.query(WorkerInstanceModel).filter(WorkerInstanceModel.pool_id == pool.id).all()
    target_worker = workers[0]

    # Graceful drain
    drained = orchestrator.graceful_drain_worker(db=db_session, worker_id=str(target_worker.worker_id))
    assert drained is not None
    assert drained.status == "draining"

    # Emergency stop
    stopped = orchestrator.emergency_stop_worker(db=db_session, worker_id=str(target_worker.worker_id))
    assert stopped is not None
    assert stopped.status == "stopped"
