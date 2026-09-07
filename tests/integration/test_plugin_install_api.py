# --- DNK-MRH-HEADER ---
# mrh_id: "tests/integration/test_plugin_install_api.py"
# purpose: "Integration tests for FastAPI Plugin Lifecycle REST API endpoints and standardized HTTP errors"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

import base64
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.plugins.plugin_api import router as plugin_router, global_installer
from core.plugins.plugin_security_gate import (
    generate_ed25519_keypair,
    sign_data_ed25519,
    calculate_package_hash,
)

app = FastAPI()
app.include_router(plugin_router)
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_api_key_registry():
    priv_key, pub_key = generate_ed25519_keypair()
    pub_bytes = pub_key.public_bytes(
        encoding=pytest.importorskip("cryptography.hazmat.primitives.serialization").Encoding.Raw,
        format=pytest.importorskip("cryptography.hazmat.primitives.serialization").PublicFormat.Raw
    )
    global_installer.key_registry.register_key("api_key_01", pub_bytes, "DNK-e.com", "active")
    return {"priv_key": priv_key}

def make_signed_payload(priv_key, plugin_id="api_plugin", version="1.0.0"):
    pkg_bytes = b"print('hello api')\n"
    pkg_b64 = base64.b64encode(pkg_bytes).decode('utf-8')
    pkg_hash = calculate_package_hash(pkg_bytes)
    sig = sign_data_ed25519(f"{plugin_id}:{version}:{pkg_hash}".encode('utf-8'), priv_key)
    
    manifest = {
        "plugin_id": plugin_id,
        "name": "API Plugin",
        "version": version,
        "publisher": "DNK-e.com",
        "entrypoint": "main.py",
        "runtime_compatibility": ">=0.1.0",
        "permissions": [],
        "dependencies": {"python": ">=3.12"},
        "content_hash": pkg_hash,
        "signature_metadata": {"key_id": "api_key_01", "signature": sig},
    }
    return {"manifest": manifest, "package_b64": pkg_b64, "production_mode": True}

def test_api_install_activate_provenance_audit_lifecycle(setup_api_key_registry):
    payload = make_signed_payload(setup_api_key_registry["priv_key"])
    
    # 1. POST /plugins/install
    resp = client.post("/plugins/install", json=payload, headers={"X-Workspace-ID": "ws_api_1"})
    assert resp.status_code == 201
    data = resp.json()
    inst_id = data["installation_id"]
    assert data["install_state"] == "installed"

    # 2. GET /plugins/installations/{installation_id}
    resp_get = client.get(f"/plugins/installations/{inst_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["installation_id"] == inst_id

    # 3. POST /plugins/{plugin_id}/activate
    resp_act = client.post("/plugins/api_plugin/activate", json={"version": "1.0.0"}, headers={"X-Workspace-ID": "ws_api_1"})
    assert resp_act.status_code == 200
    assert resp_act.json()["install_state"] == "active"

    # 4. GET /plugins/{plugin_id}/provenance
    resp_prov = client.get("/plugins/api_plugin/provenance", headers={"X-Workspace-ID": "ws_api_1"})
    assert resp_prov.status_code == 200
    assert resp_prov.json()["trust_state"] == "trusted"

    # 5. GET /plugins/{plugin_id}/audit
    resp_aud = client.get("/plugins/api_plugin/audit")
    assert resp_aud.status_code == 200
    assert len(resp_aud.json()) >= 2

    # 6. POST /plugins/{plugin_id}/uninstall
    resp_un = client.post("/plugins/api_plugin/uninstall", json={"version": "1.0.0"}, headers={"X-Workspace-ID": "ws_api_1"})
    assert resp_un.status_code == 200
    assert resp_un.json()["status"] == "uninstalled"

def test_api_unsigned_plugin_returns_403(setup_api_key_registry):
    payload = make_signed_payload(setup_api_key_registry["priv_key"])
    payload["manifest"]["signature_metadata"] = {}  # Unsigned
    
    resp = client.post("/plugins/install", json=payload, headers={"X-Workspace-ID": "ws_api_2"})
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"] == "PRODUCTION_UNSIGNED_PLUGIN"

def test_api_invalid_manifest_returns_400(setup_api_key_registry):
    payload = make_signed_payload(setup_api_key_registry["priv_key"])
    del payload["manifest"]["version"]
    
    resp = client.post("/plugins/install", json=payload, headers={"X-Workspace-ID": "ws_api_3"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "INVALID_PLUGIN_MANIFEST"
