# --- DNK-MRH-HEADER ---
# mrh_id: "tests_swarm_test_quantum_engine"
# purpose: "Unit & Integration Tests for Task Quantum Swarm Engine, Decomposition, DAG Pipeline & Self-Healing"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import pytest
import os
import tempfile
from unittest.mock import MagicMock

from core.swarm.quantum_engine import (
    TaskQuantum,
    QuantumDecomposer,
    QuantumSwarmCoordinator,
    QuantumExecutionResult
)
from core.swarm.subagents import (
    BuilderSubagent,
    TesterSubagent,
    AuditorSubagent,
    SubagentResult
)


def test_quantum_decomposer_splits_large_task():
    file_specs = [
        {"component": "DB Multi-Pool", "file_path": "apps/api/db/database.py", "test_path": "tests/test_db.py"},
        {"component": "Tenant Router", "file_path": "apps/api/db/tenant_router.py", "test_path": "tests/test_router.py"},
        {"component": "Redis Bus", "file_path": "apps/api/services/redis_pubsub.py", "test_path": "tests/test_redis.py"},
        {"component": "Web UI", "file_path": "apps/web/page.tsx", "test_path": "tests/test_ui.py"},
        {"component": "Docs", "file_path": "docs/handoff.md", "test_path": ""}
    ]

    quanta = QuantumDecomposer.decompose_task(
        task_id="DNK-TEST-001",
        title="Scale Platform",
        file_specs=file_specs
    )

    # 5 files chunked by 2 = 3 quanta
    assert len(quanta) == 3
    for q in quanta:
        assert len(q.target_files) <= 3
        assert q.max_turns <= 12

    # Verify dependency chain
    assert quanta[0].dependencies == []
    assert quanta[1].dependencies == [quanta[0].quantum_id]
    assert quanta[2].dependencies == [quanta[1].quantum_id]


@pytest.mark.asyncio
async def test_quantum_swarm_coordinator_successful_dag():
    mock_builder = MagicMock(spec=BuilderSubagent)
    mock_builder.name = "mock_builder"
    mock_builder.execute_quantum.return_value = SubagentResult(
        success=True,
        agent_name="mock_builder",
        output="Code synthesized"
    )

    mock_tester = MagicMock(spec=TesterSubagent)
    mock_tester.name = "mock_tester"
    mock_tester.run_tests.return_value = SubagentResult(
        success=True,
        agent_name="mock_tester",
        output="All tests passed"
    )

    mock_auditor = MagicMock(spec=AuditorSubagent)
    mock_auditor.name = "mock_auditor"
    mock_auditor.audit_files.return_value = SubagentResult(
        success=True,
        agent_name="mock_auditor",
        output="Audit passed"
    )

    coordinator = QuantumSwarmCoordinator(
        builder=mock_builder,
        tester=mock_tester,
        auditor=mock_auditor
    )

    q1 = TaskQuantum(quantum_id="q1", title="Quantum 1", target_files=["f1.py"], test_files=["t1.py"])
    q2 = TaskQuantum(quantum_id="q2", title="Quantum 2", target_files=["f2.py"], test_files=["t2.py"], dependencies=["q1"])

    result = await coordinator.execute_task_dag("TASK-001", [q1, q2])

    assert result.overall_status == "SUCCESS"
    assert result.completed_quanta == 2
    assert result.failed_quanta == 0
    assert q1.status == "VERIFIED"
    assert q2.status == "VERIFIED"


@pytest.mark.asyncio
async def test_quantum_swarm_coordinator_self_healing_retry():
    mock_builder = MagicMock(spec=BuilderSubagent)
    mock_builder.name = "mock_builder"
    mock_builder.execute_quantum.return_value = SubagentResult(success=True, agent_name="mock_builder", output="Code synthesized")

    mock_tester = MagicMock(spec=TesterSubagent)
    mock_tester.name = "mock_tester"
    # Fails on attempt 1, passes on attempt 2 (self-healing)
    mock_tester.run_tests.side_effect = [
        SubagentResult(success=False, agent_name="mock_tester", output="", errors=["Import error in test"]),
        SubagentResult(success=True, agent_name="mock_tester", output="Pass")
    ]

    mock_auditor = MagicMock(spec=AuditorSubagent)
    mock_auditor.name = "mock_auditor"
    mock_auditor.audit_files.return_value = SubagentResult(success=True, agent_name="mock_auditor", output="Audit passed")

    coordinator = QuantumSwarmCoordinator(
        builder=mock_builder,
        tester=mock_tester,
        auditor=mock_auditor
    )

    quantum = TaskQuantum(quantum_id="q_healing", title="Healing Quantum", target_files=["f1.py"], test_files=["t1.py"])
    executed = await coordinator.execute_quantum(quantum)

    assert executed.status == "VERIFIED"
    assert executed.retry_count == 1
    assert mock_tester.run_tests.call_count == 2


@pytest.mark.asyncio
async def test_quantum_swarm_fail_closed_on_prereq_failure():
    mock_builder = MagicMock(spec=BuilderSubagent)
    mock_builder.name = "mock_builder"
    mock_builder.execute_quantum.return_value = SubagentResult(success=False, agent_name="mock_builder", output="", errors=["Unrecoverable syntax error"])

    mock_tester = MagicMock(spec=TesterSubagent)
    mock_auditor = MagicMock(spec=AuditorSubagent)

    coordinator = QuantumSwarmCoordinator(builder=mock_builder, tester=mock_tester, auditor=mock_auditor)

    q1 = TaskQuantum(quantum_id="q1", title="Quantum 1", max_retries=0)
    q2 = TaskQuantum(quantum_id="q2", title="Quantum 2", dependencies=["q1"])

    result = await coordinator.execute_task_dag("TASK-FAIL-001", [q1, q2])

    assert result.overall_status == "FAILED"
    assert q1.status == "FAILED"
    assert q2.status == "ROLLED_BACK"
    assert result.completed_quanta == 0


def test_builder_enforces_scope_boundary():
    builder = BuilderSubagent()
    # Reject 4 files (> 3)
    res = builder.execute_quantum("Overloaded Quantum", ["f1.py", "f2.py", "f3.py", "f4.py"], "instructions")
    assert res.success is False
    assert "exceeds quantum maximum of 3" in res.errors[0]


def test_auditor_catches_mrh_and_path_violations():
    auditor = AuditorSubagent()

    with tempfile.TemporaryDirectory() as tmpdir:
        # File with forbidden absolute user path
        bad_path_file = os.path.join(tmpdir, "bad_path.py")
        with open(bad_path_file, "w") as f:
            f.write("# --- DNK-MRH-HEADER ---\n# mrh_id: 'test'\nimport os\npath = '/Users/kuzmenko.top/secret'\n")

        # File missing MRH header
        no_mrh_file = os.path.join(tmpdir, "no_mrh.py")
        with open(no_mrh_file, "w") as f:
            f.write("def foo(): return 42\n")

        # Valid file
        valid_file = os.path.join(tmpdir, "valid.py")
        with open(valid_file, "w") as f:
            f.write("# --- DNK-MRH-HEADER ---\n# mrh_id: 'valid'\n# status: 'Active'\n# --- END DNK-MRH-HEADER ---\ndef ok(): pass\n")

        # 1. Audit bad path
        res_bad = auditor.audit_files([bad_path_file])
        assert res_bad.success is False
        assert any("Path hygiene violation" in e for e in res_bad.errors)

        # 2. Audit missing MRH
        res_no_mrh = auditor.audit_files([no_mrh_file])
        assert res_no_mrh.success is False
        assert any("MRH violation" in e for e in res_no_mrh.errors)

        # 3. Audit valid
        res_valid = auditor.audit_files([valid_file])
        assert res_valid.success is True
        assert len(res_valid.errors) == 0
