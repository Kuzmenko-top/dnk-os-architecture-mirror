# --- DNK-MRH-HEADER ---
# mrh_id: "test_visual_shell"
# purpose: "Automated verification test suite for Visual Shell (Robochyi Kabinet) MVP"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2] # DNK OS
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

import pytest
import time
from uuid import uuid4
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.database import _data
from apps.api.middleware.security import RATE_LIMIT_STORE
from core.models.security import SecurityPolicy
from core.decorators.security_gate import get_security_gate_service, SecurityGateDenied
from core.flows.research_write_validate import GLOBAL_EVENTS_LOG

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    # Clear visual shell DB data and global flow logs before each test
    _data["canvases"].clear()
    _data["artifacts"].clear()
    _data["runs"].clear()
    GLOBAL_EVENTS_LOG.clear()
    RATE_LIMIT_STORE.clear()
    # Clear policies in the security gate
    gate = get_security_gate_service()
    gate.policies.clear()
    yield

def test_create_canvas():
    """1. test_create_canvas — створення canvas."""
    response = client.post("/canvas", json={"name": "Test Canvas"})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Canvas"

def test_get_canvas():
    """2. test_get_canvas — отримання canvas."""
    create_res = client.post("/canvas", json={"name": "Canvas to Fetch"})
    canvas_id = create_res.json()["id"]

    get_res = client.get(f"/canvas/{canvas_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Canvas to Fetch"

def test_update_canvas():
    """3. test_update_canvas — оновлення canvas."""
    create_res = client.post("/canvas", json={"name": "Canvas to Update"})
    canvas_id = create_res.json()["id"]

    update_res = client.put(f"/canvas/{canvas_id}", json={"name": "Updated Name"})
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Name"

def test_run_agent_flow():
    """4. test_run_agent_flow — запуск агентних флоу."""
    # Create canvas
    canvas_id = str(uuid4())
    response = client.post("/agent/run", json={
        "canvas_id": canvas_id,
        "flow_type": "research_write_validate",
        "query": "test query"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "content" in data
    assert "SOTA Research results" in data["content"]

def test_artifact_update():
    """5. test_artifact_update — оновлення артефакту."""
    canvas_id = str(uuid4())
    content = "This is a new artifact content."
    response = client.put(f"/artifact/{canvas_id}", json={"content": content})
    assert response.status_code == 200
    data = response.json()
    assert data["canvas_id"] == canvas_id
    assert data["content"] == content

def test_security_gate_integration():
    """6. test_security_gate_integration — оновлення артефакту через Security Gate."""
    # Create a restrictive policy: maximum file size is 10 bytes
    policy_id = uuid4()
    policy = SecurityPolicy(
        id=policy_id,
        name="Block updates over 10 bytes",
        action_patterns=["artifact.update"],
        conditions={"max_file_size": 10},
        require_approval=False,
        created_at=int(time.time()),
        updated_at=int(time.time())
    )
    get_security_gate_service().create_policy(policy)

    canvas_id = str(uuid4())
    # Long content exceeds 10 bytes limit -> should fail
    long_content = "This is long content exceeding 10 bytes."
    
    # PUT request should catch SecurityGateDenied and map it to 403 via our FastAPI handler
    response = client.put(f"/artifact/{canvas_id}", json={"content": long_content})
    assert response.status_code == 403
    assert "Security Gate Denied" in response.json()["detail"]

def test_timeline_db_integration():
    """7. test_timeline_db_integration — всі кроки записуються в Timeline DB."""
    canvas_id = str(uuid4())
    client.post("/agent/run", json={
        "canvas_id": canvas_id,
        "flow_type": "research_write_validate",
        "query": "Visual Shell"
    })

    # Verify that flow logs recorded all required events:
    # flow_started, research_completed, write_completed, validate_completed, flow_completed
    event_types = [event["event_type"] for event in GLOBAL_EVENTS_LOG]
    
    assert "flow_started" in event_types
    assert "research_completed" in event_types
    assert "write_completed" in event_types
    assert "validate_completed" in event_types
    assert "flow_completed" in event_types
