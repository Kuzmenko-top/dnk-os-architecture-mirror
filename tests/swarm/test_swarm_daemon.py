# --- DNK-MRH-HEADER ---
# mrh_id: "tests/swarm/test_swarm_daemon.py"
# purpose: "Unit tests verifying SwarmDaemon parallel DAG execution, dependency resolution, and worker logging."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import pytest
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

from scripts.system.swarm_daemon import (
    SwarmDaemon,
    SwarmExecutionPlan,
    SwarmTask,
    TaskState,
)


@pytest.mark.asyncio
async def test_swarm_daemon_parallel_dag_execution():
    daemon = SwarmDaemon(max_concurrency=4)

    plan = SwarmExecutionPlan(
        plan_id="plan-test-001",
        workspace_id="ws-alpha-001",
        tasks={
            "task_cmo": SwarmTask(
                task_id="task_cmo",
                name="Marketing Copy",
                target_agent="dnk_marketing_cmo",
                payload={"product": "DNK Ergo Chair"},
            ),
            "task_shopify": SwarmTask(
                task_id="task_shopify",
                name="Shopify PDP",
                target_agent="dnk_shopify",
                dependencies=["task_cmo"],
            ),
            "task_video": SwarmTask(
                task_id="task_video",
                name="Video Reel",
                target_agent="dnk_video_ai_creator",
                dependencies=["task_cmo"],
            ),
            "task_cfo": SwarmTask(
                task_id="task_cfo",
                name="Financial Analysis",
                target_agent="dnk_finance_cfo",
                dependencies=["task_shopify", "task_video"],
            ),
            "task_auditor": SwarmTask(
                task_id="task_auditor",
                name="Quality Audit",
                target_agent="gerych_auditor",
                dependencies=["task_cfo"],
            ),
        },
    )

    result = await daemon.execute_plan(plan)

    # 1. Verification of Execution Plan
    assert result.success is True
    assert result.total_tasks == 5
    assert result.completed_tasks == 5
    assert result.failed_tasks == 0
    assert result.elapsed_seconds < 2.0

    # 2. Check each task state
    for t_id, task in plan.tasks.items():
        assert task.state == TaskState.COMPLETED
        assert task.result is not None
        assert task.execution_time_seconds >= 0.0

    # 3. Timeline event sequence
    assert len(result.timeline) == 10  # 5 tasks x 2 (RUNNING + COMPLETED)
    running_events = [e for e in result.timeline if e["state"] == "RUNNING"]
    assert len(running_events) == 5


@pytest.mark.asyncio
async def test_swarm_daemon_custom_handlers():
    daemon = SwarmDaemon()

    executed_agents = []

    async def custom_builder(payload):
        executed_agents.append("builder")
        return {"code": "export const App = () => null;"}

    async def custom_auditor(payload):
        executed_agents.append("auditor")
        return {"lint": "clean", "passed": True}

    plan = SwarmExecutionPlan(
        plan_id="plan-custom-002",
        tasks={
            "t1": SwarmTask(task_id="t1", name="Build UI", target_agent="gerych_builder"),
            "t2": SwarmTask(task_id="t2", name="Audit UI", target_agent="gerych_auditor", dependencies=["t1"]),
        },
    )

    handlers = {
        "gerych_builder": custom_builder,
        "gerych_auditor": custom_auditor,
    }

    result = await daemon.execute_plan(plan, custom_handlers=handlers)
    assert result.success is True
    assert executed_agents == ["builder", "auditor"]
    assert result.results["t1"]["code"] == "export const App = () => null;"
    assert result.results["t2"]["passed"] is True
