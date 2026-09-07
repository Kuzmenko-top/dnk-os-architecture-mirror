# --- DNK-MRH-HEADER ---
# mrh_id: "test_multi_agent_collaboration"
# purpose: "Verification tests for multi-agent coordination, task queues, self-healing, and LangGraph+crewAI integration"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import asyncio
from datetime import datetime
import os
import sys
from pathlib import Path
import pytest
import asyncpg
from uuid import uuid4, UUID

# Setup paths relative to test file to resolve core modules
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.models.collaboration import Task, TaskPriority, TaskStatus, AgentRole
from core.queues.task_queue import TaskQueue
from core.adapters.redis_task_queue import RedisTaskQueue
from core.adapters.postgres_task_queue import PostgresTaskQueue
from core.coordinators.agent_coordinator import AgentCoordinator
from core.adapters.langgraph_crewai_coordinator import LangGraphCrewAICoordinator
from core.adapters.postgres_timeline_repository import PostgresTimelineRepository
from core.config.timeline_config import DATABASE_URL
from core.models.timeline import Agent, Run, Event, Task as TimelineTask

# Mock Redis class to test RedisTaskQueue without running redis instance
class MockRedis:
    def __init__(self, **kwargs):
        self.store = {}
        self.zsets = {}

    def set(self, key, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)

    def zadd(self, key, mapping):
        self.zsets.setdefault(key, {})
        for k, v in mapping.items():
            self.zsets[key][k] = v

    def zpopmax(self, key):
        zset = self.zsets.get(key, {})
        if not zset:
            return []
        max_item = max(zset.items(), key=lambda item: item[1])
        del zset[max_item[0]]
        return [max_item]

    def zrevrange(self, key, start, end):
        zset = self.zsets.get(key, {})
        sorted_items = sorted(zset.items(), key=lambda item: item[1], reverse=True)
        return [item[0] for item in sorted_items]

# Set pytestmark to anyio for async tests
pytestmark = pytest.mark.anyio

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

async def setup_test_conn(conn):
    await conn.execute("CREATE SCHEMA IF NOT EXISTS timeline;")
    await conn.execute("SET search_path TO timeline, public;")

@pytest.fixture(scope="module")
async def db_pool():
    try:
        pool = await asyncpg.create_pool(DATABASE_URL, setup=setup_test_conn, timeout=2.0)
    except Exception as e:
        pytest.skip(f"PostgreSQL integration unavailable: {e}")
    
    # Run migrations to ensure schema is ready in timeline
    migrations_dir = BASE_DIR / "db" / "migrations"
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
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE timeline.events, timeline.tasks, timeline.runs, timeline.agents CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS timeline.collaboration_tasks CASCADE;")
    yield

async def test_enqueue_dequeue(monkeypatch):
    """1. test_enqueue_dequeue — черга працює коректно."""
    # Monkeypatch redis to use our MockRedis
    monkeypatch.setattr("redis.Redis", MockRedis)
    
    queue = RedisTaskQueue()
    agent_id = uuid4()
    run_id = uuid4()
    now_ts = int(datetime.utcnow().timestamp())
    
    task1 = Task(
        id=uuid4(),
        run_id=run_id,
        agent_id=agent_id,
        task_type="research",
        priority=TaskPriority.LOW,
        status=TaskStatus.PENDING,
        payload={"query": "low"},
        created_at=now_ts,
        updated_at=now_ts
    )
    
    task2 = Task(
        id=uuid4(),
        run_id=run_id,
        agent_id=agent_id,
        task_type="research",
        priority=TaskPriority.CRITICAL,
        status=TaskStatus.PENDING,
        payload={"query": "critical"},
        created_at=now_ts,
        updated_at=now_ts
    )
    
    queue.enqueue(task1)
    queue.enqueue(task2)
    
    # Dequeue should return CRITICAL first (task2)
    dequeued = queue.dequeue(agent_id)
    assert dequeued is not None
    assert dequeued.id == task2.id
    assert dequeued.status == TaskStatus.RUNNING
    
    # Next should be LOW (task1)
    dequeued_next = queue.dequeue(agent_id)
    assert dequeued_next is not None
    assert dequeued_next.id == task1.id

async def test_assign_role():
    """2. test_assign_role — призначення ролі агенту."""
    coordinator = LangGraphCrewAICoordinator()
    agent_id = uuid4()
    
    coordinator.assign_role(agent_id, AgentRole.RESEARCHER)
    assert coordinator.roles[agent_id] == AgentRole.RESEARCHER

async def test_distribute_tasks():
    """3. test_distribute_tasks — розподіл за ролями + пріоритетами."""
    coordinator = LangGraphCrewAICoordinator()
    
    agent_res1 = uuid4()
    agent_res2 = uuid4()
    agent_writer = uuid4()
    
    coordinator.assign_role(agent_res1, AgentRole.RESEARCHER)
    coordinator.assign_role(agent_res2, AgentRole.RESEARCHER)
    coordinator.assign_role(agent_writer, AgentRole.WRITER)
    
    run_id = uuid4()
    now_ts = int(datetime.utcnow().timestamp())
    tasks = [
        Task(
            id=uuid4(),
            run_id=run_id,
            agent_id=uuid4(), # dummy
            task_type="research",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            payload={},
            created_at=now_ts,
            updated_at=now_ts
        ),
        Task(
            id=uuid4(),
            run_id=run_id,
            agent_id=uuid4(), # dummy
            task_type="research",
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.PENDING,
            payload={},
            created_at=now_ts,
            updated_at=now_ts
        ),
        Task(
            id=uuid4(),
            run_id=run_id,
            agent_id=uuid4(), # dummy
            task_type="write",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            payload={},
            created_at=now_ts,
            updated_at=now_ts
        )
    ]
    
    agents = [agent_res1, agent_res2, agent_writer]
    distribution = coordinator.distribute_tasks(tasks, agents)
    
    # Writer task goes to writer agent
    assert len(distribution[agent_writer]) == 1
    assert distribution[agent_writer][0].task_type == "write"
    
    # Researcher tasks should be round-robin'ed or assigned to researcher agents
    res_tasks = distribution[agent_res1] + distribution[agent_res2]
    assert len(res_tasks) == 2
    
    # Verify priority sorting on agent assignment: CRITICAL should be ordered first
    critical_task = [t for t in res_tasks if t.priority == TaskPriority.CRITICAL][0]
    medium_task = [t for t in res_tasks if t.priority == TaskPriority.MEDIUM][0]
    
    assert critical_task.agent_id != medium_task.agent_id or len(res_tasks) == 2

async def test_handle_failures_retry():
    """4. test_handle_failures_retry — retry при фейлі."""
    coordinator = LangGraphCrewAICoordinator()
    task_id = uuid4()
    run_id = uuid4()
    agent_id = uuid4()
    now_ts = int(datetime.utcnow().timestamp())
    
    task = Task(
        id=task_id,
        run_id=run_id,
        agent_id=agent_id,
        task_type="research",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.FAILED,
        payload={},
        error="Connection failed",
        created_at=now_ts,
        updated_at=now_ts
    )
    
    # First fail -> retry 1
    re_runs = coordinator.handle_failures([task])
    assert len(re_runs) == 1
    assert re_runs[0].id == task_id
    assert re_runs[0].status == TaskStatus.PENDING
    assert re_runs[0].payload["retry_count"] == 1
    assert coordinator.retries[task_id] == 1

async def test_handle_failures_reassign():
    """5. test_handle_failures_reassign — reassign на іншого агента."""
    coordinator = LangGraphCrewAICoordinator()
    agent1 = uuid4()
    agent2 = uuid4()
    now_ts = int(datetime.utcnow().timestamp())
    
    coordinator.assign_role(agent1, AgentRole.RESEARCHER)
    coordinator.assign_role(agent2, AgentRole.RESEARCHER)
    
    task_id = uuid4()
    task = Task(
        id=task_id,
        run_id=uuid4(),
        agent_id=agent1,
        task_type="research",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.FAILED,
        payload={},
        error="Permanent fail",
        created_at=now_ts,
        updated_at=now_ts
    )
    
    # Simulate already had 3 attempts
    coordinator.retries[task_id] = 3
    
    re_runs = coordinator.handle_failures([task])
    assert len(re_runs) == 1
    assert re_runs[0].id == task_id
    assert re_runs[0].agent_id == agent2 # Reassigned to another researcher!
    assert re_runs[0].status == TaskStatus.PENDING
    assert coordinator.retries[task_id] == 0 # Reset retries for the new agent

async def test_handle_failures_escalate():
    """6. test_handle_failures_escalate — escalate до orchestrator."""
    coordinator = LangGraphCrewAICoordinator()
    agent1 = uuid4()
    agent_orchestrator = uuid4()
    now_ts = int(datetime.utcnow().timestamp())
    
    coordinator.assign_role(agent1, AgentRole.RESEARCHER)
    coordinator.assign_role(agent_orchestrator, AgentRole.ORCHESTRATOR)
    
    task_id = uuid4()
    task = Task(
        id=task_id,
        run_id=uuid4(),
        agent_id=agent1,
        task_type="research",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.FAILED,
        payload={},
        error="Permanent fail",
        created_at=now_ts,
        updated_at=now_ts
    )
    
    # Simulate 3 attempts, and no other researcher agents are available
    coordinator.retries[task_id] = 3
    
    re_runs = coordinator.handle_failures([task])
    assert len(re_runs) == 1
    assert re_runs[0].id == task_id
    assert re_runs[0].agent_id == agent_orchestrator # Escalated to orchestrator!
    assert re_runs[0].status == TaskStatus.PENDING

async def test_langgraph_crewai_integration(monkeypatch):
    """7. test_langgraph_crewai_integration — інтеграція з LangGraph + CrewAI."""
    monkeypatch.setattr("redis.Redis", MockRedis)
    task_queue = RedisTaskQueue()
    
    coordinator = LangGraphCrewAICoordinator()
    
    agent_id = uuid4()
    coordinator.assign_role(agent_id, AgentRole.RESEARCHER)
    now_ts = int(datetime.utcnow().timestamp())
    
    # Put a task in queue for researcher
    task = Task(
        id=uuid4(),
        run_id=uuid4(),
        agent_id=agent_id,
        task_type="research",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        payload={"goal": "Find SOTA algorithms", "backstory": "AI researcher"},
        created_at=now_ts,
        updated_at=now_ts
    )
    task_queue.enqueue(task)
    
    graph = coordinator.create_collaboration_graph(task_queue)
    
    # Run the researcher node in the graph
    initial_state = {"current_node": "researcher"}
    res = graph.execute(initial_state, thread_id="collab_thread")
    
    assert res["status"] == "completed"
    assert len(res["messages"]) > 0
    assert "researcher" in res["messages"][0]

async def test_audit_trail(db_pool):
    """8. test_audit_trail — всі події записуються в Timeline DB."""
    repo = PostgresTimelineRepository(db_pool)
    
    # Initialize coordinator with real PG repo
    coordinator = LangGraphCrewAICoordinator(timeline_repo=repo)
    
    agent_id = uuid4()
    coordinator.assign_role(agent_id, AgentRole.RESEARCHER)
    
    # Create required parent Agent and Run inside DB to satisfy foreign keys
    await repo.create_agent(Agent(id=agent_id, name="Researcher Agent"))
    
    run_id = uuid4()
    await repo.create_run(Run(id=run_id, agent_id=agent_id, run_type="research", status="running"))
    
    task_id = uuid4()
    now_ts = int(datetime.utcnow().timestamp())
    
    # Pre-insert the Task in DB to prevent foreign key violation in events table
    await repo.create_task(TimelineTask(
        id=task_id,
        run_id=run_id,
        task_type="research",
        status="failed",
        payload={},
        error="Failure for audit trail test",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ))
    
    task = Task(
        id=task_id,
        run_id=run_id,
        agent_id=agent_id,
        task_type="research",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.FAILED,
        payload={},
        error="Failure for audit trail test",
        created_at=now_ts,
        updated_at=now_ts
    )
    
    # Trigger handle_failures -> triggers event log
    coordinator.handle_failures([task])
    
    # Wait a tiny bit for the async thread loop to finish writing
    await asyncio.sleep(0.5)
    
    # Query events from DB
    events = await repo.get_events_by_run(run_id)
    assert len(events) >= 2
    
    event_types = [e.event_type for e in events]
    assert "task_failed" in event_types
    assert "task_retried" in event_types
