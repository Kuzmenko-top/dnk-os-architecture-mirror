# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_subagent_sandbox_handshake.py"
# purpose: "Verification of Subagent Sandbox Environment Isolation and Zero-Loss Artifact Handshake."
# canonical_source: false
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import os
import subprocess
from pathlib import Path
import pytest

from core.orchestrator.subagent_sandbox import (
    prepare_subagent_environment,
    get_subagent_context,
    emit_subagent_output,
    harvest_subagent_output,
)
from core.orchestrator.swarm_coordinator import GerychSwarmCoordinator
from core.orchestrator.swarm_ledger import SwarmLedger


def test_prepare_and_get_subagent_context(tmp_path, monkeypatch):
    hub_root = tmp_path
    task_id = "test_subagent_task_123"
    agent = "dnk_dev_fullstack"
    action = "scaffold_api"
    payload = {
        "target_files": ["apps/api/routers/test.py"],
        "task_description": "Build test router",
        "feature_flag": True,
    }
    trace_id = "trace-test-uuid-456"

    env, in_path, out_path = prepare_subagent_environment(
        agent=agent,
        task_id=task_id,
        action=action,
        payload=payload,
        trace_id=trace_id,
        hub_root=hub_root,
        timeout_seconds=60,
    )

    assert in_path.exists()
    assert out_path.name == f"{task_id}_output.json"
    assert env["DNK_TASK_ID"] == task_id
    assert env["DNK_AGENT_ID"] == agent
    assert env["DNK_TRACE_ID"] == trace_id

    # Simulate subagent picking up environment
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    ctx = get_subagent_context()
    assert ctx is not None
    assert ctx.task_id == task_id
    assert ctx.agent_id == agent
    assert ctx.action == action
    assert ctx.trace_id == trace_id
    assert ctx.target_files == ["apps/api/routers/test.py"]
    assert ctx.payload.get("feature_flag") is True


def test_emit_and_harvest_subagent_output(tmp_path, monkeypatch):
    hub_root = tmp_path
    out_dir = hub_root / "data" / "swarm_artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "task_xyz_output.json"

    monkeypatch.setenv("DNK_OUTPUT_ARTIFACT", str(out_file))
    monkeypatch.setenv("DNK_TASK_ID", "task_xyz")
    monkeypatch.setenv("DNK_AGENT_ID", "gerych_builder")

    written_path = emit_subagent_output(
        status="completed",
        data={"components_created": ["CanvasCard.tsx"], "tests_passed": 3},
        modified_files=["apps/web/components/CanvasCard.tsx"],
        summary="Canvas card component built and verified",
    )

    assert written_path == out_file
    assert out_file.exists()

    harvested = harvest_subagent_output(out_file)
    assert harvested["status"] == "completed"
    assert harvested["summary"] == "Canvas card component built and verified"
    assert harvested["modified_files"] == ["apps/web/components/CanvasCard.tsx"]
    assert harvested["data"]["tests_passed"] == 3


def test_coordinator_zero_loss_subagent_handshake(tmp_path, monkeypatch):
    hub_root = tmp_path
    coordinator = GerychSwarmCoordinator()
    coordinator.hub_root = hub_root
    
    # Configure custom agents directory in tmp_path
    fake_agents_dir = hub_root / "core" / "orchestrator" / "agents"
    worker_dir = fake_agents_dir / "dnk_dev_fullstack"
    worker_dir.mkdir(parents=True, exist_ok=True)
    coordinator.agents_dir = fake_agents_dir

    ledger = SwarmLedger()
    coordinator.ledger = ledger

    # Create dummy gerych_swarm.sh script
    scripts_dir = hub_root / "scripts" / "system"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    swarm_script = scripts_dir / "gerych_swarm.sh"
    
    # Script that simulates worker execution and emits output artifact
    swarm_script.write_text(
        "#!/usr/bin/env bash\n"
        "python3 -c '\n"
        "import os, json\n"
        "out_path = os.environ.get(\"DNK_OUTPUT_ARTIFACT\")\n"
        "if out_path:\n"
        "    with open(out_path, \"w\") as f:\n"
        "        json.dump({\"status\": \"completed\", \"summary\": \"Mock worker success\", \"modified_files\": [\"foo.py\"]}, f)\n"
        "'\n"
        "echo 'Worker completed execution successfully'\n"
        "exit 0\n"
    )
    swarm_script.chmod(0o755)

    payload = {
        "task_id": "test_isolated_worker_001",
        "task_description": "Build test API component",
        "target_files": ["apps/api/test_mod.py"],
    }

    result = coordinator._execute_headless_subagent(
        agent="dnk_dev_fullstack",
        action="build_module",
        payload=payload,
        timeout_seconds=30,
        trace_id="test-trace-subagent-999",
    )

    assert result["status"] == "completed"
    assert result["exit_code"] == 0
    assert result["input_artifact"] is not None
    assert result["output_artifact"] is not None
    assert result["structured_output"]["status"] == "completed"
    assert result["structured_output"]["summary"] == "Mock worker success"
    assert "artifact_id" in result

    # Verify mailbox delivery to gerych_prime in ledger
    mailbox = ledger.fetch_mailbox(recipient_agent="gerych_prime")
    assert len(mailbox) >= 1
    delivered = next(m for m in mailbox if m["task_id"] == "test_isolated_worker_001")
    assert delivered["producer_agent"] == "dnk_dev_fullstack"
    assert delivered["recipient_agent"] == "gerych_prime"
