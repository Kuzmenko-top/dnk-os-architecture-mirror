# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_product_sync_pilot"
# purpose: "Positive Lifecycle Test Suite for Shopify Product Sync Pilot (DNK-SHOPIFY-PILOT-001)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

import pytest
from tests.shopify.conftest import create_shopify_plugin_package
from core.supervisor.shopify_sync_supervisor import UntrustedPluginError


def test_positive_pilot_dry_run_sync(shopify_pilot_setup, valid_shopify_product_payload):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_ws_01"
    actor_id = "mentor_tester"

    manifest, pkg_bytes, _ = create_shopify_plugin_package(priv_key, key_id, version="0.1.0")

    # Install & activate plugin
    inst.install_plugin(raw_manifest=manifest, package_bytes=pkg_bytes, workspace_id=workspace_id, actor_id=actor_id)
    inst.activate_plugin(workspace_id=workspace_id, plugin_id="dnk-shopify-sync", version="0.1.0", actor_id=actor_id)

    # Execute dry-run sync via Supervisor
    result = supervisor.execute_dry_run_sync(
        workspace_id=workspace_id,
        plugin_id="dnk-shopify-sync",
        version="0.1.0",
        payload=valid_shopify_product_payload,
        actor_id=actor_id,
    )

    assert result["plugin_id"] == "dnk-shopify-sync"
    assert result["mode"] == "dry_run"
    assert result["write_performed"] is False
    assert result["mutations"] == []
    assert result["normalized"]["price_minor"] == 4900

    # Verify audit event emission
    audit_logs = inst.audit_logger.get_logs_for_plugin("dnk-shopify-sync")
    dry_run_logs = [log for log in audit_logs if log["action"] == "plugin.execution.dry_run"]
    assert len(dry_run_logs) == 1

    log_data = dry_run_logs[0]["details"]
    assert log_data["workspace_id"] == workspace_id
    assert log_data["plugin_id"] == "dnk-shopify-sync"
    assert log_data["mode"] == "dry_run"
    assert log_data["write_performed"] is False
    assert log_data["mutations_count"] == 0
    assert "input_hash" in log_data
    assert "output_hash" in log_data
    assert log_data["permissions"]["granted"] == ["products.read"]


def test_dry_run_idempotency_and_hash_consistency(shopify_pilot_setup, valid_shopify_product_payload):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_ws_idempotency"

    manifest, pkg_bytes, _ = create_shopify_plugin_package(priv_key, key_id, version="0.1.0")
    inst.install_plugin(manifest, pkg_bytes, workspace_id=workspace_id)
    inst.activate_plugin(workspace_id, "dnk-shopify-sync", "0.1.0")

    res1 = supervisor.execute_dry_run_sync(workspace_id, "dnk-shopify-sync", "0.1.0", valid_shopify_product_payload)
    res2 = supervisor.execute_dry_run_sync(workspace_id, "dnk-shopify-sync", "0.1.0", valid_shopify_product_payload)

    assert res1 == res2

    logs = [l for l in inst.audit_logger.get_logs_for_plugin("dnk-shopify-sync") if l["action"] == "plugin.execution.dry_run"]
    assert len(logs) == 2
    assert logs[0]["details"]["input_hash"] == logs[1]["details"]["input_hash"]
    assert logs[0]["details"]["output_hash"] == logs[1]["details"]["output_hash"]


def test_cross_workspace_execution_rejected(shopify_pilot_setup, valid_shopify_product_payload):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]

    manifest, pkg_bytes, _ = create_shopify_plugin_package(priv_key, key_id, version="0.1.0")
    # Installed in workspace_A only
    inst.install_plugin(manifest, pkg_bytes, workspace_id="workspace_A")
    inst.activate_plugin("workspace_A", "dnk-shopify-sync", "0.1.0")

    # Attempt execution in workspace_B
    with pytest.raises(UntrustedPluginError, match="is not installed in workspace 'workspace_B'"):
        supervisor.execute_dry_run_sync("workspace_B", "dnk-shopify-sync", "0.1.0", valid_shopify_product_payload)
