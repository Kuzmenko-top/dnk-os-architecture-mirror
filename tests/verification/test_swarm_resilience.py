# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_swarm_resilience.py"
# purpose: "Unit & Integration test suite for Swarm Resilience, Process Hygiene and Health API."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_swarm_health_endpoint():
    """Verify GET /api/v1/swarm/health returns healthy status and active metrics."""
    response = client.get("/api/v1/swarm/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded", "operational")
    assert isinstance(data.get("active_locks"), list)
    assert "memory_tier_status" in data
    assert "agent_count" in data
    assert data["agent_count"] >= 1
    assert "timestamp" in data


def test_swarm_reap_zombies_endpoint():
    """Verify POST /api/v1/swarm/reap-zombies executes process audit safely."""
    response = client.post("/api/v1/swarm/reap-zombies")
    assert response.status_code == 200
    data = response.json()
    assert "reaped_count" in data
    assert isinstance(data["reaped_count"], int)
    assert data["status"] == "completed"


def test_swarm_token_status_endpoint():
    """Verify GET /api/v1/swarm/token-status returns token validity info."""
    response = client.get("/api/v1/swarm/token-status")
    assert response.status_code == 200
    data = response.json()
    assert "token_present" in data
    assert "provider" in data
    assert data["provider"] in ("vertex", "google_cloud", "mock", "env")
