# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_subagent_sandbox.py"
# purpose: "Unit tests for subagent environment preparation, context retrieval, and artifact handshake."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from pathlib import Path
from core.orchestrator.subagent_sandbox import (
    prepare_subagent_environment,
    get_subagent_context,
    emit_subagent_output,
    harvest_subagent_output,
)


def test_prepare_and_harvest_subagent_environment(tmp_path: Path):
    hub_root = tmp_path
    agent = "dnk_dev_fullstack"
    task_id = "task_test_001"
    action = "build_component"
    payload = {"target_files": ["apps/web/test.tsx"], "goal": "test goal"}
    trace_id = "trace-test-123"

    env, in_art, out_art = prepare_subagent_environment(
        agent=agent,
        task_id=task_id,
        action=action,
        payload=payload,
        trace_id=trace_id,
        hub_root=hub_root,
        timeout_seconds=60,
    )

    assert env["DNK_SWARM_WORKER"] == "1"
    assert env["DNK_AGENT_ID"] == agent
    assert env["DNK_TASK_ID"] == task_id
    assert env["DNK_TRACE_ID"] == trace_id
    assert in_art.exists()

    # Simulate subagent context reading
    orig_env = os.environ.copy()
    try:
        os.environ.update(env)
        ctx = get_subagent_context()
        assert ctx is not None
        assert ctx.agent_id == agent
        assert ctx.task_id == task_id
        assert ctx.action == action
        assert ctx.target_files == ["apps/web/test.tsx"]
        assert ctx.timeout_seconds == 60

        # Simulate subagent output emission
        emitted_path = emit_subagent_output(
            status="completed",
            data={"result": "ok"},
            modified_files=["apps/web/test.tsx"],
            summary="Component built",
        )
        assert emitted_path is not None
        assert emitted_path.exists()

        # Harvest output
        harvested = harvest_subagent_output(out_art)
        assert harvested["status"] == "completed"
        assert harvested["summary"] == "Component built"
        assert harvested["modified_files"] == ["apps/web/test.tsx"]
        assert harvested["data"]["result"] == "ok"
    finally:
        os.environ.clear()
        os.environ.update(orig_env)


def test_get_subagent_context_none_when_not_in_worker():
    orig_env = os.environ.copy()
    try:
        os.environ.pop("DNK_SWARM_WORKER", None)
        ctx = get_subagent_context()
        assert ctx is None
    finally:
        os.environ.clear()
        os.environ.update(orig_env)
