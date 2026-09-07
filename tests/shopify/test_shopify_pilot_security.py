# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_shopify_pilot_security"
# purpose: "Negative Security Test Suite for Shopify Product Sync Pilot (DNK-SHOPIFY-PILOT-001)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

import pytest
from tests.shopify.conftest import create_shopify_plugin_package
from core.supervisor.shopify_sync_supervisor import (
    InvalidShopifyProductPayloadError,
    ShopifyPilotPermissionDeniedError,
    ShopifyPilotWriteForbiddenError,
    UntrustedPluginError,
    CustomerDataForbiddenError,
    DryRunMutationDetectedError,
    PluginQuarantinedError,
)


def test_security_write_permission_forbidden(shopify_pilot_setup, valid_shopify_product_payload):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_sec_write"

    # Plugin requests products.write permission
    manifest, pkg_bytes, _ = create_shopify_plugin_package(
        priv_key, key_id, version="0.1.0", permissions=["products.read", "products.write"]
    )
    inst.install_plugin(manifest, pkg_bytes, workspace_id=workspace_id)
    inst.activate_plugin(workspace_id, "dnk-shopify-sync", "0.1.0")

    with pytest.raises(ShopifyPilotWriteForbiddenError, match="Permission 'products.write' is forbidden in pilot mode"):
        supervisor.execute_dry_run_sync(workspace_id, "dnk-shopify-sync", "0.1.0", valid_shopify_product_payload)


def test_security_missing_read_permission(shopify_pilot_setup, valid_shopify_product_payload):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_sec_no_read"

    # Plugin permissions do not include products.read
    manifest, pkg_bytes, _ = create_shopify_plugin_package(
        priv_key, key_id, version="0.1.0", permissions=["audit.write"]
    )
    inst.install_plugin(manifest, pkg_bytes, workspace_id=workspace_id)
    inst.activate_plugin(workspace_id, "dnk-shopify-sync", "0.1.0")

    with pytest.raises(ShopifyPilotPermissionDeniedError, match="Permission 'products.read' is required"):
        supervisor.execute_dry_run_sync(workspace_id, "dnk-shopify-sync", "0.1.0", valid_shopify_product_payload)


def test_security_customer_data_rejected(shopify_pilot_setup, valid_shopify_product_payload):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_sec_customer"

    manifest, pkg_bytes, _ = create_shopify_plugin_package(priv_key, key_id, version="0.1.0")
    inst.install_plugin(manifest, pkg_bytes, workspace_id=workspace_id)
    inst.activate_plugin(workspace_id, "dnk-shopify-sync", "0.1.0")

    forbidden_fields = ["customer", "email", "phone", "address", "order", "payment", "access_token", "client_secret", "webhook_secret"]

    for forbidden in forbidden_fields:
        payload_with_forbidden = dict(valid_shopify_product_payload)
        payload_with_forbidden[forbidden] = "sensitive_value_123"

        with pytest.raises(CustomerDataForbiddenError, match="Forbidden field or credentials detected"):
            supervisor.execute_dry_run_sync(workspace_id, "dnk-shopify-sync", "0.1.0", payload_with_forbidden)


def test_security_invalid_product_payload(shopify_pilot_setup):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_sec_invalid"

    manifest, pkg_bytes, _ = create_shopify_plugin_package(priv_key, key_id, version="0.1.0")
    inst.install_plugin(manifest, pkg_bytes, workspace_id=workspace_id)
    inst.activate_plugin(workspace_id, "dnk-shopify-sync", "0.1.0")

    bad_payload = {"id": "1001", "title": "Incomplete Product"}

    with pytest.raises(InvalidShopifyProductPayloadError, match="Missing required Shopify product field"):
        supervisor.execute_dry_run_sync(workspace_id, "dnk-shopify-sync", "0.1.0", bad_payload)


def test_security_revoked_key_leads_to_quarantine(shopify_pilot_setup, valid_shopify_product_payload):
    inst = shopify_pilot_setup["installer"]
    supervisor = shopify_pilot_setup["supervisor"]
    registry = shopify_pilot_setup["registry"]
    key_id = shopify_pilot_setup["key_id"]
    priv_key = shopify_pilot_setup["priv_key"]
    workspace_id = "sandbox_sec_revoked"

    manifest, pkg_bytes, _ = create_shopify_plugin_package(priv_key, key_id, version="0.1.0")
    inst.install_plugin(manifest, pkg_bytes, workspace_id=workspace_id)
    inst.activate_plugin(workspace_id, "dnk-shopify-sync", "0.1.0")

    # Revoke key in registry
    registry.revoke_key(key_id)

    with pytest.raises(PluginQuarantinedError, match="signing key 'shopify_test_key_01' is inactive or revoked"):
        supervisor.execute_dry_run_sync(workspace_id, "dnk-shopify-sync", "0.1.0", valid_shopify_product_payload)
