# --- DNK-MRH-HEADER ---
# mrh_id: "tests/plugins/test_install_lifecycle.py"
# purpose: "Comprehensive unit tests for Plugin Installation Lifecycle, Staging, Security Gate, and Atomicity"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

import os
import tempfile
import base64
import pytest

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
def test_setup():
    temp_store = tempfile.mkdtemp(prefix="test_plugin_store_")
    registry = TrustKeyRegistry()
    priv_key, pub_key = generate_ed25519_keypair()
    
    pub_bytes = pub_key.public_bytes(
        encoding=pytest.importorskip("cryptography.hazmat.primitives.serialization").Encoding.Raw,
        format=pytest.importorskip("cryptography.hazmat.primitives.serialization").PublicFormat.Raw
    )
    registry.register_key("key_trusted_01", pub_bytes, "DNK-e.com", "active")
    
    installer = PluginInstaller(base_store_dir=temp_store, key_registry=registry)
    
    return {
        "store_dir": temp_store,
        "registry": registry,
        "priv_key": priv_key,
        "pub_bytes": pub_bytes,
        "installer": installer,
    }

def create_valid_package_and_manifest(priv_key, key_id="key_trusted_01", plugin_id="valid_plugin"):
    package_bytes = b"print('Hello from DNK plugin')\n"
    pkg_hash = calculate_package_hash(package_bytes)
    
    canonical_payload = f"{plugin_id}:1.0.0:{pkg_hash}".encode('utf-8')
    sig_b64 = sign_data_ed25519(canonical_payload, priv_key)
    
    manifest = {
        "plugin_id": plugin_id,
        "name": "Valid Test Plugin",
        "version": "1.0.0",
        "publisher": "DNK-e.com",
        "entrypoint": "main.py",
        "runtime_compatibility": ">=0.1.0",
        "permissions": ["read_memory"],
        "dependencies": {"python": ">=3.12"},
        "content_hash": pkg_hash,
        "signature_metadata": {
            "key_id": key_id,
            "signature": sig_b64,
        }
    }
    return manifest, package_bytes

# 1. Valid signed plugin installs successfully
def test_1_valid_signed_plugin_installs(test_setup):
    inst = test_setup["installer"]
    manifest, pkg_bytes = create_valid_package_and_manifest(test_setup["priv_key"])
    
    rec = inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_01")
    assert rec.install_state == PluginLifecycleState.INSTALLED.value
    assert rec.trust_state == PluginTrustState.TRUSTED.value
    assert os.path.exists(rec.installed_path)

# 2. Unsigned plugin is blocked in production
def test_2_unsigned_plugin_blocked_in_production(test_setup):
    inst = test_setup["installer"]
    manifest, pkg_bytes = create_valid_package_and_manifest(test_setup["priv_key"])
    manifest["signature_metadata"] = {}  # Remove signature
    
    with pytest.raises(ProductionUnsignedPluginError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_01", production_mode=True)

# 3. Tampered package is rejected
def test_3_tampered_package_rejected(test_setup):
    inst = test_setup["installer"]
    manifest, pkg_bytes = create_valid_package_and_manifest(test_setup["priv_key"])
    tampered_bytes = pkg_bytes + b"\n# TAMPERED ATTACK PAYLOAD"
    
    with pytest.raises(HashMismatchError):
        inst.install_plugin(manifest, tampered_bytes, workspace_id="ws_01", production_mode=True)

# 4. Unknown signing key is blocked
def test_4_unknown_key_blocked(test_setup):
    inst = test_setup["installer"]
    manifest, pkg_bytes = create_valid_package_and_manifest(test_setup["priv_key"], key_id="unknown_key_99")
    
    with pytest.raises(UntrustedSigningKeyError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_01", production_mode=True)

# 5. Revoked key leads to quarantine
def test_5_revoked_key_quarantine(test_setup):
    inst = test_setup["installer"]
    test_setup["registry"].revoke_key("key_trusted_01")
    manifest, pkg_bytes = create_valid_package_and_manifest(test_setup["priv_key"], key_id="key_trusted_01")
    
    with pytest.raises(PluginQuarantinedError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_01", production_mode=True)

# 6. Invalid manifest is rejected before installation
def test_6_invalid_manifest_rejected(test_setup):
    inst = test_setup["installer"]
    manifest, pkg_bytes = create_valid_package_and_manifest(test_setup["priv_key"])
    del manifest["publisher"]
    
    with pytest.raises(InvalidPluginManifestError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_01", production_mode=True)

# 7. Path traversal is rejected
def test_7_path_traversal_rejected(test_setup):
    inst = test_setup["installer"]
    manifest, pkg_bytes = create_valid_package_and_manifest(test_setup["priv_key"])
    manifest["entrypoint"] = "../../etc/shadow"
    
    with pytest.raises(InvalidPluginManifestError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_01", production_mode=True)

# 8. Symlink package is rejected
def test_8_symlink_package_rejected(test_setup):
    inst = test_setup["installer"]
    manifest, pkg_bytes = create_valid_package_and_manifest(test_setup["priv_key"])
    
    staging_temp = tempfile.mkdtemp()
    symlink_path = os.path.join(staging_temp, "escape_link")
    os.symlink("/etc/passwd", symlink_path)
    
    try:
        with pytest.raises(InvalidPluginManifestError):
            inst._verify_staging_safety(staging_temp)
    finally:
        import shutil
        shutil.rmtree(staging_temp, ignore_errors=True)

# 9. Duplicate version is idempotent
def test_9_duplicate_version_idempotent(test_setup):
    inst = test_setup["installer"]
    manifest, pkg_bytes = create_valid_package_and_manifest(test_setup["priv_key"])
    
    rec1 = inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_01")
    rec2 = inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_01")
    assert rec1.installation_id == rec2.installation_id

# 10. Atomic cleanup on failure
def test_10_atomic_cleanup_on_failure(test_setup):
    inst = test_setup["installer"]
    manifest, pkg_bytes = create_valid_package_and_manifest(test_setup["priv_key"])
    manifest["entrypoint"] = "invalid_path/../../../malicious"
    
    with pytest.raises(InvalidPluginManifestError):
        inst.install_plugin(manifest, pkg_bytes, workspace_id="ws_01")
    
    # Confirm store remains clean
    versions = inst.store.list_versions("ws_01", "valid_plugin")
    assert len(versions) == 0
