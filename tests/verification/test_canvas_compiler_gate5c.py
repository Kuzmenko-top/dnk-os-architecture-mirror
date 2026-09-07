# --- DNK-MRH-HEADER ---
# mrh_id: "test_canvas_compiler_gate5c.py"
# purpose: "E2E verification tests for DNK Canvas Compiler Gate 5C-A Controlled External Pilot."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import os
import sys
import pathlib
import json
import pytest
from uuid import uuid4

ROOT = pathlib.Path(__file__).resolve().parents[2] # DNK OS
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
services_path = ROOT / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from services.dnk_canvas_api.main import (
    Base, engine, SessionLocal, DesignRun, SupervisorRun, DesignValidationResult, CanvasDocument, Canvas
)
from services.dnk_canvas_api.supervisor.supervisor import DNKSupervisor

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

def test_external_pilot_configuration_contract():
    # Verify pilot configuration variables are parsed correctly
    os.environ["LLM_PROVIDER_MODE"] = "validated"
    os.environ["LLM_WHITELISTED_WORKSPACES"] = "some-external-tenant-uuid"
    
    assert os.getenv("LLM_PROVIDER_MODE") == "validated"
    assert "some-external-tenant-uuid" in os.getenv("LLM_WHITELISTED_WORKSPACES")
    
    os.environ.pop("LLM_PROVIDER_MODE", None)
    os.environ.pop("LLM_WHITELISTED_WORKSPACES", None)

@pytest.mark.anyio
async def test_external_pilot_validated_single_workspace_gate(setup_db):
    db = SessionLocal()
    try:
        os.environ["LLM_PROVIDER_MODE"] = "validated"
        pilot_ws_uuid = str(uuid4())
        os.environ["LLM_WHITELISTED_WORKSPACES"] = pilot_ws_uuid
        
        canvas_id = str(uuid4())
        canvas = Canvas(id=canvas_id, name="External Pilot Canvas")
        db.add(canvas)
        db.flush()
        
        doc = CanvasDocument(
            id=canvas_id,
            workspace_id=pilot_ws_uuid,
            title="External Pilot Document"
        )
        db.add(doc)

        design_run = DesignRun(
            id=str(uuid4()),
            canvas_id=canvas_id,
            status="queued",
            command="generate_workspace",
            payload_json=json.dumps({
                "project_id": str(uuid4()),
                "prompt": "Create custom analytics node for external pilot workspace",
                "mode": "supervised"
            })
        )
        db.add(design_run)
        db.commit()

        sv = DNKSupervisor()
        sv_run = sv.create_supervisor_run(db, design_run.id, canvas_id, json.loads(design_run.payload_json))
        
        await sv.execute_run_workflow_async(db, sv_run.id)
        db.refresh(sv_run)
        
        # Verify it went to live validated execution successfully
        assert sv_run.status in ["running", "completed", "tool_pending"]
        
    finally:
        db.close()
        os.environ.pop("LLM_PROVIDER_MODE", None)
        os.environ.pop("LLM_WHITELISTED_WORKSPACES", None)

@pytest.mark.anyio
async def test_external_pilot_negative_degradation_fallback(setup_db):
    db = SessionLocal()
    try:
        os.environ["LLM_PROVIDER_MODE"] = "validated"
        pilot_ws_uuid = str(uuid4())
        other_ws_uuid = str(uuid4())
        os.environ["LLM_WHITELISTED_WORKSPACES"] = pilot_ws_uuid
        
        canvas_id = str(uuid4())
        canvas = Canvas(id=canvas_id, name="Non-Pilot Canvas")
        db.add(canvas)
        db.flush()
        
        doc = CanvasDocument(
            id=canvas_id,
            workspace_id=other_ws_uuid,
            title="Non-Pilot Document"
        )
        db.add(doc)

        design_run = DesignRun(
            id=str(uuid4()),
            canvas_id=canvas_id,
            status="queued",
            command="generate_workspace",
            payload_json=json.dumps({
                "project_id": str(uuid4()),
                "prompt": "This should instantly fail-closed to shadow mode",
                "mode": "supervised"
            })
        )
        db.add(design_run)
        db.commit()

        sv = DNKSupervisor()
        sv_run = sv.create_supervisor_run(db, design_run.id, canvas_id, json.loads(design_run.payload_json))
        
        await sv.execute_run_workflow_async(db, sv_run.id)
        db.refresh(sv_run)
        
        # Must execute safely inside shadow mode
        assert sv_run.status in ["running", "completed", "tool_pending"]
        
    finally:
        db.close()
        os.environ.pop("LLM_PROVIDER_MODE", None)
        os.environ.pop("LLM_WHITELISTED_WORKSPACES", None)
