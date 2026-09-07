# --- DNK-MRH-HEADER ---
# mrh_id: "test_security_gate"
# purpose: "Automated verification test suite for SecurityGateService and @security_gate decorator"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import asyncio
import time
from uuid import uuid4, UUID
import pytest
import asyncpg
import pathlib

from core.models.security import SecurityPolicy, GateDecision
from core.models.timeline import Agent, Run
from core.ports.timeline_repository import ITimelineRepository
from core.adapters.postgres_timeline_repository import PostgresTimelineRepository
from core.adapters.security_gate_timeline_adapter import SecurityGateTimelineAdapter
from core.services.security_gate_service import InlineSecurityGateService
from core.decorators.security_gate import (
    security_gate,
    set_security_gate_service,
    get_security_gate_service,
    SecurityGateDenied
)
from core.config.timeline_config import DATABASE_URL

# Mark all tests as async/anyio
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
    
    async with pool.acquire() as conn:
        await conn.execute("DROP SCHEMA IF EXISTS timeline CASCADE;")
    await pool.close()

@pytest.fixture(autouse=True)
async def clean_tables(db_pool):
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE timeline.events, timeline.tasks, timeline.runs, timeline.agents CASCADE;")
    yield

@pytest.fixture
def timeline_repo(db_pool):
    return PostgresTimelineRepository(db_pool)

@pytest.fixture
def timeline_adapter(timeline_repo):
    return SecurityGateTimelineAdapter(timeline_repo)

@pytest.fixture
def gate_service(timeline_adapter):
    return InlineSecurityGateService(timeline_adapter)

# Ensure our service is registered in the decorator registry before each test
@pytest.fixture(autouse=True)
def register_service(gate_service):
    set_security_gate_service(gate_service)
    yield
    # restore fallback
    set_security_gate_service(None)


async def create_agent_and_run(timeline_repo: ITimelineRepository) -> UUID:
    agent_id = uuid4()
    agent = Agent(id=agent_id, name="Security Test Agent")
    await timeline_repo.create_agent(agent)
    
    run_id = uuid4()
    run = Run(id=run_id, agent_id=agent_id, run_type="security_test", status="running")
    await timeline_repo.create_run(run)
    return run_id


async def test_evaluate_policy_allowed(gate_service, timeline_repo):
    policy_id = uuid4()
    policy = SecurityPolicy(
        id=policy_id,
        name="Allow write under 100 bytes",
        action_patterns=["file.write"],
        conditions={"max_file_size": 100},
        require_approval=False,
        created_at=int(time.time()),
        updated_at=int(time.time())
    )
    gate_service.create_policy(policy)
    
    run_id = await create_agent_and_run(timeline_repo)
    
    # 50 bytes content -> allowed
    decision = gate_service.evaluate_policy(
        run_id=run_id,
        action="file.write",
        arguments={"path": "test.txt", "content": "A" * 50},
        context={}
    )
    assert decision.allowed is True
    assert "allowed" in decision.reason


async def test_evaluate_policy_denied(gate_service, timeline_repo):
    policy_id = uuid4()
    policy = SecurityPolicy(
        id=policy_id,
        name="Allow write under 100 bytes",
        action_patterns=["file.write"],
        conditions={"max_file_size": 100},
        require_approval=False,
        created_at=int(time.time()),
        updated_at=int(time.time())
    )
    gate_service.create_policy(policy)
    
    run_id = await create_agent_and_run(timeline_repo)
    
    # 150 bytes content -> denied
    decision = gate_service.evaluate_policy(
        run_id=run_id,
        action="file.write",
        arguments={"path": "test.txt", "content": "A" * 150},
        context={}
    )
    assert decision.allowed is False
    assert "exceeds policy limit" in decision.reason


async def test_evaluate_policy_require_approval(gate_service, timeline_repo):
    policy_id = uuid4()
    policy = SecurityPolicy(
        id=policy_id,
        name="Require manual approval on delete",
        action_patterns=["db.delete"],
        conditions={},
        require_approval=True,
        created_at=int(time.time()),
        updated_at=int(time.time())
    )
    gate_service.create_policy(policy)
    
    run_id = await create_agent_and_run(timeline_repo)
    
    decision = gate_service.evaluate_policy(
        run_id=run_id,
        action="db.delete",
        arguments={"table": "users", "id": "123"},
        context={}
    )
    assert decision.allowed is False
    assert "Manual approval required" in decision.reason
    assert decision.approval_run_id == run_id


async def test_decorator_allowed(gate_service, timeline_repo):
    policy_id = uuid4()
    policy = SecurityPolicy(
        id=policy_id,
        name="Allow write under 100 bytes",
        action_patterns=["file.write"],
        conditions={"max_file_size": 100},
        require_approval=False,
        created_at=int(time.time()),
        updated_at=int(time.time())
    )
    gate_service.create_policy(policy)
    
    run_id = await create_agent_and_run(timeline_repo)

    # Wrapped sync function
    @security_gate(action="file.write")
    def sync_write(run_id, path: str, content: str):
        return "sync_ok"

    # Wrapped async function
    @security_gate(action="file.write")
    async def async_write(run_id, path: str, content: str):
        return "async_ok"

    # Try sync call
    res_sync = sync_write(run_id, "test.txt", "A" * 50)
    assert res_sync == "sync_ok"

    # Try async call
    res_async = await async_write(run_id, "test.txt", "A" * 50)
    assert res_async == "async_ok"


async def test_decorator_denied(gate_service, timeline_repo):
    policy_id = uuid4()
    policy = SecurityPolicy(
        id=policy_id,
        name="Block any db deletion",
        action_patterns=["db.*"],
        conditions={},
        require_approval=True,
        created_at=int(time.time()),
        updated_at=int(time.time())
    )
    gate_service.create_policy(policy)
    
    run_id = await create_agent_and_run(timeline_repo)

    @security_gate(action="db.drop")
    def sync_drop(run_id, table: str):
        return "dropped"

    @security_gate(action="db.drop")
    async def async_drop(run_id, table: str):
        return "dropped"

    with pytest.raises(SecurityGateDenied) as exc_sync:
        sync_drop(run_id, "users")
    assert "Manual approval required" in str(exc_sync.value)

    with pytest.raises(SecurityGateDenied) as exc_async:
        await async_drop(run_id, "users")
    assert "Manual approval required" in str(exc_async.value)


async def test_fail_closed():
    # Force get_security_gate_service to return None or fail
    set_security_gate_service(None)
    
    @security_gate(action="file.write")
    def risky_write(path: str, content: str):
        return "written"

    from unittest.mock import patch
    with patch("core.decorators.security_gate.get_security_gate_service", side_effect=RuntimeError("Connection lost")):
        with pytest.raises(SecurityGateDenied) as excinfo:
            risky_write("test.txt", "hello")
        assert "Fail-Closed" in str(excinfo.value)


async def test_idempotency(gate_service, timeline_repo):
    policy_id = uuid4()
    policy = SecurityPolicy(
        id=policy_id,
        name="Allow write under 100 bytes",
        action_patterns=["file.write"],
        conditions={"max_file_size": 100},
        require_approval=False,
        created_at=int(time.time()),
        updated_at=int(time.time())
    )
    gate_service.create_policy(policy)
    
    run_id = await create_agent_and_run(timeline_repo)
    args = {"path": "test.txt", "content": "A" * 50}
    
    # First call - fresh evaluation
    decision_1 = gate_service.evaluate_policy(run_id, "file.write", args, {})
    
    # Second call - same arguments, should retrieve from cache (instant)
    decision_2 = gate_service.evaluate_policy(run_id, "file.write", args, {})
    
    assert decision_1 is decision_2  # Object reference equality due to caching!


async def test_audit_trail(gate_service, timeline_repo):
    policy_id = uuid4()
    policy = SecurityPolicy(
        id=policy_id,
        name="Allow write under 100 bytes",
        action_patterns=["file.write"],
        conditions={"max_file_size": 100},
        require_approval=False,
        created_at=int(time.time()),
        updated_at=int(time.time())
    )
    gate_service.create_policy(policy)
    
    run_id = await create_agent_and_run(timeline_repo)
    args = {"path": "test.txt", "content": "A" * 50}
    
    # Run the evaluation which writes audit trail
    gate_service.evaluate_policy(run_id, "file.write", args, {})
    
    # We must yield a tiny sleep to let the async concurrent logger task complete
    await asyncio.sleep(0.1)
    
    # Query events by run_id
    events = await timeline_repo.get_events_by_run(run_id)
    assert len(events) == 1
    assert events[0].event_type == "security_gate_evaluated"
    assert events[0].payload["allowed"] is True
    assert events[0].payload["action"] == "file.write"
