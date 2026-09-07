# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_diff_reconciliation"
# purpose: "Unit and Integration Test Suite for Diff Engine, Idempotency & Reconciliation in DNK-SHOPIFY-PILOT-002"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import pytest
from tests.shopify.conftest import create_shopify_plugin_package
from core.supervisor.shopify_diff_engine import (
    compute_product_diff,
    generate_canonical_idempotency_key,
    calculate_json_hash,
)
from core.supervisor.shopify_sync_supervisor import (
    CustomerDataForbiddenError,
)


@pytest.fixture
def active_supervisor_setup(shopify_pilot_setup):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_recon_test"

    manifest, pkg_bytes, _ = create_shopify_plugin_package(
        priv_key, key_id, version="1.0.0", permissions=["products.read"]
    )
    inst.install_plugin(manifest, pkg_bytes, workspace_id=workspace_id)
    inst.activate_plugin(workspace_id, "dnk-shopify-sync", "1.0.0")

    return {
        "supervisor": supervisor,
        "workspace_id": workspace_id,
        "plugin_id": "dnk-shopify-sync",
        "version": "1.0.0",
    }


def sample_payload():
    return {
        "id": 987654321,
        "title": "Tactical Hoodie Cyberpunk Edition",
        "handle": "tactical-hoodie-cyberpunk",
        "status": "active",
        "body_html": "<p>High performance apparel</p>",
        "vendor": "DNK Gear",
        "product_type": "Apparel",
        "tags": ["tactical", "cyberpunk", "new"],
        "variants": [
            {
                "id": 111222333,
                "sku": "DNK-TH-01-L",
                "price": "120.00",
                "inventory_quantity": 50,
                "title": "Large / Black",
            }
        ],
    }


def test_diff_engine_created():
    norm = {
        "external_id": "987654321",
        "title": "Tactical Hoodie Cyberpunk Edition",
        "handle": "tactical-hoodie-cyberpunk",
        "status": "active",
        "vendor": "DNK Gear",
        "price_minor": 12000,
        "inventory_quantity": 50,
    }
    diff, state_hash, diff_hash = compute_product_diff(None, norm)
    assert diff["status"] == "created"
    assert diff["has_changes"] is True
    assert len(diff["summary"]["added_fields"]) == len(norm)
    assert state_hash == calculate_json_hash({})
    assert diff_hash == calculate_json_hash(diff)


def test_diff_engine_unchanged():
    norm = {
        "external_id": "987654321",
        "title": "Tactical Hoodie Cyberpunk Edition",
        "price_minor": 12000,
        "inventory_quantity": 50,
    }
    diff, state_hash, diff_hash = compute_product_diff(norm, norm)
    assert diff["status"] == "unchanged"
    assert diff["has_changes"] is False
    assert diff["summary"]["modified_fields"] == []


def test_diff_engine_updated():
    existing = {
        "external_id": "987654321",
        "title": "Tactical Hoodie Cyberpunk Edition",
        "price_minor": 12000,
        "inventory_quantity": 50,
    }
    incoming = {
        "external_id": "987654321",
        "title": "Tactical Hoodie Cyberpunk Edition (V2)",
        "price_minor": 13500,
        "inventory_quantity": 45,
    }
    diff, state_hash, diff_hash = compute_product_diff(existing, incoming)
    assert diff["status"] == "updated"
    assert diff["has_changes"] is True
    assert "title" in diff["summary"]["modified_fields"]
    assert "price_minor" in diff["summary"]["modified_fields"]
    assert "inventory_quantity" in diff["summary"]["modified_fields"]
    assert diff["field_diffs"]["price_minor"]["old_value"] == 12000
    assert diff["field_diffs"]["price_minor"]["new_value"] == 13500


def test_idempotency_key_deterministic():
    k1 = generate_canonical_idempotency_key("ws_1", "dnk-shopify-sync", "987654321", "hash_abc")
    k2 = generate_canonical_idempotency_key("ws_1", "dnk-shopify-sync", "987654321", "hash_abc")
    k3 = generate_canonical_idempotency_key("ws_1", "dnk-shopify-sync", "987654321", "hash_xyz")

    assert k1 == k2
    assert k1 != k3


def test_reconcile_single_event_and_duplicate(active_supervisor_setup):
    env = active_supervisor_setup
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]
    payload = sample_payload()

    res1 = supervisor.reconcile_single_event(
        workspace_id=ws,
        plugin_id=plugin_id,
        version=ver,
        payload=payload,
        existing_state=None,
    )

    assert res1["status"] == "created"
    assert res1["is_duplicate"] is False
    assert res1["write_performed"] is False
    assert res1["mutations_count"] == 0
    assert "input_hash" in res1
    assert "canonical_state_hash" in res1
    assert "diff_hash" in res1
    assert "idempotency_key" in res1
    assert "correlation_id" in res1
    assert "audit_event_id" in res1
    assert res1["result"] == "success"

    # Repeat exact same call -> duplicate event handling
    res2 = supervisor.reconcile_single_event(
        workspace_id=ws,
        plugin_id=plugin_id,
        version=ver,
        payload=payload,
        existing_state=None,
    )

    assert res2["status"] == "duplicate_ignored"
    assert res2["is_duplicate"] is True
    assert res2["result"] == "duplicate_ignored"
    assert res2["idempotency_key"] == res1["idempotency_key"]
    assert res2["write_performed"] is False
    assert res2["mutations_count"] == 0


def test_reconcile_batch_report(active_supervisor_setup):
    env = active_supervisor_setup
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    p1 = sample_payload()
    p1["id"] = 101

    p2 = sample_payload()
    p2["id"] = 102
    existing_p2 = {
        "external_id": "102",
        "title": "Tactical Hoodie Cyberpunk Edition",
        "handle": "tactical-hoodie-cyberpunk",
        "status": "active",
        "vendor": "DNK Gear",
        "sku": "DNK-TH-01-L",
        "currency": "UAH",
        "price_minor": 12000,
        "inventory_quantity": 50,
        "tags": ["tactical", "cyberpunk", "new"],
    }

    p3 = sample_payload()
    p3["id"] = 103
    norm_p3 = {
        "external_id": "103",
        "title": "Tactical Hoodie Cyberpunk Edition",
        "handle": "tactical-hoodie-cyberpunk",
        "status": "active",
        "sku": "DNK-TH-01-L",
        "price_minor": 12000,
        "currency": "USD",
        "inventory_quantity": 50,
        "tags": ["cyberpunk", "new", "tactical"],
    }

    batch_items = [
        # Item 1: Created (no existing state)
        {"payload": p1, "existing_state": None},
        # Item 2: Updated (existing state with lower price)
        {
            "payload": p2,
            "existing_state": {
                **existing_p2,
                "price_minor": 10000,
            },
        },
        # Item 3: Unchanged (exact same state)
        {
            "payload": p3,
            "existing_state": norm_p3,
        },
        # Item 4: Duplicate of p1
        {"payload": p1, "existing_state": None},
    ]

    report = supervisor.reconcile_batch(
        workspace_id=ws,
        plugin_id=plugin_id,
        version=ver,
        batch_items=batch_items,
    )

    assert report["total_events"] == 4
    assert report["new_items"] == 1
    assert report["updated_items"] == 1
    assert report["unchanged_items"] == 1
    assert report["duplicate_events"] == 1
    assert report["summary_status"] == "reconciled"
    assert report["write_performed"] is False
    assert report["mutations_count"] == 0
    assert report["customer_data_accessed"] is False
    assert report["network_accessed"] is False


def test_customer_data_reconciliation_forbidden(active_supervisor_setup):
    env = active_supervisor_setup
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    payload = sample_payload()
    payload["customer"] = {"email": "john@example.com"}

    with pytest.raises(CustomerDataForbiddenError):
        supervisor.reconcile_single_event(
            workspace_id=ws,
            plugin_id=plugin_id,
            version=ver,
            payload=payload,
        )
