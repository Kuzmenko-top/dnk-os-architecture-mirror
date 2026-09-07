# --- DNK-MRH-HEADER ---
# mrh_id: "tests/batch/test_batch_router.py"
# purpose: "Integration tests for DNK-BATCH-001 Batch Processing REST API Endpoints."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.main import app
from apps.api.services.batch_engine_service import get_default_batch_engine
from apps.api.db.models.batch_job import BatchJobPriority


@pytest.fixture(autouse=True)
def clean_batch_engine():
    engine = get_default_batch_engine()
    engine._jobs.clear()
    engine._tasks.clear()
    engine._dags.clear()
    engine._workers.clear()
    engine._dlq.clear()
    yield


@pytest.mark.asyncio
async def test_submit_and_get_job():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name": "Integration ETL Job",
            "priority": "HIGH",
            "payload": {"source": "s3://bucket/data.csv"},
            "tasks_spec": [
                {"name": "extract", "task_type": "download"},
                {"name": "transform", "task_type": "normalize"},
            ],
            "timeout_seconds": 1800,
            "max_retries": 2,
        }
        res = await client.post("/api/v1/batch/jobs", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "SUBMITTED"
        job_id = data["job"]["id"]
        assert data["job"]["total_tasks"] == 2

        # Get Job details
        get_res = await client.get(f"/api/v1/batch/jobs/{job_id}")
        assert get_res.status_code == 200
        job_details = get_res.json()
        assert job_details["id"] == job_id
        assert len(job_details["tasks"]) == 2

        # List jobs
        list_res = await client.get("/api/v1/batch/jobs?priority=HIGH")
        assert list_res.status_code == 200
        assert list_res.json()["total"] == 1


@pytest.mark.asyncio
async def test_cancel_batch_job():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/batch/jobs", json={"name": "Job to Cancel"})
        job_id = res.json()["job"]["id"]

        cancel_res = await client.post(f"/api/v1/batch/jobs/{job_id}/cancel")
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"
        assert cancel_res.json()["job"]["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_dag_workflow_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dag_payload = {
            "name": "ETL Pipeline DAG",
            "description": "Extract Transform Load with dependency checks",
            "nodes": [
                {"node_id": "extract", "name": "Extract Raw", "task_type": "extract", "dependencies": []},
                {"node_id": "transform", "name": "Transform Data", "task_type": "transform", "dependencies": ["extract"]},
                {"node_id": "load", "name": "Load to DW", "task_type": "load", "dependencies": ["transform"]},
            ],
            "concurrency_limit": 3,
        }
        create_res = await client.post("/api/v1/batch/workflows/dag", json=dag_payload)
        assert create_res.status_code == 201
        dag_data = create_res.json()
        dag_id = dag_data["dag"]["id"]

        # Get DAG
        get_res = await client.get(f"/api/v1/batch/workflows/dag/{dag_id}")
        assert get_res.status_code == 200
        assert get_res.json()["dag"]["name"] == "ETL Pipeline DAG"

        # Execute DAG
        exec_res = await client.post(f"/api/v1/batch/workflows/dag/{dag_id}/execute", json={"batch_date": "2026-08-29"})
        assert exec_res.status_code == 201
        assert exec_res.json()["status"] == "EXECUTED"
        assert exec_res.json()["job"]["total_tasks"] == 3


@pytest.mark.asyncio
async def test_dag_workflow_cycle_rejection():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cyclic_dag = {
            "name": "Cyclic DAG",
            "nodes": [
                {"node_id": "A", "dependencies": ["B"]},
                {"node_id": "B", "dependencies": ["A"]},
            ],
        }
        res = await client.post("/api/v1/batch/workflows/dag", json=cyclic_dag)
        assert res.status_code == 400
        assert "cyclic dependencies" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_worker_registration_and_heartbeat():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_payload = {
            "hostname": "worker-gpu-node-01",
            "concurrency_slots": 8,
            "supported_task_types": ["ai_inference", "video_encode"],
            "ip_address": "10.0.1.50",
        }
        reg_res = await client.post("/api/v1/batch/workers/register", json=reg_payload)
        assert reg_res.status_code == 201
        worker_id = reg_res.json()["worker"]["id"]

        # List workers
        list_res = await client.get("/api/v1/batch/workers")
        assert list_res.status_code == 200
        assert list_res.json()["total"] == 1

        # Send heartbeat
        hb_res = await client.post(
            f"/api/v1/batch/workers/{worker_id}/heartbeat",
            json={"cpu_usage_percent": 45.2, "memory_usage_mb": 1024.0},
        )
        assert hb_res.status_code == 200
        assert hb_res.json()["status"] == "HEARTBEAT_ACK"
        assert hb_res.json()["worker"]["cpu_usage_percent"] == 45.2


@pytest.mark.asyncio
async def test_dlq_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        engine = get_default_batch_engine()
        # Manually seed a task and send to DLQ
        job = await engine.submit_job("DLQ Seed Job")
        task = await engine.submit_job("Failed Task")
        tasks = [t for t in engine._tasks.values() if t.job_id == job.id]
        if not tasks:
            from apps.api.db.models.batch_task import BatchTask
            task_obj = BatchTask(job_id=job.id, name="faulty_task", tenant_id="ws-alpha-001", error_message="DB Conn Timeout")
            engine._tasks[task_obj.id] = task_obj
            dlq_rec = await engine._send_to_dlq(task_obj)
        else:
            dlq_rec = await engine._send_to_dlq(tasks[0])

        # List DLQ
        dlq_list = await client.get("/api/v1/batch/dlq")
        assert dlq_list.status_code == 200
        assert dlq_list.json()["total"] >= 1

        # Replay DLQ task
        replay_res = await client.post(f"/api/v1/batch/dlq/{dlq_rec.id}/replay")
        assert replay_res.status_code == 200
        assert replay_res.json()["status"] == "REPLAYED"


@pytest.mark.asyncio
async def test_batch_metrics_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/batch/metrics")
        assert res.status_code == 200
        metrics = res.json()["metrics"]
        assert "total_jobs" in metrics
        assert "active_workers_count" in metrics
        assert "capacity_utilization_pct" in metrics
