# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_node_tasks_artifacts.py"
# purpose: "Verification tests for Node Tasks Live Artifacts, Diff Inspector, and Verification Gate endpoints"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_test_node():
    test_node_id = "test-node-artifact-verification-001"
    # Create test node before each test
    node_payload = {
        "id": test_node_id,
        "title": "Artifacts Verification Test Task",
        "description": "Task for verifying live artifact diffs and test gate execution",
        "node_type": "task",
        "stage": "ready",
        "status": "ready",
        "assigned_agent": "gerych_builder",
        "priority": "P1_High",
        "target_module": "apps/api",
        "target_files": [
            "apps/api/routers/node_tasks_router.py",
            "services/dnk_node_tasks/models.py",
        ],
        "tags": ["test", "artifacts", "diff_inspector"],
    }
    client.post("/api/v3/node_tasks/node", json=node_payload)
    yield test_node_id
    # Clean up test node after
    client.delete(f"/api/v3/node_tasks/node/{test_node_id}")


def test_get_node_artifacts_not_found():
    res = client.get("/api/v3/node_tasks/non-existent-artifact-node-xyz/artifacts")
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data


def test_get_node_artifacts_success(cleanup_test_node):
    node_id = cleanup_test_node
    res = client.get(f"/api/v3/node_tasks/{node_id}/artifacts")
    assert res.status_code == 200
    data = res.json()
    assert data["node_id"] == node_id
    assert data["agent"] == "gerych_builder"
    assert "files" in data
    assert len(data["files"]) >= 2

    # Check file diff contents
    file_diff = data["files"][0]
    assert "path" in file_diff
    assert "change_type" in file_diff
    assert "diff_content" in file_diff
    assert "additions" in file_diff
    assert "deletions" in file_diff
    assert len(file_diff["diff_content"]) > 0


def test_accept_artifacts(cleanup_test_node):
    node_id = cleanup_test_node
    res = client.post(f"/api/v3/node_tasks/{node_id}/accept_artifacts")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["action"] == "accepted"
    assert data["node"]["status"] == "completed"
    assert data["node"]["stage"] == "completed"
    assert data["node"]["progress"] == 100.0

    # Verify logs received SUCCESS entry
    log_res = client.get(f"/api/v3/node_tasks/{node_id}/logs")
    assert log_res.status_code == 200
    logs = log_res.json()["logs"]
    assert any("Artifacts accepted and certified" in log["message"] for log in logs)


def test_reject_artifacts(cleanup_test_node):
    node_id = cleanup_test_node
    reason = "Code does not adhere to zero-waste protocol."
    res = client.post(
        f"/api/v3/node_tasks/{node_id}/reject_artifacts",
        json={"reason": reason},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["action"] == "rejected"
    assert data["node"]["status"] == "in_progress"
    assert data["node"]["stage"] == "in_progress"
    assert data["node"]["progress"] == 50.0

    # Verify logs received WARNING entry
    log_res = client.get(f"/api/v3/node_tasks/{node_id}/logs")
    assert log_res.status_code == 200
    logs = log_res.json()["logs"]
    assert any(reason in log["message"] for log in logs)


def test_run_verification_success(cleanup_test_node):
    node_id = cleanup_test_node
    # Test with custom quick command that always succeeds
    res = client.post(
        f"/api/v3/node_tasks/{node_id}/run_verification",
        json={"test_command": "python3 -c 'print(\"VERIFICATION OK\")'"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["verified"] is True
    assert data["exit_code"] == 0
    assert "VERIFICATION OK" in data["output"]

    # Verify logs contain verification success
    log_res = client.get(f"/api/v3/node_tasks/{node_id}/logs")
    logs = log_res.json()["logs"]
    assert any("Verification gate PASSED" in log["message"] for log in logs)


def test_run_verification_failure(cleanup_test_node):
    node_id = cleanup_test_node
    # Test with command that fails
    res = client.post(
        f"/api/v3/node_tasks/{node_id}/run_verification",
        json={"test_command": "python3 -c 'import sys; sys.stderr.write(\"FAILING\"); sys.exit(2)'"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "failure"
    assert data["verified"] is False
    assert data["exit_code"] == 2
    assert "FAILING" in data["output"]

    # Verify logs contain verification error
    log_res = client.get(f"/api/v3/node_tasks/{node_id}/logs")
    logs = log_res.json()["logs"]
    assert any("Verification gate FAILED" in log["message"] for log in logs)


def test_clear_node_logs(cleanup_test_node):
    node_id = cleanup_test_node
    # Trigger an action that writes logs
    client.post(
        f"/api/v3/node_tasks/{node_id}/reject_artifacts",
        json={"reason": "Testing logs"},
    )
    log_res = client.get(f"/api/v3/node_tasks/{node_id}/logs")
    assert len(log_res.json()["logs"]) > 0

    # Clear via POST
    clear_post = client.post(f"/api/v3/node_tasks/{node_id}/clear_logs")
    assert clear_post.status_code == 200
    log_res_after = client.get(f"/api/v3/node_tasks/{node_id}/logs")
    assert len(log_res_after.json()["logs"]) == 0

    # Add logs again and clear via DELETE
    client.post(f"/api/v3/node_tasks/{node_id}/accept_artifacts")
    log_res2 = client.get(f"/api/v3/node_tasks/{node_id}/logs")
    assert len(log_res2.json()["logs"]) > 0

    clear_del = client.delete(f"/api/v3/node_tasks/{node_id}/logs")
    assert clear_del.status_code == 200
    log_res_after2 = client.get(f"/api/v3/node_tasks/{node_id}/logs")
    assert len(log_res_after2.json()["logs"]) == 0
