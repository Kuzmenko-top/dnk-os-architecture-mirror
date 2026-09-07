# --- DNK-MRH-HEADER ---
# mrh_id: "tests_integration_test_shopify_product_sync_dry_run"
# purpose: "End-to-End Integration Test Suite for Shopify Product Sync Dry-Run (DNK-SHOPIFY-PILOT-001)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from core.plugins.plugin_models import PluginLifecycleState
from tests.shopify.conftest import create_shopify_plugin_package, shopify_pilot_setup, valid_shopify_product_payload


def test_e2e_shopify_product_sync_dry_run_flow(shopify_pilot_setup, valid_shopify_product_payload):
    """
    E2E Verification of:
    mock Shopify payload -> Supervisor ingress -> permission check -> trusted signed plugin ->
    normalization -> zero mutations -> immutable audit event -> response
    """
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_e2e_ws_01"
    actor_id = "supervisor_e2e_runner"

    # 1. Package creation & signing
    manifest, pkg_bytes, _ = create_shopify_plugin_package(priv_key, key_id, version="0.1.0")

    # 2. Plugin installation
    inst_record = inst.install_plugin(
        raw_manifest=manifest,
        package_bytes=pkg_bytes,
        workspace_id=workspace_id,
        actor_id=actor_id,
    )
    assert inst_record.install_state == PluginLifecycleState.INSTALLED.value

    # 3. Plugin activation
    act_record = inst.activate_plugin(
        workspace_id=workspace_id,
        plugin_id="dnk-shopify-sync",
        version="0.1.0",
        actor_id=actor_id,
    )
    assert act_record.install_state == PluginLifecycleState.ACTIVE.value

    # 4. Supervisor execution
    result = supervisor.execute_dry_run_sync(
        workspace_id=workspace_id,
        plugin_id="dnk-shopify-sync",
        version="0.1.0",
        payload=valid_shopify_product_payload,
        actor_id=actor_id,
    )

    # 5. Result contract assertions
    assert result["plugin_id"] == "dnk-shopify-sync"
    assert result["mode"] == "dry_run"
    assert result["operation"] == "product_sync_preview"
    assert result["source_product_id"] == "gid://shopify/Product/1001"
    assert result["write_performed"] is False
    assert result["mutations"] == []

    norm = result["normalized"]
    assert norm["external_id"] == "1001"
    assert norm["title"] == "ReBurn Sample Product"
    assert norm["handle"] == "reburn-sample-product"
    assert norm["status"] == "active"
    assert norm["sku"] == "RB-TEST-001"
    assert norm["price_minor"] == 4900
    assert norm["currency"] == "USD"
    assert norm["inventory_quantity"] == 3
    assert norm["tags"] == ["pilot", "reburn"]

    # 6. Audit trail verification
    audit_logs = inst.audit_logger.get_logs_for_plugin("dnk-shopify-sync")
    actions = [log["action"] for log in audit_logs]
    assert "plugin.install.started" in actions
    assert "plugin.install.completed" in actions
    assert "plugin.activation.completed" in actions
    assert "plugin.execution.dry_run" in actions

    dry_run_entry = [log for log in audit_logs if log["action"] == "plugin.execution.dry_run"][0]
    dt = dry_run_entry["details"]
    assert dt["workspace_id"] == workspace_id
    assert dt["plugin_id"] == "dnk-shopify-sync"
    assert dt["plugin_version"] == "0.1.0"
    assert dt["source"] == "mock_test_store"
    assert dt["source_product_id"] == "gid://shopify/Product/1001"
    assert dt["mode"] == "dry_run"
    assert dt["write_performed"] is False
    assert dt["mutations_count"] == 0
    assert len(dt["input_hash"]) == 64
    assert len(dt["output_hash"]) == 64
    assert dt["result"] == "success"
    assert dt["actor"] == actor_id

    # Ensure no secrets or customer payload data leaked into audit trail
    for log in audit_logs:
        log_str = str(log).lower()
        assert "access_token" not in log_str
        assert "client_secret" not in log_str
        assert "sensitive_value" not in log_str
