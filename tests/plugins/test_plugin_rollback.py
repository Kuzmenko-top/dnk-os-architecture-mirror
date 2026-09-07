# --- DNK-MRH-HEADER ---
# mrh_id: "tests/plugins/test_plugin_rollback.py"
# purpose: "Unit tests for Plugin Rollback, Atomic Restoration, and Audit Trail"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

import pytest
import tempfile
from core.plugins.plugin_installer import PluginInstaller
from core.plugins.plugin_models import PluginLifecycleState
from core.plugins.plugin_security_gate import (
    TrustKeyRegistry,
    generate_ed25519_keypair,
    sign_data_ed25519,
    calculate_package_hash,
    InstallationRollbackFailedError,
)

@pytest.fixture
def rollback_setup():
    temp_store = tempfile.mkdtemp(prefix="test_plugin_rb_")
    registry = TrustKeyRegistry()
    priv_key, pub_key = generate_ed25519_keypair()
    
    pub_bytes = pub_key.public_bytes(
        encoding=pytest.importorskip("cryptography.hazmat.primitives.serialization").Encoding.Raw,
        format=pytest.importorskip("cryptography.hazmat.primitives.serialization").PublicFormat.Raw
    )
    registry.register_key("key_01", pub_bytes, "DNK-e.com", "active")
    installer = PluginInstaller(base_store_dir=temp_store, key_registry=registry)
    
    return {
        "installer": installer,
        "priv_key": priv_key,
    }

def install_and_activate(installer, priv_key, version, plugin_id="rb_plugin", workspace_id="ws_01"):
    code = f"# version {version}\nprint('{version}')\n".encode('utf-8')
    pkg_hash = calculate_package_hash(code)
    sig = sign_data_ed25519(f"{plugin_id}:{version}:{pkg_hash}".encode('utf-8'), priv_key)
    manifest = {
        "plugin_id": plugin_id,
        "name": "Rollback Test Plugin",
        "version": version,
        "publisher": "DNK-e.com",
        "entrypoint": "main.py",
        "runtime_compatibility": ">=0.1.0",
        "permissions": [],
        "dependencies": {"python": ">=3.12"},
        "content_hash": pkg_hash,
        "signature_metadata": {"key_id": "key_01", "signature": sig},
    }
    installer.install_plugin(manifest, code, workspace_id=workspace_id)
    return installer.activate_plugin(workspace_id, plugin_id, version)

def test_rollback_restores_previous_trusted_version(rollback_setup):
    inst = rollback_setup["installer"]
    priv_key = rollback_setup["priv_key"]

    # 1. Install & activate v1.0.0
    install_and_activate(inst, priv_key, "1.0.0")
    assert inst.store.get_active_version("ws_01", "rb_plugin") == "1.0.0"

    # 2. Install & activate v2.0.0
    install_and_activate(inst, priv_key, "2.0.0")
    assert inst.store.get_active_version("ws_01", "rb_plugin") == "2.0.0"

    # 3. Manual rollback
    rb_rec = inst.rollback_plugin("ws_01", "rb_plugin", target_version="1.0.0")
    assert rb_rec.version == "1.0.0"
    assert inst.store.get_active_version("ws_01", "rb_plugin") == "1.0.0"

def test_rollback_fails_when_no_trusted_version(rollback_setup):
    inst = rollback_setup["installer"]
    with pytest.raises(InstallationRollbackFailedError):
        inst.rollback_plugin("ws_01", "non_existent_plugin")

def test_uninstall_preserves_audit_history(rollback_setup):
    inst = rollback_setup["installer"]
    priv_key = rollback_setup["priv_key"]

    install_and_activate(inst, priv_key, "1.0.0")
    inst.uninstall_plugin("ws_01", "rb_plugin", "1.0.0")

    # Confirm active version removed
    assert inst.store.get_active_version("ws_01", "rb_plugin") is None

    # Confirm audit logs preserved
    logs = inst.audit_logger.get_logs_for_plugin("rb_plugin")
    assert len(logs) >= 3
    action_types = [l["action"] for l in logs]
    assert "plugin.uninstall.completed" in action_types
