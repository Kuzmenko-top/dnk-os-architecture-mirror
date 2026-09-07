# --- DNK-MRH-HEADER ---
# mrh_id: "tests_verification_test_swarm_parallel_and_adversarial"
# purpose: "Comprehensive verification suite for Swarm Parallel Subagents and Adversarial Review Gate."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from core.orchestrator.swarm_coordinator import swarm_coordinator
from core.security.adversarial_review import adversarial_review_engine


@pytest.fixture
def client():
    return TestClient(app)


def test_swarm_coordinator_list_agents():
    """Verifies that Swarm Coordinator registers and lists all swarm agents and capabilities."""
    agents = swarm_coordinator.list_agents()
    assert len(agents) >= 4
    agent_ids = [a.get("agent_id") for a in agents]
    assert "gerych_prime" in agent_ids
    assert "gerych_builder" in agent_ids
    assert "gerych_researcher" in agent_ids
    assert "gerych_auditor" in agent_ids
    assert "dnk_dev_fullstack" in agent_ids
    assert "dnk_shopify" in agent_ids


def test_swarm_coordinator_parallel_dispatch():
    """Verifies concurrent subagent task execution with timing telemetry."""
    tasks = [
        {"agent": "gerych_builder", "action": "synthesize_ui", "payload": {"domain": "canvas"}},
        {"agent": "dnk_dev_fullstack", "action": "build_router", "payload": {"domain": "agent"}},
        {"agent": "dnk_shopify", "action": "verify_checkout", "payload": {"shop": "test.myshopify.com"}},
        {"agent": "gerych_auditor", "action": "adversarial_audit", "payload": {}},
    ]
    res = swarm_coordinator.dispatch_parallel(tasks)
    assert res["status"] == "parallel_batch_completed"
    assert res["task_count"] == 4
    assert len(res["completed_tasks"]) == 4
    for task_res in res["completed_tasks"]:
        assert task_res["status"] == "completed"
        assert "duration_seconds" in task_res
        assert "outcome" in task_res


def test_swarm_coordinator_adversarial_review_debate():
    """Verifies that Adversarial AI Review engine executes Red-Team Auditor vs Blue-Team Builder."""
    review_res = swarm_coordinator.run_adversarial_review()
    assert review_res["status"] == "success"
    assert "total_candidates_detected" in review_res
    assert "false_positives_refuted" in review_res
    assert "confirmed_issues_count" in review_res
    assert "passed" in review_res


def test_swarm_coordinator_autonomous_pipeline():
    """Verifies the autonomous 4-stage pipeline (Prime -> Researcher -> Builder -> Auditor)."""
    res = swarm_coordinator.run_pipeline("Verify resilient multi-agent orchestration and security gates")
    assert res["status"] == "pipeline_success"
    assert len(res["pipeline_stages"]) == 4
    assert res["pipeline_stages"][0]["agent"] == "gerych_prime"
    assert res["pipeline_stages"][1]["agent"] == "gerych_researcher"
    assert res["pipeline_stages"][2]["agent"] == "gerych_builder"
    assert res["pipeline_stages"][3]["agent"] == "gerych_auditor"
    assert res["pipeline_stages"][3]["status"] == "passed"


def test_api_swarm_status_endpoint(client):
    """Verifies GET /api/agent/swarm/status endpoint."""
    response = client.get("/api/agent/swarm/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_agents"] >= 4
    assert any(a["agent_id"] == "gerych_auditor" for a in data["agents"])


def test_api_swarm_dispatch_endpoint(client):
    """Verifies POST /api/agent/swarm/dispatch endpoint."""
    payload = {
        "tasks": [
            {"agent": "gerych_builder", "action": "render_node", "payload": {}},
            {"agent": "dnk_shopify", "action": "check_pixels", "payload": {}},
            {"agent": "gerych_auditor", "action": "audit_paths", "payload": {}},
        ]
    }
    response = client.post("/api/agent/swarm/dispatch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["dispatch_summary"]["task_count"] == 3


def test_api_swarm_adversarial_review_endpoint(client):
    """Verifies POST /api/agent/swarm/adversarial-review endpoint."""
    response = client.post("/api/agent/swarm/adversarial-review", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["verdict"] in ["PASSED", "FLAGGED"]
    assert "adversarial_review" in data


def test_api_agent_run_swarm_parallel(client):
    """Verifies POST /api/agent/run with flow_type='swarm_parallel'."""
    payload = {
        "flow_type": "swarm_parallel",
        "query": "Parallel multi-agent execution test",
        "canvas_id": "00000000-0000-0000-0000-000000000001",
    }
    response = client.post("/api/agent/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["execution_status"] == "completed"
    assert "Swarm parallel execution completed" in data["content"]
    assert data["swarm_result"]["status"] == "parallel_batch_completed"


def test_api_agent_run_adversarial_review(client):
    """Verifies POST /api/agent/run with flow_type='adversarial_review'."""
    payload = {
        "flow_type": "adversarial_review",
        "query": "Adversarial AI Gate test",
    }
    response = client.post("/api/agent/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Adversarial Review debate completed" in data["content"]
