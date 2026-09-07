# --- DNK-MRH-HEADER ---
# mrh_id: "tests/plugins/test_plugin_activation.py"
# purpose: "Unit tests for Plugin Activation, Health Checks, and Workspace Isolation"
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
from core.plugins.plugin_models import PluginLifecycleState, PluginTrustState
from core.plugins.plugin_security_gate import (
    TrustKeyRegistry,
    generate_ed25519_keypair,
    sign_data_ed25519,
    calculate_package_hash,
    DependencyNotSatisfiedError,
)

@pytest.fixture
def activation_setup():
    temp_store = tempfile.mkdtemp(prefix="test_plugin_act_")
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

def helper_install_version(installer, priv_key, plugin_id="act_plugin", version="1.0.0", workspace_id="ws_A", code=b"print('ok')\n"):
    pkg_hash = calculate_package_hash(code)
    sig = sign_data_ed25519(f"{plugin_id}:{version}:{pkg_hash}".encode('utf-8'), priv_key)
    manifest = {
        "plugin_id": plugin_id,
        "name": "Activation Test Plugin",
        "version": version,
        "publisher": "DNK-e.com",
        "entrypoint": "main.py",
        "runtime_compatibility": ">=0.1.0",
        "permissions": [],
        "dependencies": {"python": ">=3.12"},
        "content_hash": pkg_hash,
        "signature_metadata": {"key_id": "key_01", "signature": sig},
    }
    return installer.install_plugin(manifest, code, workspace_id=workspace_id)

def test_successful_activation(activation_setup):
    inst = activation_setup["installer"]
    rec = helper_install_version(inst, activation_setup["priv_key"], version="1.0.0")
    
    act_rec = inst.activate_plugin("ws_A", "act_plugin", "1.0.0")
    assert act_rec.install_state == PluginLifecycleState.ACTIVE.value
    assert inst.store.get_active_version("ws_A", "act_plugin") == "1.0.0"

def test_activation_failure_preserves_previous_active(activation_setup):
    inst = activation_setup["installer"]
    # 1. Install & Activate v1.0.0
    rec1 = helper_install_version(inst, activation_setup["priv_key"], version="1.0.0")
    inst.activate_plugin("ws_A", "act_plugin", "1.0.0")
    assert inst.store.get_active_version("ws_A", "act_plugin") == "1.0.0"

    # 2. Install v2.0.0 with health check failure code
    bad_code = b"RAISE_HEALTH_CHECK_FAILURE\n"
    rec2 = helper_install_version(inst, activation_setup["priv_key"], version="2.0.0", code=bad_code)

    # 3. Attempt to activate v2.0.0
    with pytest.raises(RuntimeError):
        inst.activate_plugin("ws_A", "act_plugin", "2.0.0")

    # 4. Verify active version falls back/remains v1.0.0
    assert inst.store.get_active_version("ws_A", "act_plugin") == "1.0.0"

def test_workspace_isolation_prevents_cross_workspace(activation_setup):
    inst = activation_setup["installer"]
    # Install in ws_A
    helper_install_version(inst, activation_setup["priv_key"], workspace_id="ws_A")
    inst.activate_plugin("ws_A", "act_plugin", "1.0.0")

    # Attempt to activate in ws_B where it is not installed
    with pytest.raises(ValueError) as exc:
        inst.activate_plugin("ws_B", "act_plugin", "1.0.0")
    assert "not installed in workspace" in str(exc.value)

def test_missing_dependency_fails_activation(activation_setup):
    inst = activation_setup["installer"]
    code = b"print('ok')\n"
    pkg_hash = calculate_package_hash(code)
    sig = sign_data_ed25519(f"dep_plugin:1.0.0:{pkg_hash}".encode('utf-8'), activation_setup["priv_key"])
    manifest = {
        "plugin_id": "dep_plugin",
        "name": "Dependency Plugin",
        "version": "1.0.0",
        "publisher": "DNK-e.com",
        "entrypoint": "main.py",
        "runtime_compatibility": ">=0.1.0",
        "permissions": [],
        "dependencies": {"non_existent_package_xyz_99": ">=1.0.0"},
        "content_hash": pkg_hash,
        "signature_metadata": {"key_id": "key_01", "signature": sig},
    }
    inst.install_plugin(manifest, code, workspace_id="ws_A")
    
    with pytest.raises(DependencyNotSatisfiedError):
        inst.activate_plugin("ws_A", "dep_plugin", "1.0.0")
