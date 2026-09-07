# --- DNK-MRH-HEADER ---
# mrh_id: "core/agent_factory/prime_engine/tests/test_prime_orchestrator.py"
# purpose: "Unit tests for SwarmDispatcher and GerychPrimeOrchestrator."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from core.agent_factory.prime_engine.swarm_dispatcher import SwarmDispatcher
from core.agent_factory.prime_engine.prime_orchestrator import GerychPrimeOrchestrator


def test_swarm_dispatcher_routing():
    dispatcher = SwarmDispatcher()

    res_rick = dispatcher.dispatch_task("t1", "Refactor Code", "refactor_pytest")
    assert res_rick.assigned_agent == "agent_rick"
    assert res_rick.status == "completed"

    res_yuriy = dispatcher.dispatch_task("t2", "Update Obsidian Notes", "obsidian_rag")
    assert res_yuriy.assigned_agent == "agent_yuriy"

    res_cas = dispatcher.dispatch_task("t3", "Build FastAPI Endpoint", "docker_fastapi")
    assert res_cas.assigned_agent == "agent_cas"

    res_tiffany = dispatcher.dispatch_task("t4", "Build Canvas UI", "reactflow_ui")
    assert res_tiffany.assigned_agent == "agent_tiffany"


def test_gerych_prime_orchestrator_cycle():
    orchestrator = GerychPrimeOrchestrator(vault_path="docs/tasks")
    result = orchestrator.run_orchestration_cycle()

    assert result["status"] == "success"
    assert "scanned_nodes_count" in result
    assert result["scanned_nodes_count"] >= 1
