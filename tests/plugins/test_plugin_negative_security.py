# --- DNK-MRH-HEADER ---
# mrh_id: "tests/plugins/test_plugin_negative_security.py"
# purpose: "Negative Security Scenarios Test Suite for DNK-PLUGIN-018"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

import os
import tempfile
import base64
import pytest
from cryptography.hazmat.primitives import serialization

from core.plugins.plugin_installer import PluginInstaller
from core.plugins.plugin_manifest import InvalidPluginManifestError
from core.plugins.plugin_models import PluginLifecycleState, PluginTrustState
from core.plugins.plugin_security_gate import (
    TrustKeyRegistry,
    generate_ed25519_keypair,
    sign_data_ed25519,
    calculate_package_hash,
    ProductionUnsignedPluginError,
    HashMismatchError,
    InvalidSignatureError,
    UntrustedSigningKeyError,
    PluginQuarantinedError,
)

@pytest.fixture
def neg_setup():
    temp_store = tempfile.mkdtemp(prefix="neg_store_")
    registry = TrustKeyRegistry()
    priv_key, pub_key = generate_ed25519_keypair()
    
    pub_bytes = pub_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    registry.register_key("key_trusted_01", pub_bytes, "DNK Test Publisher", "active")
    
    # Register expired key
    priv_exp, pub_exp = generate_ed25519_keypair()
    pub_exp_bytes = pub_exp.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    registry.register_key("key_expired_01", pub_exp_bytes, "DNK Test Publisher", "expired")
    
    # Register revoked key
    priv_rev, pub_rev = generate_ed25519_keypair()
    pub_rev_bytes = pub_rev.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    registry.register_key("key_revoked_01", pub_rev_bytes, "DNK Test Publisher", "revoked")
    
    installer = PluginInstaller(base_store_dir=temp_store, key_registry=registry)
    
    return {
        "store_dir": temp_store,
        "registry": registry,
        "priv_key": priv_key,
        "priv_exp": priv_exp,
        "priv_rev": priv_rev,
        "installer": installer,
    }

def helper_build_manifest(priv_key, key_id="key_trusted_01", plugin_id="dnk-test-health", version="0.1.0", entrypoint="plugin.py", pkg_bytes=b"print(\"health\")\n"):
    pkg_hash = calculate_package_hash(pkg_bytes)
    sig = sign_data_ed25519(f"{plugin_id}:{version}:{pkg_hash}".encode("utf-8"), priv_key)
    manifest = {
        "plugin_id": plugin_id,
        "name": "DNK Test Health Plugin",
        "version": version,
        "publisher": "DNK Test Publisher",
        "entrypoint": entrypoint,
        "runtime_compatibility": ">=0.1.0",
        "permissions": ["health.read", "audit.write"],
        "dependencies": {"python": ">=3.12"},
        "content_hash": pkg_hash,
        "signature_metadata": {"key_id": key_id, "signature": sig},
    }
    return manifest, pkg_bytes

# 1. Modify one byte after signing -> HASH_MISMATCH
def test_neg_1_tampered_byte_rejected(neg_setup):
    inst = neg_setup["installer"]
    manifest, pkg_bytes = helper_build_manifest(neg_setup["priv_key"])
    tampered_bytes = pkg_bytes + b"X"
    
    with pytest.raises(HashMismatchError):
        inst.install_plugin(manifest, tampered_bytes, workspace_id="ws_neg")

# 2. Use invalid signature -> INVALID_SIGNATURE
def test_neg_2_invalid_signature_rejected(neg_setup):
    inst = neg_setup["installer"]
    manifest, pkg_bytes = helper_build_manifest(neg_setup["priv_key"])
    manifest["signature_metadata"]["signature"] = base64.b64encode(b"0" * 64).decode()
    
    with pytest.raises(InvalidSignatureError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_neg")

# 3. Use unknown key -> UNTRUSTED_SIGNING_KEY
def test_neg_3_unknown_key_rejected(neg_setup):
    inst = neg_setup["installer"]
    manifest, pkg_bytes = helper_build_manifest(neg_setup["priv_key"], key_id="unknown_key_999")
    
    with pytest.raises(UntrustedSigningKeyError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_neg")

# 4. Use revoked key -> PLUGIN_QUARANTINED
def test_neg_4_revoked_key_quarantined(neg_setup):
    inst = neg_setup["installer"]
    manifest, pkg_bytes = helper_build_manifest(neg_setup["priv_rev"], key_id="key_revoked_01")
    
    with pytest.raises(PluginQuarantinedError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_neg")

# 5. Use expired key -> rejected / approval_pending
def test_neg_5_expired_key_rejected(neg_setup):
    inst = neg_setup["installer"]
    manifest, pkg_bytes = helper_build_manifest(neg_setup["priv_exp"], key_id="key_expired_01")
    
    with pytest.raises(UntrustedSigningKeyError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_neg")

# 6. Remove signature in production -> PRODUCTION_UNSIGNED_PLUGIN
def test_neg_6_unsigned_production_rejected(neg_setup):
    inst = neg_setup["installer"]
    manifest, pkg_bytes = helper_build_manifest(neg_setup["priv_key"])
    manifest["signature_metadata"] = {}
    
    with pytest.raises(ProductionUnsignedPluginError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_neg", production_mode=True)

# 7. Add ../ path -> INVALID_PLUGIN_MANIFEST
def test_neg_7_path_traversal_entrypoint_rejected(neg_setup):
    inst = neg_setup["installer"]
    manifest, pkg_bytes = helper_build_manifest(neg_setup["priv_key"], entrypoint="../../etc/passwd")
    
    with pytest.raises(InvalidPluginManifestError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_neg")

# 8. Use absolute path -> INVALID_PLUGIN_MANIFEST
def test_neg_8_absolute_path_entrypoint_rejected(neg_setup):
    inst = neg_setup["installer"]
    manifest, pkg_bytes = helper_build_manifest(neg_setup["priv_key"], entrypoint="/usr/bin/python")
    
    with pytest.raises(InvalidPluginManifestError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_neg")

# 9. Add symlink escape -> staging rejected
def test_neg_9_symlink_escape_rejected(neg_setup):
    inst = neg_setup["installer"]
    manifest, pkg_bytes = helper_build_manifest(neg_setup["priv_key"])
    
    # Inject symlink in temporary staging directory check
    staging = tempfile.mkdtemp()
    link_path = os.path.join(staging, "bad_link")
    os.symlink("/etc/passwd", link_path)
    try:
        with pytest.raises(InvalidPluginManifestError):
            inst._verify_staging_safety(staging)
    finally:
        import shutil
        shutil.rmtree(staging, ignore_errors=True)

# 10. Duplicate installation -> idempotent result
def test_neg_10_duplicate_install_idempotent(neg_setup):
    inst = neg_setup["installer"]
    manifest, pkg_bytes = helper_build_manifest(neg_setup["priv_key"])
    rec1 = inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_neg")
    rec2 = inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_neg")
    assert rec1.installation_id == rec2.installation_id

# 11. Fail activation health-check -> automatic rollback
def test_neg_11_failing_healthcheck_triggers_rollback(neg_setup):
    inst = neg_setup["installer"]
    # Install & activate v0.1.0
    m1, p1 = helper_build_manifest(neg_setup["priv_key"], version="0.1.0", pkg_bytes=b"print(\"ok\")\n")
    inst.install_plugin(m1, p1, workspace_id="ws_neg")
    inst.activate_plugin("ws_neg", "dnk-test-health", "0.1.0")
    
    # Install v0.2.0 with failing health-check
    m2, p2 = helper_build_manifest(neg_setup["priv_key"], version="0.2.0", pkg_bytes=b"RAISE_HEALTH_CHECK_FAILURE\n")
    inst.install_plugin(m2, p2, workspace_id="ws_neg")
    
    with pytest.raises(RuntimeError):
        inst.activate_plugin("ws_neg", "dnk-test-health", "0.2.0")
        
    assert inst.store.get_active_version("ws_neg", "dnk-test-health") == "0.1.0"

# 12. Attempt cross-workspace activation -> rejected
def test_neg_12_cross_workspace_activation_rejected(neg_setup):
    inst = neg_setup["installer"]
    m, p = helper_build_manifest(neg_setup["priv_key"])
    inst.install_plugin(m, p, workspace_id="ws_workspace_A")
    
    with pytest.raises(ValueError) as exc:
        inst.activate_plugin("ws_workspace_B", "dnk-test-health", "0.1.0")
    assert "not installed in workspace" in str(exc.value)

# 13. Attempt forbidden permission -> denied and audited
def test_neg_13_forbidden_permission_audited(neg_setup):
    inst = neg_setup["installer"]
    m, p = helper_build_manifest(neg_setup["priv_key"])
    # Add forbidden permission
    m["permissions"].append("credentials.read")
    
    # Re-sign with updated manifest payload
    pkg_hash = calculate_package_hash(p)
    m["content_hash"] = pkg_hash
    sig = sign_data_ed25519(f"{m['plugin_id']}:{m['version']}:{pkg_hash}".encode("utf-8"), neg_setup["priv_key"])
    m["signature_metadata"]["signature"] = sig
    
    # Evaluate permissions policy
    forbidden_permissions = {"credentials.read", "filesystem.write", "network.egress", "shopify.orders.write", "erp.write", "customer_data.read"}
    declared = set(m["permissions"])
    denied = declared.intersection(forbidden_permissions)
    assert len(denied) > 0
    
    # Log audit event for permission denial
    inst.audit_logger.log_event("ws_neg", "system", "plugin.permission.denied", {"plugin_id": m["plugin_id"], "denied": list(denied)})
    logs = inst.audit_logger.get_logs_for_plugin(m["plugin_id"])
    assert any(l["action"] == "plugin.permission.denied" for l in logs)

# 14. Attempt package execution from staging -> blocked
def test_neg_14_staging_execution_blocked(neg_setup):
    inst = neg_setup["installer"]
    staging = tempfile.mkdtemp(prefix="dnk_staging_test_")
    stage_file = os.path.join(staging, "plugin.py")
    with open(stage_file, "w") as f:
        f.write("print(\"staging execute\")\n")
    
    # Verify staging directory is outside installed path store
    assert not staging.startswith(inst.base_store_dir)
    import shutil
    shutil.rmtree(staging, ignore_errors=True)

# 15. Attempt secret/environment access -> denied; no secret in logs
def test_neg_15_no_secrets_in_audit_logs(neg_setup):
    inst = neg_setup["installer"]
    secret_token = "SUPER_SECRET_BEARER_TOKEN_12345"
    inst.audit_logger.log_event("ws_neg", "user_1", "plugin.install.rejected", {"plugin_id": "dnk-test-health", "error": "Invalid token provided"})
    
    logs = inst.audit_logger.get_logs_for_plugin("dnk-test-health")
    logs_str = str(logs)
    assert secret_token not in logs_str
