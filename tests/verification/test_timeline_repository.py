# --- DNK-MRH-HEADER ---
# mrh_id: "test_timeline_repository"
# purpose: "Automated verification test suite for PostgresTimelineRepository and Idempotency logic with schema isolation"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import asyncio
from datetime import datetime
import json
import os
import pathlib
import pytest
import asyncpg
from uuid import uuid4

from core.config.timeline_config import DATABASE_URL, MAX_PAYLOAD_SIZE
from core.models.timeline import Agent, Run, Task, Event
from core.adapters.postgres_timeline_repository import PostgresTimelineRepository

# Mark all tests in this module as async
pytestmark = pytest.mark.anyio

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

async def setup_test_conn(conn):
    # Enforce test schema isolation to avoid collision with existing public tables
    await conn.execute("CREATE SCHEMA IF NOT EXISTS timeline;")
    await conn.execute("SET search_path TO timeline, public;")

@pytest.fixture(scope="module")
async def db_pool():
    # Setup connection pool with isolated schema initializer
    try:
        pool = await asyncpg.create_pool(DATABASE_URL, setup=setup_test_conn, timeout=2.0)
    except Exception as e:
        pytest.skip(f"PostgreSQL integration unavailable: {e}")
    
    # Run migrations to ensure schema is ready in timeline
    migrations_dir = pathlib.Path(__file__).resolve().parents[2] / "db" / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    async with pool.acquire() as conn:
        for m_file in migration_files:
            sql = m_file.read_text(encoding="utf-8")
            try:
                await conn.execute(sql)
            except Exception as e:
                if "vector" in str(e).lower() and m_file.name == "006_create_knowledge_table.sql":
                    continue
                await pool.close()
                pytest.skip(f"PostgreSQL migration failed: {e}")
            
    yield pool
    
    # Tear down test schema after testing
    async with pool.acquire() as conn:
        await conn.execute("DROP SCHEMA IF EXISTS timeline CASCADE;")
        
    await pool.close()

@pytest.fixture(autouse=True)
async def clean_tables(db_pool):
    # Clean tables before each test
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE timeline.events, timeline.tasks, timeline.runs, timeline.agents CASCADE;")
    yield

@pytest.fixture
def repo(db_pool):
    return PostgresTimelineRepository(db_pool)

async def test_create_agent(repo):
    agent_id = uuid4()
    agent = Agent(
        id=agent_id,
        name="Test Agent",
        description="A specialized agent for verification tests",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    created = await repo.create_agent(agent)
    assert created.id == agent_id
    assert created.name == "Test Agent"
    
    fetched = await repo.get_agent(agent_id)
    assert fetched is not None
    assert fetched.id == agent_id
    assert fetched.description == "A specialized agent for verification tests"

async def test_create_run(repo):
    # First need an agent
    agent_id = uuid4()
    agent = Agent(id=agent_id, name="Agent 1")
    await repo.create_agent(agent)
    
    run_id = uuid4()
    run = Run(
        id=run_id,
        agent_id=agent_id,
        run_type="task",
        status="pending",
        idempotency_key="key_123"
    )
    
    created = await repo.create_run(run)
    assert created.id == run_id
    assert created.idempotency_key == "key_123"
    
    fetched = await repo.get_run(run_id)
    assert fetched is not None
    assert fetched.id == run_id
    assert fetched.idempotency_key == "key_123"
    
    # Verify idempotency key uniqueness returns same run
    run_dup = Run(
        id=uuid4(),
        agent_id=agent_id,
        run_type="task",
        status="running",
        idempotency_key="key_123"
    )
    created_dup = await repo.create_run(run_dup)
    assert created_dup.id == run_id  # Should return original run ID!
    assert created_dup.status == "pending"  # original status

    # Query runs by agent
    runs = await repo.get_runs_by_agent(agent_id)
    assert len(runs) == 1
    assert runs[0].id == run_id

async def test_create_task(repo):
    # First need agent and run
    agent_id = uuid4()
    agent = Agent(id=agent_id, name="Agent 1")
    await repo.create_agent(agent)
    
    run_id = uuid4()
    run = Run(id=run_id, agent_id=agent_id, run_type="research", status="running")
    await repo.create_run(run)
    
    task_id = uuid4()
    task = Task(
        id=task_id,
        run_id=run_id,
        task_type="research",
        status="running",
        payload={"query": "SOTA FastMCP patterns"},
        result={"status": "success", "count": 42}
    )
    
    created = await repo.create_task(task)
    assert created.id == task_id
    assert created.payload == {"query": "SOTA FastMCP patterns"}
    assert created.result == {"status": "success", "count": 42}
    
    fetched = await repo.get_task(task_id)
    assert fetched is not None
    assert fetched.id == task_id
    assert fetched.payload == {"query": "SOTA FastMCP patterns"}
    
    tasks = await repo.get_tasks_by_run(run_id)
    assert len(tasks) == 1
    assert tasks[0].id == task_id

async def test_create_event(repo):
    agent_id = uuid4()
    agent = Agent(id=agent_id, name="Agent 1")
    await repo.create_agent(agent)
    
    run_id = uuid4()
    run = Run(id=run_id, agent_id=agent_id, run_type="orchestration", status="running")
    await repo.create_run(run)
    
    task_id = uuid4()
    task = Task(id=task_id, run_id=run_id, task_type="write", status="pending")
    await repo.create_task(task)
    
    event_id = uuid4()
    event = Event(
        id=event_id,
        run_id=run_id,
        task_id=task_id,
        event_type="task_completed",
        payload={"step": 2, "time_spent_ms": 150}
    )
    
    created = await repo.create_event(event)
    assert created.id == event_id
    assert created.event_type == "task_completed"
    assert created.payload == {"step": 2, "time_spent_ms": 150}
    
    events_run = await repo.get_events_by_run(run_id)
    assert len(events_run) == 1
    assert events_run[0].id == event_id
    
    events_task = await repo.get_events_by_task(task_id)
    assert len(events_task) == 1
    assert events_task[0].id == event_id

async def test_create_duplicate_event(repo):
    agent_id = uuid4()
    agent = Agent(id=agent_id, name="Agent 1")
    await repo.create_agent(agent)
    
    run_id = uuid4()
    run = Run(id=run_id, agent_id=agent_id, run_type="orchestration", status="running")
    await repo.create_run(run)
    
    event_id = uuid4()
    event1 = Event(
        id=event_id,
        run_id=run_id,
        event_type="heartbeat",
        payload={"count": 1}
    )
    event2 = Event(
        id=event_id,
        run_id=run_id,
        event_type="heartbeat",
        payload={"count": 2}
    )
    
    res1 = await repo.create_event(event1)
    res2 = await repo.create_event(event2)
    
    assert res1.id == event_id
    assert res2.id == event_id
    assert res1.payload == {"count": 1}
    assert res2.payload == {"count": 1} # Verify ON CONFLICT DO NOTHING returns existing event payload!

async def test_concurrent_writes(repo):
    agent_id = uuid4()
    agent = Agent(id=agent_id, name="Agent 1")
    await repo.create_agent(agent)
    
    # Create two identical runs concurrently
    idempotency_key = f"concurrent_key_{uuid4()}"
    run1 = Run(id=uuid4(), agent_id=agent_id, run_type="task", status="pending", idempotency_key=idempotency_key)
    run2 = Run(id=uuid4(), agent_id=agent_id, run_type="task", status="running", idempotency_key=idempotency_key)
    
    # Run concurrently using asyncio.gather
    res1, res2 = await asyncio.gather(
        repo.create_run(run1),
        repo.create_run(run2)
    )
    
    # Both must succeed and return the SAME run object ID
    assert res1.id == res2.id
    assert res1.idempotency_key == idempotency_key
    assert res2.idempotency_key == idempotency_key

async def test_payload_sanitization(repo):
    agent_id = uuid4()
    agent = Agent(id=agent_id, name="Agent 1")
    await repo.create_agent(agent)
    
    run_id = uuid4()
    run = Run(id=run_id, agent_id=agent_id, run_type="task", status="running")
    await repo.create_run(run)
    
    # Test secret sanitization
    task_secrets = Task(
        id=uuid4(),
        run_id=run_id,
        task_type="api_call",
        status="pending",
        payload={
            "api_key": "sk-real-secret",
            "password": "real-password",
            "safe_field": "public_data",
            "nested": {
                "token": "sensitive_nested_token",
                "normal": 42
            }
        }
    )
    
    created = await repo.create_task(task_secrets)
    assert created.payload["api_key"] == "***"
    assert created.payload["password"] == "***"
    assert created.payload["safe_field"] == "public_data"
    assert created.payload["nested"]["token"] == "***"
    assert created.payload["nested"]["normal"] == 42
    
    # Small payload should succeed
    task_ok = Task(
        id=uuid4(),
        run_id=run_id,
        task_type="validate",
        status="pending",
        payload={"valid": True}
    )
    assert (await repo.create_task(task_ok)) is not None
    
    # Huge payload should raise ValueError
    large_payload = {"data": "X" * (MAX_PAYLOAD_SIZE + 10)}
    task_huge = Task(
        id=uuid4(),
        run_id=run_id,
        task_type="validate",
        status="pending",
        payload=large_payload
    )
    
    with pytest.raises(ValueError) as excinfo:
        await repo.create_task(task_huge)
    assert "Payload size exceeds" in str(excinfo.value)
    
    # Huge event payload should also raise ValueError
    event_huge = Event(
        id=uuid4(),
        run_id=run_id,
        event_type="error",
        payload=large_payload
    )
    
    with pytest.raises(ValueError) as excinfo:
        await repo.create_event(event_huge)
    assert "Payload size exceeds" in str(excinfo.value)
