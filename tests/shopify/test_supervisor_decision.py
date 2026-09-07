# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_supervisor_decision"
# purpose: "Unit Test Suite for Shopify Supervisor Decision Engine (DNK-SHOPIFY-PILOT-003)"
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
)


@pytest.fixture
def decision_test_env(shopify_pilot_setup):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_decision_ws"

    manifest, pkg_bytes, _ = create_shopify_plugin_package(
        priv_key, key_id, version="0.1.0", permissions=["products.read"]
    )
    inst.install_plugin(manifest, pkg_bytes, workspace_id=workspace_id)
    inst.activate_plugin(workspace_id, "dnk-shopify-sync", "0.1.0")

    return {
        "supervisor": supervisor,
        "installer": inst,
        "workspace_id": workspace_id,
        "plugin_id": "dnk-shopify-sync",
        "version": "0.1.0",
    }


def sample_product():
    return {
        "id": "1001",
        "title": "Tactical Hoodie Cyberpunk Edition",
        "handle": "tactical-hoodie-cyberpunk",
        "status": "active",
        "vendor": "DNK Gear",
        "product_type": "Apparel",
        "tags": ["tactical", "cyberpunk"],
        "variants": [
            {
                "id": 2001,
                "sku": "DNK-TH-01",
                "price": "120.00",
                "inventory_quantity": 50,
            }
        ],
    }


def test_decision_unchanged_diff_returns_no_changes(decision_test_env):
    env = decision_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    prod = sample_product()
    # Normalized representation as existing state
    existing_state = {
        "external_id": "1001",
        "title": "Tactical Hoodie Cyberpunk Edition",
        "handle": "tactical-hoodie-cyberpunk",
        "status": "active",
        "sku": "DNK-TH-01",
        "price_minor": 12000,
        "currency": "USD",
        "inventory_quantity": 50,
        "tags": ["cyberpunk", "tactical"],
    }

    decision = supervisor.evaluate_supervisor_decision(
        workspace_id=ws,
        plugin_id=plugin_id,
        version=ver,
        payload=prod,
        existing_state=existing_state,
        requested_permissions=["products.read"],
    )

    assert decision["decision"] == "NO_CHANGES"
    assert decision["reason"] == "no_changes_detected"
    assert decision["product_id"] == "1001"
    assert decision["write_performed"] is False
    assert decision["mutations_count"] == 0
    assert decision["customer_data_accessed"] is False
    assert decision["network_accessed"] is False
    assert "diff_hash" in decision
    assert "idempotency_key" in decision


def test_decision_changed_diff_returns_approval_required(decision_test_env):
    env = decision_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    prod = sample_product()
    # Existing state with different title and price
    existing_state = {
        "external_id": "1001",
        "title": "Old Tactical Hoodie",
        "handle": "tactical-hoodie-cyberpunk",
        "status": "active",
        "vendor": "DNK Gear",
        "sku": "DNK-TH-01",
        "price_minor": 9900,
        "currency": "USD",
        "inventory_quantity": 50,
        "tags": ["cyberpunk", "tactical"],
    }

    decision = supervisor.evaluate_supervisor_decision(
        workspace_id=ws,
        plugin_id=plugin_id,
        version=ver,
        payload=prod,
        existing_state=existing_state,
        requested_permissions=["products.read"],
    )

    assert decision["decision"] == "APPROVAL_REQUIRED"
    assert decision["reason"] == "product_fields_changed"
    assert decision["product_id"] == "1001"
    assert decision["write_performed"] is False
    assert decision["mutations_count"] == 0
    assert decision["customer_data_accessed"] is False
    assert decision["network_accessed"] is False


def test_decision_customer_data_blocked_policy(decision_test_env):
    env = decision_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    prod = sample_product()
    prod["customer"] = {"email": "user@target.com"}

    with pytest.raises(CustomerDataForbiddenError):
        supervisor.evaluate_supervisor_decision(
            workspace_id=ws,
            plugin_id=plugin_id,
            version=ver,
            payload=prod,
            existing_state=None,
        )


def test_decision_missing_products_read_blocked(decision_test_env):
    env = decision_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    prod = sample_product()

    with pytest.raises(ApprovalPermissionDeniedError):
        supervisor.evaluate_supervisor_decision(
            workspace_id=ws,
            plugin_id=plugin_id,
            version=ver,
            payload=prod,
            requested_permissions=[],
        )


def test_decision_products_write_always_rejected(decision_test_env):
    env = decision_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    prod = sample_product()

    with pytest.raises(ShopifyPilotWriteForbiddenError):
        supervisor.evaluate_supervisor_decision(
            workspace_id=ws,
            plugin_id=plugin_id,
            version=ver,
            payload=prod,
            requested_permissions=["products.read", "products.write"],
        )


def test_decision_duplicate_request_idempotent(decision_test_env):
    env = decision_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    plugin_id = env["plugin_id"]
    ver = env["version"]

    prod = sample_product()

    dec1 = supervisor.evaluate_supervisor_decision(
        workspace_id=ws,
        plugin_id=plugin_id,
        version=ver,
        payload=prod,
        requested_permissions=["products.read"],
    )

    dec2 = supervisor.evaluate_supervisor_decision(
        workspace_id=ws,
        plugin_id=plugin_id,
        version=ver,
        payload=prod,
        requested_permissions=["products.read"],
    )

    assert dec1["decision"] == "APPROVAL_REQUIRED"
    assert dec2["decision"] == "DUPLICATE_REQUEST"
    assert dec2["is_duplicate"] is True
    assert dec2["idempotency_key"] == dec1["idempotency_key"]
    assert dec2["write_performed"] is False
    assert dec2["mutations_count"] == 0


def test_decision_untrusted_plugin_blocked(decision_test_env):
    env = decision_test_env
    supervisor = env["supervisor"]
    ws = env["workspace_id"]
    prod = sample_product()

    with pytest.raises(UntrustedPluginError):
        supervisor.evaluate_supervisor_decision(
            workspace_id=ws,
            plugin_id="malicious-plugin",
            version="1.0.0",
            payload=prod,
        )
