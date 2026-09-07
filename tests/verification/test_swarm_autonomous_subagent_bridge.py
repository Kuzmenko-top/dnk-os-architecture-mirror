# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_swarm_autonomous_subagent_bridge.py"
# purpose: "Verification of Autonomous Subagent Execution & Artifact Mailbox Bridge."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
from unittest.mock import patch
from core.orchestrator.swarm_coordinator import swarm_coordinator
from core.hermes_agent.tools.dnk_swarm_tool import dnk_swarm_dispatch


def test_swarm_coordinator_autonomous_subagent_routing():
    """Verify that mode='autonomous_subagent' calls _execute_headless_subagent and records artifacts."""
    with patch.object(swarm_coordinator, "_execute_headless_subagent") as mock_headless:
        mock_headless.return_value = {
            "agent": "gerych_builder",
            "action": "execute",
            "execution_mode": "autonomous_subagent",
            "status": "completed",
            "artifact_path": "data/swarm_artifacts/artifact_gerych_builder_123.json"
        }

        task = {
            "agent": "gerych_builder",
            "action": "build_component",
            "mode": "autonomous_subagent",
            "timeout_seconds": 60,
            "payload": {
                "task_description": "Build Canvas header",
                "target_files": ["apps/web/src/Header.tsx"]
            }
        }

        res = swarm_coordinator.dispatch_parallel([task])
        assert res["status"] == "parallel_batch_completed"
        assert res["task_count"] == 1
        assert len(res["completed_tasks"]) == 1
        completed = res["completed_tasks"][0]
        assert completed["agent"] == "gerych_builder"
        assert completed["outcome"]["status"] == "completed"
        assert completed["outcome"]["execution_mode"] == "autonomous_subagent"
        mock_headless.assert_called_once()


def test_dnk_swarm_dispatch_forwards_mode_and_target_files():
    """Verify that dnk_swarm_dispatch forwards mode and target_files to SwarmCoordinator."""
    with patch.object(swarm_coordinator, "dispatch_parallel") as mock_dispatch:
        mock_dispatch.return_value = {
            "status": "parallel_batch_completed",
            "task_count": 1,
            "completed_tasks": [{
                "agent": "dnk_dev_fullstack",
                "action": "scaffold_api",
                "outcome": {
                    "execution_mode": "autonomous_subagent",
                    "status": "completed",
                    "artifact_path": "data/swarm_artifacts/artifact_dnk_dev_fullstack_456.json"
                }
            }]
        }

        res_json = dnk_swarm_dispatch(
            agent="dnk_dev_fullstack",
            task_description="Scaffold auth endpoints",
            mode="autonomous_subagent",
            parameters={
                "action": "scaffold_api",
                "target_files": ["apps/api/routers/auth.py"],
                "timeout_seconds": 90
            }
        )

        res = json.loads(res_json)
        assert res["status"] == "success"
        assert res["agent"] == "dnk_dev_fullstack"
        assert res["outcome"]["status"] == "completed"
        assert res["outcome"]["artifact_path"] == "data/swarm_artifacts/artifact_dnk_dev_fullstack_456.json"

        mock_dispatch.assert_called_once()
        sent_tasks = mock_dispatch.call_args[0][0]
        assert len(sent_tasks) == 1
        sent_task = sent_tasks[0]
        assert sent_task["agent"] == "dnk_dev_fullstack"
        assert sent_task["action"] == "scaffold_api"
        assert sent_task["mode"] == "autonomous_subagent"
        assert sent_task["timeout_seconds"] == 90
        assert sent_task["payload"]["target_files"] == ["apps/api/routers/auth.py"]
