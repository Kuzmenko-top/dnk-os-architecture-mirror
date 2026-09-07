# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_approval_binding"
# purpose: "Unit Test Suite for Canonical Approval Binding and Hash Determinism (DNK-SHOPIFY-PILOT-003)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import pytest
from tests.shopify.conftest import create_shopify_plugin_package
from core.supervisor.shopify_diff_engine import compute_canonical_arguments_hash
from core.supervisor.shopify_sync_supervisor import (
    DuplicateApprovalRequestError,
    InvalidDiffBindingError,
    InvalidApprovalPayloadError,
)


@pytest.fixture
def approval_test_env(shopify_pilot_setup):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_approval_ws"

    manifest, pkg_bytes, _ = create_shopify_plugin_package(
        priv_key, key_id, version="0.1.0", permissions=["products.read"]
    )
    inst.install_plugin(manifest, pkg_bytes, workspace_id=workspace_id)
    inst.activate_plugin(workspace_id, "dnk-shopify-sync", "0.1.0")

    return {
        "supervisor": supervisor,
        "workspace_id": workspace_id,
        "plugin_id": "dnk-shopify-sync",
        "version": "0.1.0",
    }


def sample_approval_payload():
    return {
        "action_name": "shopify.product_sync.preview",
        "workspace_id": "sandbox_approval_ws",
        "plugin_id": "dnk-shopify-sync",
        "plugin_version": "0.1.0",
        "source_product_id": "1001",
        "diff_hash": "diff_hash_1234567890abcdef",
        "idempotency_key": "idemp_key_1234567890abcdef",
        "requested_permissions": ["products.read"],
        "proposed_mutations": [
            {
                "field": "title",
                "before": "Old title",
                "after": "New title",
            }
        ],
        "mode": "simulated_write_plan",
    }


def test_canonical_approval_payload_stable_hash():
    p1 = sample_approval_payload()
    p2 = sample_approval_payload()

    h1 = compute_canonical_arguments_hash(p1)
    h2 = compute_canonical_arguments_hash(p2)

    assert h1 == h2
    assert isinstance(h1, str)
    assert len(h1) == 64  # SHA256 hex string


def test_reordered_json_keys_and_arrays_produce_same_hash():
    # p1 with keys in default order
    p1 = sample_approval_payload()

    # p2 with reversed keys and permissions array order
    p2 = {
        "mode": "simulated_write_plan",
        "proposed_mutations": [
            {
                "after": "New title",
                "before": "Old title",
                "field": "title",
            }
        ],
        "requested_permissions": ["products.read"],
        "idempotency_key": "idemp_key_1234567890abcdef",
        "diff_hash": "diff_hash_1234567890abcdef",
        "source_product_id": "1001",
        "plugin_version": "0.1.0",
        "plugin_id": "dnk-shopify-sync",
        "workspace_id": "sandbox_approval_ws",
        "action_name": "shopify.product_sync.preview",
    }

    h1 = compute_canonical_arguments_hash(p1)
    h2 = compute_canonical_arguments_hash(p2)

    assert h1 == h2


def test_changed_diff_produces_different_hash():
    p1 = sample_approval_payload()
    p2 = sample_approval_payload()
    p2["diff_hash"] = "diff_hash_CHANGED_9876543210"

    h1 = compute_canonical_arguments_hash(p1)
    h2 = compute_canonical_arguments_hash(p2)

    assert h1 != h2


def test_changed_product_id_invalidates_binding():
    p1 = sample_approval_payload()
    p2 = sample_approval_payload()
    p2["source_product_id"] = "9999"

    h1 = compute_canonical_arguments_hash(p1)
    h2 = compute_canonical_arguments_hash(p2)

    assert h1 != h2


def test_changed_workspace_invalidates_binding():
    p1 = sample_approval_payload()
    p2 = sample_approval_payload()
    p2["workspace_id"] = "production_ws"

    h1 = compute_canonical_arguments_hash(p1)
    h2 = compute_canonical_arguments_hash(p2)

    assert h1 != h2


def test_changed_plugin_version_invalidates_binding():
    p1 = sample_approval_payload()
    p2 = sample_approval_payload()
    p2["plugin_version"] = "2.0.0"

    h1 = compute_canonical_arguments_hash(p1)
    h2 = compute_canonical_arguments_hash(p2)

    assert h1 != h2


def test_approval_preview_created_without_mutation(approval_test_env):
    env = approval_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    payload = sample_approval_payload()

    appr = supervisor.create_approval_preview(
        workspace_id=ws,
        plugin_id=plugin_id,
        version=ver,
        approval_payload=payload,
    )

    assert appr["status"] == "preview_created"
    assert "approval_id" in appr
    assert appr["arguments_hash"] == compute_canonical_arguments_hash(payload)
    assert appr["write_performed"] is False
    assert appr["mutations_count"] == 0
    assert appr["executed"] is False
    assert appr["customer_data_accessed"] is False
    assert appr["network_accessed"] is False


def test_duplicate_approval_request_handling(approval_test_env):
    env = approval_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    payload = sample_approval_payload()

    appr1 = supervisor.create_approval_preview(
        workspace_id=ws,
        plugin_id=plugin_id,
        version=ver,
        approval_payload=payload,
    )
    assert "approval_id" in appr1

    with pytest.raises(DuplicateApprovalRequestError):
        supervisor.create_approval_preview(
            workspace_id=ws,
            plugin_id=plugin_id,
            version=ver,
            approval_payload=payload,
        )


def test_approval_preview_mismatched_diff_hash_fails(approval_test_env):
    env = approval_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    payload = sample_approval_payload()
    payload["diff_hash"] = "wrong_diff_hash"

    raw_product = {
        "id": "1001",
        "title": "Tactical Hoodie Cyberpunk Edition",
        "handle": "tactical-hoodie-cyberpunk",
        "status": "active",
        "variants": [{"sku": "DNK-TH-01", "price": "120.00", "inventory_quantity": 50}],
    }

    with pytest.raises(InvalidDiffBindingError):
        supervisor.create_approval_preview(
            workspace_id=ws,
            plugin_id=plugin_id,
            version=ver,
            approval_payload=payload,
            payload=raw_product,
        )
