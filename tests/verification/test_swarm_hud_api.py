# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_swarm_hud_api.py"
# purpose: "Verify Swarm HUD & Live Worktree Inspector API endpoints (/api/v1/swarm/*)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & Maksym Kuzmenko"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from core.orchestrator.swarm_ledger import SwarmLedger, ArtifactCategory


@pytest.fixture
def client():
    return TestClient(app)


def test_swarm_health_and_token_status(client):
    res_health = client.get("/api/v1/swarm/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] == "healthy"
    assert data_health["agent_count"] == 14

    res_token = client.get("/api/v1/swarm/token-status")
    assert res_token.status_code == 200
    data_token = res_token.json()
    assert data_token["provider"] == "vertex"


def test_swarm_worktrees_endpoint(client):
    res = client.get("/api/v1/swarm/worktrees")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_swarm_audit_trail_endpoint(client):
    res = client.get("/api/v1/swarm/audit-trail?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "events" in data
    assert isinstance(data["events"], list)


def test_swarm_ledger_endpoint(client):
    # Register an artifact to test retrieval
    ledger = SwarmLedger.get_instance()
    ledger.register_artifact(
        key="hud_test:schema",
        category=ArtifactCategory.SCHEMA,
        producer_agent="dnk_dev_fullstack",
        content={"model": "TestSchema"},
        task_id="hud_test_task",
    )

    res = client.get("/api/v1/swarm/ledger?task_id=hud_test_task")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert any(a["key"] == "hud_test:schema" for a in data["artifacts"])


def test_swarm_hud_summary_endpoint(client):
    res = client.get("/api/v1/swarm/hud-summary")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"
    assert "active_worktrees_count" in data
    assert "total_audit_events" in data
    assert "total_ledger_artifacts" in data
    assert "consensus_stats" in data
