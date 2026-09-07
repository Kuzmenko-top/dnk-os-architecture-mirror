# --- DNK-MRH-HEADER ---
# mrh_id: "tests/plugins/test_operational_pilot.py"
# purpose: "Positive Lifecycle Operational Pilot Test Suite for DNK-PLUGIN-018"
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
from core.plugins.plugin_manifest import validate_manifest
from core.plugins.plugin_models import PluginLifecycleState, PluginTrustState
from core.plugins.plugin_security_gate import (
    TrustKeyRegistry,
    generate_ed25519_keypair,
    sign_data_ed25519,
    calculate_package_hash,
)

@pytest.fixture
def pilot_setup():
    temp_store = tempfile.mkdtemp(prefix="pilot_store_")
    registry = TrustKeyRegistry()
    priv_key, pub_key = generate_ed25519_keypair()
    
    pub_bytes = pub_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    key_id = "test_ephemeral_key_01"
    registry.register_key(key_id, pub_bytes, "DNK Test Publisher", "active")
    
    installer = PluginInstaller(base_store_dir=temp_store, key_registry=registry)
    
    return {
        "store_dir": temp_store,
        "registry": registry,
        "priv_key": priv_key,
        "pub_bytes": pub_bytes,
        "key_id": key_id,
        "installer": installer,
    }

def create_test_health_package(priv_key, key_id, version="0.1.0", failing_health=False):
    if failing_health:
        code_bytes = b"# RAISE_HEALTH_CHECK_FAILURE\ndef health_check(): raise RuntimeError(\"Health check failure\")\n"
    else:
        code_bytes = b"def health_check(): return {\"status\": \"healthy\", \"version\": \"" + version.encode() + b"\"}\n"
        
    pkg_hash = calculate_package_hash(code_bytes)
    plugin_id = "dnk-test-health"
    canonical_payload = f"{plugin_id}:{version}:{pkg_hash}".encode("utf-8")
    sig_b64 = sign_data_ed25519(canonical_payload, priv_key)
    
    raw_manifest = {
        "plugin_id": plugin_id,
        "name": "DNK Test Health Plugin",
        "version": version,
        "publisher": "DNK Test Publisher",
        "entrypoint": "plugin.py",
        "runtime_compatibility": ">=0.1.0",
        "permissions": ["health.read", "audit.write"],
        "dependencies": {"python": ">=3.12"},
        "content_hash": pkg_hash,
        "signature_metadata": {
            "key_id": key_id,
            "signature": sig_b64,
        }
    }
    return raw_manifest, code_bytes, pkg_hash

def test_full_positive_lifecycle_pilot(pilot_setup):
    inst = pilot_setup["installer"]
    key_id = pilot_setup["key_id"]
    priv_key = pilot_setup["priv_key"]
    workspace_id = "ws_pilot_01"
    actor_id = "mentor_tester"
    
    # 1. Acquire valid package & manifest for v0.1.0
    manifest_v1, pkg_v1, hash_v1 = create_test_health_package(priv_key, key_id, version="0.1.0")
    
    # 2. Validate manifest
    validated_manifest = validate_manifest(manifest_v1)
    assert validated_manifest.plugin_id == "dnk-test-health"
    assert validated_manifest.permissions == ["health.read", "audit.write"]
    
    # 3. Calculate canonical hash & verify
    calc_hash = calculate_package_hash(pkg_v1)
    assert calc_hash == hash_v1
    
    # 4 & 5. Sign / verify & resolve trusted key
    key_info = pilot_setup["registry"].get_key_info(key_id)
    assert key_info["status"] == "active"
    
    # 6 & 7. Stage and install atomically
    rec_v1 = inst.install_plugin(
        raw_manifest=manifest_v1,
        package_bytes=pkg_v1,
        workspace_id=workspace_id,
        actor_id=actor_id,
        production_mode=True,
    )
    assert rec_v1.install_state == PluginLifecycleState.INSTALLED.value
    assert rec_v1.trust_state == PluginTrustState.TRUSTED.value
    assert os.path.exists(rec_v1.installed_path)
    
    # 8 & 9. Activate & health check
    act_rec_v1 = inst.activate_plugin(
        workspace_id=workspace_id,
        plugin_id="dnk-test-health",
        version="0.1.0",
        actor_id=actor_id,
    )
    assert act_rec_v1.install_state == PluginLifecycleState.ACTIVE.value
    assert inst.store.get_active_version(workspace_id, "dnk-test-health") == "0.1.0"
    
    # 10. Verify audit events
    audit_logs = inst.audit_logger.get_logs_for_plugin("dnk-test-health")
    event_actions = [log["action"] for log in audit_logs]
    assert "plugin.install.started" in event_actions
    assert "plugin.install.completed" in event_actions
    assert "plugin.activation.completed" in event_actions
    
    # 11. Install v0.2.0, activate v0.2.0, then rollback to v0.1.0
    manifest_v2, pkg_v2, _ = create_test_health_package(priv_key, key_id, version="0.2.0")
    inst.install_plugin(manifest_v2, pkg_v2, workspace_id=workspace_id, actor_id=actor_id)
    inst.activate_plugin(workspace_id, "dnk-test-health", "0.2.0", actor_id=actor_id)
    assert inst.store.get_active_version(workspace_id, "dnk-test-health") == "0.2.0"
    
    rb_rec = inst.rollback_plugin(
        workspace_id=workspace_id,
        plugin_id="dnk-test-health",
        target_version="0.1.0",
        actor_id=actor_id,
    )
    assert rb_rec.install_state == PluginLifecycleState.ACTIVE.value
    assert inst.store.get_active_version(workspace_id, "dnk-test-health") == "0.1.0"
    
    # 12 & 13. Uninstall v0.2.0 & verify audit history remains available
    uninstalled = inst.uninstall_plugin(
        workspace_id=workspace_id,
        plugin_id="dnk-test-health",
        version="0.2.0",
        actor_id=actor_id,
    )
    assert uninstalled is True
    
    final_audit = inst.audit_logger.get_logs_for_plugin("dnk-test-health")
    assert len(final_audit) >= 6
    uninst_logs = [l for l in final_audit if l["action"] == "plugin.uninstall.completed"]
    assert len(uninst_logs) == 1
