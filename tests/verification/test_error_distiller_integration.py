# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_error_distiller_integration.py"
# purpose: "Comprehensive test suite for Error Distillation, Self-Healing Hook, and FastAPI Distiller Endpoints."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Antigravity"
# --- END DNK-MRH-HEADER ---

import json
import subprocess
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.services.self_healing_distiller import SelfHealingDistiller
from core.hermes_agent.tools.dnk_distiller_tool import (
    dnk_query_error_solutions,
    dnk_record_error_solution,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_dnk_query_error_solutions_known_pattern():
    # 1. Test Network / Socket egress query
    res_json = dnk_query_error_solutions("ConnectionRefusedError: [Errno 61] Outbound socket blocked")
    data = json.loads(res_json)
    assert data["status"] == "success"
    assert data["has_known_solution"] is True
    assert data["category"] == "NETWORK_SOCKET_EGRESS"
    assert "FIXTURE_MODE" in data["recommended_action"]


def test_dnk_query_error_solutions_unknown_pattern():
    # 2. Test unknown pattern fallback
    res_json = dnk_query_error_solutions("RandomUnseenException12345xyz: unexpected cosmic ray")
    data = json.loads(res_json)
    assert data["status"] == "not_found"
    assert data["has_known_solution"] is False
    assert data["category"] == "UNKNOWN_ERROR"


def test_dnk_record_error_solution_roundtrip():
    # 3. Test recording and immediate querying
    unique_err = "CustomShopifyASTNodeMismatch_test_9999"
    unique_fix = "Use MechanicalTranspiler with Liquid AST visitor."
    root_cause = "Outdated AST node format."

    rec_res = json.loads(dnk_record_error_solution(
        error_text=unique_err,
        solution_text=unique_fix,
        root_cause=root_cause,
        workspace_id="ws-test-001"
    ))
    assert rec_res["status"] == "success"

    query_res = json.loads(dnk_query_error_solutions(unique_err, workspace_id="ws-test-001"))
    assert query_res["status"] == "success"
    assert query_res["has_known_solution"] is True
    assert query_res["recommended_action"] == unique_fix


def test_hermes_post_tool_hook_execution():
    # 4. Test invoking hermes_post_tool_hook.py via subprocess stdin
    payload = {
        "hook_event_name": "post_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": "pytest tests/shopify/test_missing.py"},
        "extra": {
            "status": "error",
            "result": "ModuleNotFoundError: No module named 'apps.api.routers.missing'",
            "error_type": "ModuleNotFoundError",
            "error_message": "No module named 'apps.api.routers.missing'"
        }
    }

    proc = subprocess.run(
        ["python3", "scripts/system/hermes_post_tool_hook.py"],
        input=json.dumps(payload),
        text=True,
        capture_output=True
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() != ""
    out_json = json.loads(proc.stdout)
    assert "context" in out_json
    assert "⚡ [DNK OS SCONES Self-Healing Distiller Advice]" in out_json["context"]
    assert "MODULE_IMPORT_PATH" in out_json["context"]


@pytest.mark.asyncio
async def test_self_healing_distiller_full_loop():
    # 5. Test SelfHealingDistiller resolution & skill packaging
    distiller = SelfHealingDistiller(max_retry=2)
    err = "FastAPI 404: Not Found for /api/v1/distiller/unknown"
    res = await distiller.handle_error(err, context={"endpoint": "/api/v1/distiller/unknown"}, auto_package_skill=True)

    assert res.status in ["resolved_by_llm", "resolved_from_cache"]
    assert res.error_hash != ""
    assert res.solution is not None


def test_fastapi_distiller_endpoints(client):
    # 6. Test REST API endpoints on /api/v1/distiller
    # Query endpoint
    q_resp = client.post(
        "/api/v1/distiller/query",
        headers={"Authorization": "Bearer test_token"},
        json={"error_text": "ModuleNotFoundError: No module named 'apps.test'"}
    )
    assert q_resp.status_code == 200
    assert q_resp.json()["has_known_solution"] is True

    # Record endpoint
    r_resp = client.post(
        "/api/v1/distiller/record",
        headers={"Authorization": "Bearer test_token"},
        json={
            "error_text": "TestApiEndpointError_4444",
            "solution_text": "Mount the router in main.py",
            "root_cause": "Unmounted router",
            "category": "FASTAPI_ROUTER_UNMOUNTED"
        }
    )
    assert r_resp.status_code == 200
    assert r_resp.json()["status"] == "success"

    # Heal endpoint
    h_resp = client.post(
        "/api/v1/distiller/heal",
        headers={"Authorization": "Bearer test_token"},
        json={
            "error_message": "TestHealFailure_5555",
            "stack_trace": "Traceback (most recent call last): ...",
            "auto_package_skill": False
        }
    )
    assert h_resp.status_code == 200
    assert h_resp.json()["status"] in ["resolved_by_llm", "resolved_from_cache"]

    # Stats endpoint
    s_resp = client.get(
        "/api/v1/distiller/stats",
        headers={"Authorization": "Bearer test_token"}
    )
    assert s_resp.status_code == 200
    stats = s_resp.json()
    assert stats["status"] == "active"
    assert stats["total_distillations"] > 0
