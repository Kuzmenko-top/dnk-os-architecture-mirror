# --- DNK-MRH-HEADER ---
# mrh_id: "tests_integration_test_shopify_approval_preview"
# purpose: "Integration & API Contract Test Suite for Shopify Approval Preview Pipeline (DNK-SHOPIFY-PILOT-003)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.shopify.conftest import create_shopify_plugin_package, shopify_pilot_setup
from core.supervisor.shopify_api import router as shopify_router
from core.supervisor.shopify_sync_supervisor import ShopifySyncSupervisor


@pytest.fixture
def api_client(shopify_pilot_setup):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_integration_ws"

    manifest, pkg_bytes, _ = create_shopify_plugin_package(
        priv_key, key_id, version="0.1.0", permissions=["products.read"]
    )
    inst.install_plugin(manifest, pkg_bytes, workspace_id=workspace_id)
    inst.activate_plugin(workspace_id, "dnk-shopify-sync", "0.1.0")

    app = FastAPI()
    app.include_router(shopify_router)
    app.state.supervisor = supervisor

    client = TestClient(app)
    return {
        "client": client,
        "supervisor": supervisor,
        "workspace_id": workspace_id,
        "plugin_id": "dnk-shopify-sync",
        "version": "0.1.0",
    }


def sample_product_raw():
    return {
        "id": "gid://shopify/Product/1001",
        "title": "Tactical Hoodie Cyberpunk Edition",
        "handle": "tactical-hoodie-cyberpunk",
        "status": "active",
        "tags": ["cyberpunk", "tactical"],
        "variants": [
            {
                "sku": "DNK-TH-01",
                "price": "120.00",
                "inventory_quantity": 50,
            }
        ],
    }


def test_full_pipeline_e2e(api_client):
    client = api_client["client"]
    ws = api_client["workspace_id"]
    plugin_id = api_client["plugin_id"]
    ver = api_client["version"]

    headers = {
        "X-Workspace-ID": ws,
        "X-Plugin-ID": plugin_id,
        "X-Plugin-Version": ver,
    }

    product_raw = sample_product_raw()

    # Step 1: POST /shopify/products/diff
    diff_resp = client.post(
        "/shopify/products/diff",
        json={"payload": product_raw},
        headers=headers,
    )
    assert diff_resp.status_code == 200
    diff_data = diff_resp.json()
    assert diff_data["write_performed"] is False
    assert diff_data["mutations_count"] == 0
    diff_hash = diff_data["diff_hash"]
    idempotency_key = diff_data["idempotency_key"]

    # Step 2: POST /shopify/products/decision
    existing_state = {
        "external_id": "1001",
        "title": "Old Tactical Hoodie",
        "handle": "tactical-hoodie-cyberpunk",
        "status": "active",
        "sku": "DNK-TH-01",
        "price_minor": 10000,
        "currency": "USD",
        "inventory_quantity": 50,
        "tags": ["cyberpunk"],
    }

    dec_resp = client.post(
        "/shopify/products/decision",
        json={
            "payload": product_raw,
            "existing_state": existing_state,
            "requested_permissions": ["products.read"],
        },
        headers=headers,
    )
    assert dec_resp.status_code == 200
    dec_data = dec_resp.json()
    assert dec_data["decision"] == "APPROVAL_REQUIRED"
    assert dec_data["write_performed"] is False
    assert dec_data["mutations_count"] == 0
    correlation_id = dec_data["correlation_id"]

    # Step 3: POST /shopify/products/approval-preview
    approval_payload = {
        "action_name": "shopify.product_sync.preview",
        "workspace_id": ws,
        "plugin_id": plugin_id,
        "plugin_version": ver,
        "source_product_id": "1001",
        "diff_hash": dec_data["diff_hash"],
        "idempotency_key": idempotency_key,
        "requested_permissions": ["products.read"],
        "proposed_mutations": [
            {
                "field": "title",
                "before": "Old Tactical Hoodie",
                "after": "Tactical Hoodie Cyberpunk Edition",
            }
        ],
        "mode": "simulated_write_plan",
    }

    appr_resp = client.post(
        "/shopify/products/approval-preview",
        json={
            "approval_payload": approval_payload,
            "payload": product_raw,
            "existing_state": existing_state,
        },
        headers=headers,
    )
    assert appr_resp.status_code in (200, 201)
    appr_data = appr_resp.json()
    assert appr_data["status"] == "preview_created"
    assert appr_data["write_performed"] is False
    assert appr_data["mutations_count"] == 0
    approval_id = appr_data["approval_id"]
    arguments_hash = appr_data["arguments_hash"]

    # Step 4: POST /shopify/products/simulated-write-plan
    plan_resp = client.post(
        "/shopify/products/simulated-write-plan",
        json={
            "approval_id": approval_id,
            "approval_payload": approval_payload,
        },
        headers=headers,
    )
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    assert plan_data["mode"] == "simulated_write_plan"
    assert plan_data["executed"] is False
    assert plan_data["write_performed"] is False
    assert plan_data["mutations_count"] == 0
    assert plan_data["network_accessed"] is False
    assert len(plan_data["operations"]) == 1

    # Step 5: GET /shopify/approvals/{approval_id}
    get_appr = client.get(f"/shopify/approvals/{approval_id}", headers=headers)
    assert get_appr.status_code == 200
    appr_record = get_appr.json()
    assert appr_record["consumed"] is True
    assert appr_record["write_performed"] is False

    # Step 6: GET /shopify/reconciliation/{correlation_id}
    rec_resp = client.get(f"/shopify/reconciliation/{correlation_id}", headers=headers)
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["reconciled"] is True
    assert len(rec_data["history"]) >= 1


def test_api_errors_status_codes(api_client):
    client = api_client["client"]
    ws = api_client["workspace_id"]
    plugin_id = api_client["plugin_id"]
    ver = api_client["version"]

    headers = {
        "X-Workspace-ID": ws,
        "X-Plugin-ID": plugin_id,
        "X-Plugin-Version": ver,
    }

    # 403 SHOPIFY_WRITE_FORBIDDEN
    resp_write = client.post(
        "/shopify/products/approval-preview",
        json={
            "approval_payload": {
                "action_name": "shopify.product_sync.preview",
                "workspace_id": ws,
                "plugin_id": plugin_id,
                "plugin_version": ver,
                "source_product_id": "1001",
                "diff_hash": "diff123",
                "idempotency_key": "idemp123",
                "requested_permissions": ["products.read", "products.write"],
                "proposed_mutations": [],
                "mode": "simulated_write_plan",
            }
        },
        headers=headers,
    )
    assert resp_write.status_code == 403
    assert resp_write.json()["error"] == "SHOPIFY_WRITE_FORBIDDEN"

    # 422 CUSTOMER_DATA_FORBIDDEN
    resp_cust = client.post(
        "/shopify/products/approval-preview",
        json={
            "approval_payload": {
                "action_name": "shopify.product_sync.preview",
                "workspace_id": ws,
                "plugin_id": plugin_id,
                "plugin_version": ver,
                "source_product_id": "1001",
                "diff_hash": "diff123",
                "idempotency_key": "idemp123",
                "requested_permissions": ["products.read"],
                "proposed_mutations": [
                    {"field": "customer_address", "before": None, "after": "123 Main St"}
                ],
                "mode": "simulated_write_plan",
            }
        },
        headers=headers,
    )
    assert resp_cust.status_code == 422
    assert resp_cust.json()["error"] == "CUSTOMER_DATA_FORBIDDEN"

    # 403 UNTRUSTED_PLUGIN
    resp_untrusted = client.post(
        "/shopify/products/diff",
        json={"plugin_id": "untrusted-plugin-hacker", "payload": sample_product_raw()},
        headers=headers,
    )
    assert resp_untrusted.status_code == 403
    assert resp_untrusted.json()["error"] == "UNTRUSTED_PLUGIN"
