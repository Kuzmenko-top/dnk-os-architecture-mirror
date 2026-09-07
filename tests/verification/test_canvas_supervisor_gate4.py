# --- DNK-MRH-HEADER ---
# mrh_id: "test_canvas_supervisor_gate4.py"
# purpose: "E2E verification tests for DNK Canvas Supervisor Gate 4."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2] # DNK OS
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# Add services folder as well
services_path = ROOT / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

import pytest
import json
from uuid import uuid4
from datetime import datetime, timezone

from services.dnk_canvas_api.main import (
    Base, engine, SessionLocal, DesignRun, SupervisorRun, AgentStep, ToolCall, Artifact, CanvasSnapshot, DesignContext, Canvas
)
from services.dnk_canvas_api.supervisor.supervisor import DNKSupervisor
from services.dnk_canvas_api.supervisor.policy_gate import PolicyGate, PolicyViolationException
from services.dnk_canvas_api.supervisor.context_builder import ContextBuilder
from services.dnk_canvas_api.skills.registry import registry
from services.dnk_canvas_worker.workers.design_workspace_worker import DesignWorkspaceWorker

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

def test_supervisor_create_and_workflow_execution(setup_db):
    db = SessionLocal()
    try:
        canvas_id = str(uuid4())
        canvas = Canvas(id=canvas_id, name="Test Canvas")
        db.add(canvas)
        db.flush()
        design_run = DesignRun(
            id=str(uuid4()),
            canvas_id=canvas_id,
            status="queued",
            command="generate_workspace",
            payload_json=json.dumps({
                "project_id": str(uuid4()),
                "prompt": "Створи головний екран кабінету DNK OS",
                "design_system_id": "dnk-default",
                "mode": "supervised"
            })
        )
        db.add(design_run)
        db.commit()

        # 1. Real Supervisor creates run
        sv = DNKSupervisor()
        sv_run = sv.create_supervisor_run(db, design_run.id, canvas_id, json.loads(design_run.payload_json))
        assert sv_run.status == "queued"
        assert sv_run.design_run_id == design_run.id

        # 2. Skill resolves successfully & workflow executes
        sv.execute_run_workflow(db, sv_run.id)
        
        db.refresh(sv_run)
        db.refresh(design_run)
        assert sv_run.status == "running"
        assert design_run.status == "running"

        # Check Context Builder compiled context
        ctx_row = db.query(DesignContext).filter(DesignContext.supervisor_run_id == sv_run.id).first()
        assert ctx_row is not None
        assert ctx_row.prompt == "Створи головний екран кабінету DNK OS"
        assert ctx_row.design_system_id == "dnk-default"
        
        # Ensure secrets are excluded from context
        collected = ctx_row.collected_data
        assert "secrets" not in collected
        assert "credentials" not in collected

        # 3. Worker creates deterministic scene & audits tool calls
        DesignWorkspaceWorker.process_task(db, sv_run.id, "dnk.ui.generate_workspace", collected)

        db.refresh(sv_run)
        db.refresh(design_run)
        assert sv_run.status == "completed"
        assert design_run.status == "completed"

        # Check Tool Call audited
        step = db.query(AgentStep).filter(AgentStep.supervisor_run_id == sv_run.id).first()
        assert step is not None
        assert step.status == "completed"

        t_call = db.query(ToolCall).filter(ToolCall.agent_step_id == step.id).first()
        assert t_call is not None
        assert t_call.tool_name == "generate_workspace_scene"
        assert t_call.status == "completed"

        # 4. Artifact persisted & Canvas Snapshot created
        brief = db.query(Artifact).filter(Artifact.canvas_id == canvas_id, Artifact.type == "design_brief").first()
        assert brief is not None

        scene = db.query(Artifact).filter(Artifact.canvas_id == canvas_id, Artifact.type == "excalidraw_scene").first()
        assert scene is not None
        scene_content = json.loads(scene.content_json)
        assert len(scene_content["elements"]) == 7

        critique = db.query(Artifact).filter(Artifact.canvas_id == canvas_id, Artifact.type == "critique_report").first()
        assert critique is not None

        snap = db.query(CanvasSnapshot).filter(CanvasSnapshot.canvas_id == canvas_id).first()
        assert snap is not None
        assert snap.version == 1
        elements_in_snap = json.loads(snap.elements_json)
        assert len(elements_in_snap) == 7

    finally:
        db.close()


def test_recovery_resilience(setup_db):
    db = SessionLocal()
    try:
        canvas_id = str(uuid4())
        canvas = Canvas(id=canvas_id, name="Test Canvas")
        db.add(canvas)
        db.flush()
        design_run = DesignRun(
            id=str(uuid4()),
            canvas_id=canvas_id,
            status="running",
            command="generate_workspace",
            payload_json=json.dumps({"mode": "supervised"})
        )
        db.add(design_run)
        db.commit()

        sv_run = SupervisorRun(
            id=str(uuid4()),
            design_run_id=design_run.id,
            workflow_id="test_recovery_wf",
            status="running"
        )
        db.add(sv_run)
        db.commit()

        sv = DNKSupervisor()
        sv.recover_incomplete_runs(db)

        db.refresh(sv_run)
        assert sv_run.status == "failed"
        assert "RECOVERY_RESET" in sv_run.failure_code
    finally:
        db.close()


def test_invalid_skill_failure(setup_db):
    db = SessionLocal()
    try:
        canvas_id = str(uuid4())
        canvas = Canvas(id=canvas_id, name="Test Canvas")
        db.add(canvas)
        db.flush()
        design_run = DesignRun(
            id=str(uuid4()),
            canvas_id=canvas_id,
            status="queued",
            command="generate_workspace",
            payload_json=json.dumps({
                "skill_id": "unregistered.skill",
                "mode": "supervised"
            })
        )
        db.add(design_run)
        db.commit()

        sv = DNKSupervisor()
        sv_run = sv.create_supervisor_run(db, design_run.id, canvas_id, json.loads(design_run.payload_json))
        sv.execute_run_workflow(db, sv_run.id)

        db.refresh(sv_run)
        assert sv_run.status == "failed"
        assert "is not registered" in sv_run.failure_code
    finally:
        db.close()


def test_policy_gate_blocking_l2(setup_db):
    from services.dnk_canvas_api.skills.models import BaseSkill, SkillContract

    class L2MockSkill(BaseSkill):
        contract = SkillContract(
            id="dnk.action.github_push",
            version="1.0.0",
            risk_level="L2",
            input_schema=["project_id"],
            output_artifacts=["commit_sha"],
            approval_required=True
        )
        def execute(self, context):
            return {"commit_sha": "abc1234"}

    registry.register(L2MockSkill())

    db = SessionLocal()
    try:
        canvas_id = str(uuid4())
        canvas = Canvas(id=canvas_id, name="Test Canvas")
        db.add(canvas)
        db.flush()
        design_run = DesignRun(
            id=str(uuid4()),
            canvas_id=canvas_id,
            status="queued",
            command="generate_workspace",
            payload_json=json.dumps({
                "skill_id": "dnk.action.github_push",
                "mode": "supervised"
            })
        )
        db.add(design_run)
        db.commit()

        sv = DNKSupervisor()
        sv_run = sv.create_supervisor_run(db, design_run.id, canvas_id, json.loads(design_run.payload_json))
        sv.execute_run_workflow(db, sv_run.id)

        db.refresh(sv_run)
        assert sv_run.status == "failed"
        assert "POLICY_VIOLATION" in sv_run.failure_code
    finally:
        db.close()
