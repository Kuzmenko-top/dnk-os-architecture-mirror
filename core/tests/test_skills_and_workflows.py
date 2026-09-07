# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_skills_and_workflows.py"
# purpose: "Unit tests for SkillManager keyword matching and WorkflowOrchestrator DAG execution with Human Approval gates."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import pytest
from core.skill_manager import SkillManager
from core.workflow_orchestrator import WorkflowOrchestrator

def test_skill_manager_trigger_matching():
    """Verify Token-Efficient RAG trigger matching to prevent context bloat."""
    manager = SkillManager()
    
    # Matches shopify customization
    m1 = manager.find_matching_skills("I want to build shopify liquid sections")
    assert len(m1) == 1
    assert m1[0]["name"] == "shopify-liquid-customizer"

    # Matches task forest syncing
    m2 = manager.find_matching_skills("Please run sync for my task-forest")
    assert len(m2) == 1
    assert m2[0]["name"] == "task-forest-sync"

    # No matches for irrelevant prompts
    m3 = manager.find_matching_skills("Do a quick git status and write a report")
    assert len(m3) == 0

def test_workflow_orchestrator_dag_execution():
    """Verify sequential DAG execution without cycles."""
    orchestrator = WorkflowOrchestrator()
    execution_trail = []

    def run_a(): execution_trail.append("A")
    def run_b(): execution_trail.append("B")
    def run_c(): execution_trail.append("C")

    orchestrator.add_step("A", run_a)
    orchestrator.add_step("B", run_b, depends_on=["A"])
    orchestrator.add_step("C", run_c, depends_on=["B"])

    assert orchestrator.has_cycle() is False

    res = orchestrator.run_workflow()
    assert res["status"] == "completed"
    assert res["executed"] == ["A", "B", "C"]
    assert execution_trail == ["A", "B", "C"]

def test_workflow_orchestrator_cycle_rejection():
    """Verify cycle/loop detection rejects non-DAG workflows."""
    orchestrator = WorkflowOrchestrator()
    
    orchestrator.add_step("A", lambda: None, depends_on=["B"])
    orchestrator.add_step("B", lambda: None, depends_on=["A"])

    assert orchestrator.has_cycle() is True
    with pytest.raises(ValueError, match="contains a cycle"):
        orchestrator.run_workflow()

def test_workflow_orchestrator_human_approval_gate():
    """Verify execution pauses on nodes requiring Human Approval until granted."""
    orchestrator = WorkflowOrchestrator()
    execution_trail = []

    def run_a(): execution_trail.append("A")
    def run_b(): execution_trail.append("B")

    orchestrator.add_step("A", run_a)
    orchestrator.add_step("B", run_b, depends_on=["A"], requires_approval=True)

    # First run (should pause before B)
    res1 = orchestrator.run_workflow()
    assert res1["status"] == "paused"
    assert res1["executed"] == ["A"]
    assert res1["paused"] == ["B"]
    assert execution_trail == ["A"]

    # Grant approval and rerun
    orchestrator.grant_approval("B")
    res2 = orchestrator.run_workflow()
    assert res2["status"] == "completed"
    assert res2["executed"] == ["B"]
    assert res2["paused"] == []
    assert execution_trail == ["A", "B"]
