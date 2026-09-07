# --- DNK-MRH-HEADER ---
# mrh_id: "tests_platform_test_platform_deployments_router"
# purpose: "Integration Tests for Platform Deployments & Canary FastAPI Router (DNK-PLATFORM-SCALE-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_initiate_deployment_endpoint():
    payload = {
        "deployment_id": "dep-api-prod-001",
        "app_name": "dnk-api",
        "image_tag": "v2.0.0-rc1",
        "target_traffic_step": 0,
        "auto_rollback_enabled": True,
    }
    response = client.post("/api/v1/platform/deployments/initiate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["deployment_id"] == "dep-api-prod-001"
    assert data["active_environment"] == "blue"
    assert data["candidate_environment"] == "green"


def test_canary_lifecycle_endpoints():
    dep_id = "dep-api-canary-002"
    init_payload = {
        "deployment_id": dep_id,
        "app_name": "dnk-api",
        "image_tag": "v2.1.0",
    }
    # 1. Initiate
    r1 = client.post("/api/v1/platform/deployments/initiate", json=init_payload)
    assert r1.status_code == 201

    # 2. Start Canary (1%)
    r2 = client.post(f"/api/v1/platform/deployments/{dep_id}/canary/start")
    assert r2.status_code == 200
    assert r2.json()["canary_state"]["canary_percentage"] == 1

    # 3. Advance Step (5%)
    r3 = client.post(f"/api/v1/platform/deployments/{dep_id}/canary/advance")
    assert r3.status_code == 200
    assert r3.json()["progress"]["canary_percentage"] == 5

    # 4. Advance Step (25%)
    r4 = client.post(f"/api/v1/platform/deployments/{dep_id}/canary/advance")
    assert r4.status_code == 200
    assert r4.json()["progress"]["canary_percentage"] == 25

    # 5. Status check
    r5 = client.get(f"/api/v1/platform/deployments/{dep_id}/status")
    assert r5.status_code == 200
    status_data = r5.json()
    assert status_data["canary_enabled"] is True
    assert status_data["environments"]["green"]["traffic_percentage"] == 25
    assert status_data["environments"]["blue"]["traffic_percentage"] == 75

    # 6. Promote Candidate
    r6 = client.post(f"/api/v1/platform/deployments/{dep_id}/promote")
    assert r6.status_code == 200
    assert r6.json()["promotion"]["status"] == "promotion_successful"

    # Verify status after promotion
    r7 = client.get(f"/api/v1/platform/deployments/{dep_id}/status")
    assert r7.status_code == 200
    assert r7.json()["active_environment"] == "green"
    assert r7.json()["canary_enabled"] is False


def test_canary_statistical_analysis_endpoint():
    dep_id = "dep-analysis-003"
    client.post(
        "/api/v1/platform/deployments/initiate",
        json={"deployment_id": dep_id, "app_name": "dnk-api", "image_tag": "v2.2.0"},
    )

    analysis_payload = {
        "blue_metrics": {
            "latency_samples": [15.0, 16.0, 15.5, 16.5, 15.2, 16.2, 15.8, 16.0, 15.4, 16.1],
            "p95_ms": 16.5,
            "error_rate": 0.001,
            "request_count": 1000,
        },
        "green_metrics": {
            "latency_samples": [15.1, 15.9, 15.6, 16.4, 15.3, 16.1, 15.7, 16.1, 15.5, 16.0],
            "p95_ms": 16.4,
            "error_rate": 0.001,
            "request_count": 500,
        },
        "statistical_test": "mann_whitney_u",
    }
    resp = client.post(f"/api/v1/platform/deployments/{dep_id}/canary/analyze", json=analysis_payload)
    assert resp.status_code == 200
    analysis = resp.json()["analysis"]
    assert analysis["recommendation"] == "promote"
    assert analysis["is_degraded"] is False


def test_rollback_endpoint():
    dep_id = "dep-rollback-004"
    client.post(
        "/api/v1/platform/deployments/initiate",
        json={"deployment_id": dep_id, "app_name": "dnk-api", "image_tag": "v2.3.0"},
    )
    client.post(f"/api/v1/platform/deployments/{dep_id}/canary/start")

    resp = client.post(
        f"/api/v1/platform/deployments/{dep_id}/rollback",
        json={"reason": "Emergency rollback test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["rollback"]["status"] == "rollback_completed"

    status_resp = client.get(f"/api/v1/platform/deployments/{dep_id}/status")
    assert status_resp.json()["canary_enabled"] is False
    assert status_resp.json()["environments"]["blue"]["traffic_percentage"] == 100


def test_gitops_manifests_endpoint():
    dep_id = "dep-gitops-005"
    client.post(
        "/api/v1/platform/deployments/initiate",
        json={"deployment_id": dep_id, "app_name": "dnk-api", "image_tag": "v2.4.0"},
    )

    resp = client.get(f"/api/v1/platform/deployments/{dep_id}/manifests?provider=nginx")
    assert resp.status_code == 200
    data = resp.json()
    assert "argo_rollout" in data
    assert "argo_application" in data
    assert "flux_kustomization" in data
    assert "yaml_bundle" in data
    assert "apiVersion: argoproj.io/v1alpha1" in data["yaml_bundle"]


def test_prometheus_metrics_endpoint():
    resp = client.get("/api/v1/platform/deployments/metrics")
    assert resp.status_code == 200
    assert "dnk_platform_deployment_traffic_percentage" in resp.text
    assert "dnk_platform_deployment_canary_active" in resp.text
