# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_approval_security"
# purpose: "Security & Isolation Negative Test Suite for Shopify Approval Engine (DNK-SHOPIFY-PILOT-003)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import pytest
from tests.shopify.conftest import create_shopify_plugin_package
from core.supervisor.shopify_sync_supervisor import (
    CustomerDataForbiddenError,
    ShopifyPilotWriteForbiddenError,
    ApprovalPermissionDeniedError,
    UntrustedPluginError,
    InvalidDiffBindingError,
)


@pytest.fixture
def security_test_env(shopify_pilot_setup):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_security_ws"

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
        "workspace_id": "sandbox_security_ws",
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


def test_approval_products_write_permission_rejected(security_test_env):
    env = security_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    payload = sample_approval_payload()
    payload["requested_permissions"] = ["products.read", "products.write"]

    with pytest.raises(ShopifyPilotWriteForbiddenError):
        supervisor.create_approval_preview(
            workspace_id=ws,
            plugin_id=plugin_id,
            version=ver,
            approval_payload=payload,
        )


def test_approval_customer_data_forbidden(security_test_env):
    env = security_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    payload = sample_approval_payload()
    payload["proposed_mutations"].append({
        "field": "customer_email",
        "before": None,
        "after": "john@example.com"
    })

    with pytest.raises(CustomerDataForbiddenError):
        supervisor.create_approval_preview(
            workspace_id=ws,
            plugin_id=plugin_id,
            version=ver,
            approval_payload=payload,
        )


def test_workspace_isolation_enforced(security_test_env):
    env = security_test_env
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
    appr_id = appr["approval_id"]

    # Trying to access approval from a different workspace raises InvalidDiffBindingError
    with pytest.raises(InvalidDiffBindingError):
        supervisor.get_approval_by_id(appr_id, workspace_id="other_workspace_ws")

    with pytest.raises(InvalidDiffBindingError):
        supervisor.generate_simulated_write_plan(
            approval_id=appr_id,
            workspace_id="other_workspace_ws",
            plugin_id=plugin_id,
            version=ver,
            approval_payload=payload,
        )


def test_audit_logs_contain_hashes_and_no_secrets(security_test_env):
    env = security_test_env
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
    appr_id = appr["approval_id"]

    _ = supervisor.generate_simulated_write_plan(
        approval_id=appr_id,
        workspace_id=ws,
        plugin_id=plugin_id,
        version=ver,
        approval_payload=payload,
    )

    # Check audit logs
    audit_logs = supervisor.audit_logger.logs
    assert len(audit_logs) >= 3

    found_preview = False
    found_bound = False
    found_plan = False

    for record in audit_logs:
        details = record.get("details", {})
        action = record.get("action", "")

        # Check required fields
        if action in [
            "plugin.approval.preview_created",
            "plugin.approval.bound",
            "plugin.simulated_write_plan.created",
        ]:
            assert "event_id" in details
            assert "event_type" in details
            assert details["workspace_id"] == ws
            assert details["plugin_id"] == plugin_id
            assert details["plugin_version"] == ver
            assert details["product_id"] == "1001"
            assert "correlation_id" in details
            assert "idempotency_key" in details
            assert "diff_hash" in details
            assert "arguments_hash" in details
            assert details["executed"] is False
            assert details["write_performed"] is False
            assert details["mutations_count"] == 0
            assert details["network_accessed"] is False

            # Verify no secret or customer email leaked
            log_str = str(record).lower()
            assert "private_key" not in log_str
            assert "password" not in log_str
            assert "secret" not in log_str
            assert "@example.com" not in log_str

        if action == "plugin.approval.preview_created":
            found_preview = True
        elif action == "plugin.approval.bound":
            found_bound = True
        elif action == "plugin.simulated_write_plan.created":
            found_plan = True

    assert found_preview is True
    assert found_bound is True
    assert found_plan is True
