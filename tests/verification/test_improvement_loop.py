# --- DNK-MRH-HEADER ---
# mrh_id: "test_improvement_loop"
# purpose: "Automated verification test suite for the Self-Improvement Loop components (Analyzer, Generator, Executor, Security Gate, and Audit Trail)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import pytest
import asyncpg
import pathlib

from core.models.timeline import Agent, Run, Task, Event
from core.models.improvement import RunAnalysis, ImprovementSuggestion, ImprovementPlan
from core.models.security import SecurityPolicy, GateDecision
from core.adapters.postgres_timeline_repository import PostgresTimelineRepository
from core.analyzers.run_analyzer import PostgresRunAnalyzer
from core.generators.improvement_generator import HeuristicImprovementGenerator
from core.executors.improvement_executor import PostgresImprovementExecutor
from core.services.improvement_security_service import ImprovementSecurityService
from core.services.security_gate_service import InlineSecurityGateService
from core.adapters.security_gate_timeline_adapter import SecurityGateTimelineAdapter
from core.config.timeline_config import DATABASE_URL

# Mark all tests as async
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
def repo(db_pool):
    return PostgresTimelineRepository(db_pool)

@pytest.fixture
def analyzer(repo):
    return PostgresRunAnalyzer(repo)

@pytest.fixture
def generator():
    return HeuristicImprovementGenerator()

@pytest.fixture
def executor(repo):
    return PostgresImprovementExecutor(repo)


async def test_analyze_runs_success_rate(repo, analyzer):
    agent_id = uuid4()
    agent = Agent(id=agent_id, name="Analyzer Agent", description="Verification Agent")
    await repo.create_agent(agent)

    # 3 Completed, 2 Failed runs
    now = datetime.utcnow()
    for i in range(3):
        run = Run(
            id=uuid4(),
            agent_id=agent_id,
            run_type="analysis_test",
            status="completed",
            started_at=now - timedelta(seconds=10),
            completed_at=now,
            created_at=now
        )
        await repo.create_run(run)

    for i in range(2):
        run = Run(
            id=uuid4(),
            agent_id=agent_id,
            run_type="analysis_test",
            status="failed",
            started_at=now - timedelta(seconds=20),
            completed_at=now,
            created_at=now
        )
        await repo.create_run(run)

    analysis: RunAnalysis = await analyzer.analyze_runs(agent_id)
    
    assert analysis.total_runs == 5
    assert analysis.success_rate == 0.6  # 3 / 5
    assert analysis.avg_duration_seconds == 14.0  # (3*10 + 2*20) / 5


async def test_detect_patterns_common_errors(repo, analyzer):
    agent_id = uuid4()
    agent = Agent(id=agent_id, name="Pattern Agent")
    await repo.create_agent(agent)

    run_id = uuid4()
    run = Run(id=run_id, agent_id=agent_id, run_type="pattern_test", status="failed")
    await repo.create_run(run)

    # Add tasks with timeout and rate limit errors
    task1 = Task(
        id=uuid4(),
        run_id=run_id,
        task_type="research",
        status="failed",
        error="TimeoutError: API call timed out after 30 seconds",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    await repo.create_task(task1)

    task2 = Task(
        id=uuid4(),
        run_id=run_id,
        task_type="writing",
        status="failed",
        error="RateLimitError: 429 Too Many Requests",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    await repo.create_task(task2)

    analysis: RunAnalysis = await analyzer.analyze_runs(agent_id)
    
    assert len(analysis.common_errors) == 2
    assert any("TimeoutError" in err for err in analysis.common_errors)
    assert any("RateLimitError" in err for err in analysis.common_errors)

    # Check that analyzer generated category-based suggestions
    categories = [sug.category for sug in analysis.suggestions]
    assert "timeout" in categories
    assert "retry_policy" in categories


async def test_generate_plan_priority(generator):
    suggestions = [
        ImprovementSuggestion(
            category="timeout",
            description="Timeout sug",
            priority="low",
            estimated_impact="medium",
            suggested_action="increase timeout"
        ),
        ImprovementSuggestion(
            category="prompt",
            description="Prompt sug",
            priority="high",
            estimated_impact="high",
            suggested_action="refine prompt"
        ),
        ImprovementSuggestion(
            category="retry_policy",
            description="Retry sug",
            priority="medium",
            estimated_impact="high",
            suggested_action="exponential backoff"
        ),
    ]

    plan: ImprovementPlan = generator.generate_plan(str(uuid4()), suggestions)

    # Assert priority order: high -> medium -> low
    assert plan.improvements[0].priority == "high"
    assert plan.improvements[1].priority == "medium"
    assert plan.improvements[2].priority == "low"
    assert plan.estimated_total_impact == "high"
    assert plan.rollback_plan is not None


async def test_execute_plan_prompt_update(repo, executor):
    agent_id = uuid4()
    run_id = uuid4()

    suggestion = ImprovementSuggestion(
        category="prompt",
        description="Prompt optimization",
        priority="high",
        estimated_impact="high",
        suggested_action="System prompt update text"
    )

    plan = ImprovementPlan(
        agent_id=str(agent_id),
        improvements=[suggestion],
        priority_order=["System prompt update text"],
        estimated_total_impact="high",
        rollback_plan="Git reset"
    )

    # Need to create run first to log events with run_id
    agent = Agent(id=agent_id, name="Test Agent")
    await repo.create_agent(agent)
    run = Run(id=run_id, agent_id=agent_id, run_type="execution_test", status="running")
    await repo.create_run(run)

    success = await executor.execute_plan(plan, run_id)
    assert success is True
    assert executor.agent_configs[str(agent_id)]["prompt"] == "System prompt update text"


async def test_execute_plan_retry_policy_update(repo, executor):
    agent_id = uuid4()
    run_id = uuid4()

    suggestion = ImprovementSuggestion(
        category="retry_policy",
        description="Exponential backoff update",
        priority="medium",
        estimated_impact="medium",
        suggested_action="Use 5 max retries with exponential backoff"
    )

    plan = ImprovementPlan(
        agent_id=str(agent_id),
        improvements=[suggestion],
        priority_order=["Use 5 max retries with exponential backoff"],
        estimated_total_impact="medium",
        rollback_plan="Rollback retry config"
    )

    # Create run first
    agent = Agent(id=agent_id, name="Test Agent")
    await repo.create_agent(agent)
    run = Run(id=run_id, agent_id=agent_id, run_type="execution_test", status="running")
    await repo.create_run(run)

    success = await executor.execute_plan(plan, run_id)
    assert success is True
    assert executor.agent_configs[str(agent_id)]["retry_policy"]["max_retries"] == 5
    assert executor.agent_configs[str(agent_id)]["retry_policy"]["backoff"] == "exponential"


async def test_security_gate_approval_required(repo):
    # Setup Security Gate and Adapter
    timeline_adapter = SecurityGateTimelineAdapter(repo)
    gate_service = InlineSecurityGateService(timeline_adapter)
    sec_service = ImprovementSecurityService(gate_service)

    run_id = uuid4()
    agent_id = uuid4()
    agent = Agent(id=agent_id, name="Security Agent")
    await repo.create_agent(agent)
    run = Run(id=run_id, agent_id=agent_id, run_type="security_test", status="running")
    await repo.create_run(run)

    # High impact should raise PermissionError (approval required)
    sug_high = ImprovementSuggestion(
        category="prompt",
        description="High impact prompt change",
        priority="high",
        estimated_impact="high",
        suggested_action="Rewrite agent core system prompt"
    )
    
    with pytest.raises(PermissionError) as exc_info:
        sec_service.evaluate_improvement(run_id, sug_high)
    assert "Manual approval required" in str(exc_info.value)

    # Low impact with policy restriction requiring approval
    policy_id = uuid4()
    policy = SecurityPolicy(
        id=policy_id,
        name="Require prompt approval",
        action_patterns=["improvement.apply.prompt"],
        conditions={},
        require_approval=True,
        created_at=int(datetime.utcnow().timestamp()),
        updated_at=int(datetime.utcnow().timestamp())
    )
    gate_service.create_policy(policy)

    sug_low = ImprovementSuggestion(
        category="prompt",
        description="Low impact prompt change",
        priority="low",
        estimated_impact="low",
        suggested_action="Minor prompt tweak"
    )

    with pytest.raises(PermissionError) as exc_info:
        sec_service.evaluate_improvement(run_id, sug_low)
    assert "Manual approval required" in str(exc_info.value)


async def test_audit_trail(repo, executor):
    agent_id = uuid4()
    run_id = uuid4()

    suggestion = ImprovementSuggestion(
        category="timeout",
        description="Timeout optimization",
        priority="medium",
        estimated_impact="medium",
        suggested_action="Increase timeout to 60s"
    )

    plan = ImprovementPlan(
        agent_id=str(agent_id),
        improvements=[suggestion],
        priority_order=["Increase timeout to 60s"],
        estimated_total_impact="medium",
        rollback_plan="Git reset"
    )

    agent = Agent(id=agent_id, name="Test Agent")
    await repo.create_agent(agent)
    run = Run(id=run_id, agent_id=agent_id, run_type="execution_test", status="running")
    await repo.create_run(run)

    await executor.execute_plan(plan, run_id)

    # Verify event was recorded in DB
    events = await repo.get_events_by_run(run_id)
    assert len(events) >= 1
    
    applied_event = next(e for e in events if e.event_type == "improvement_applied")
    assert applied_event.payload["agent_id"] == str(agent_id)
    assert applied_event.payload["category"] == "timeout"
    assert applied_event.payload["improvement"] == "Increase timeout to 60s"
