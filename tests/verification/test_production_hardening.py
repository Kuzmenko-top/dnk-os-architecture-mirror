# --- DNK-MRH-HEADER ---
# mrh_id: "test_production_hardening"
# purpose: "Security and compliance verification suite verifying P0 environment guards, canonical arguments hashing, and one-time consumption."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

import os
os.environ["ENV"] = "test"
os.environ["APP_ENV"] = "test"
os.environ["NODE_ENV"] = "test"
import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2] # DNK OS
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
services_path = ROOT / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

import pytest
import hashlib
import json
from uuid import uuid4
from fastapi.testclient import TestClient
from services.dnk_canvas_api.main import app

client = TestClient(app)

def test_endpoint_blocked_when_NODE_ENV_production():
    """1. test_endpoint_blocked_when_NODE_ENV_production — guard blocks endpoint in production NODE_ENV."""
    original_node_env = os.getenv("NODE_ENV")
    try:
        os.environ["NODE_ENV"] = "production"
        res = client.post(f"/api/v1/test/approve/{uuid4()}")
        assert res.status_code == 404
    finally:
        if original_node_env is not None:
            os.environ["NODE_ENV"] = original_node_env
        else:
            os.environ.pop("NODE_ENV", None)


def test_endpoint_blocked_when_APP_ENV_production():
    """2. test_endpoint_blocked_when_APP_ENV_production — guard blocks endpoint in production APP_ENV."""
    original_app_env = os.getenv("APP_ENV")
    try:
        os.environ["APP_ENV"] = "production"
        res = client.post(f"/api/v1/test/approve/{uuid4()}")
        assert res.status_code == 404
    finally:
        if original_app_env is not None:
            os.environ["APP_ENV"] = original_app_env
        else:
            os.environ.pop("APP_ENV", None)


def test_force_commit_hash_binds_override_reason():
    """3. test_force_commit_hash_binds_override_reason — verifies override_reason is strictly bound to payload hash."""
    # Setup test-only environment variables
    os.environ["ENV"] = "test"
    os.environ["APP_ENV"] = "test"
    os.environ["NODE_ENV"] = "test"
    try:
        workspace_id = str(uuid4())
        headers = {"X-Workspace-Id": workspace_id}
        
        canvas_id = client.post("/api/v1/canvases", json={"title": "Reason Canvas"}, headers=headers).json()["id"]
        scene = {"type": "excalidraw", "elements": [{"id": "r-1", "type": "rectangle"}]}
        
        scene_str = json.dumps(scene, sort_keys=True, separators=(',', ':'))
        checksum = hashlib.sha256(scene_str.encode('utf-8')).hexdigest()
        
        payload = {
            "override_reason": "Original reason string",
            "parent_revision_number": 0,
            "scene_json": scene,
            "scene_checksum": checksum
        }
        
        # Register approval
        res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=payload, headers=headers)
        assert res.status_code == 202
        approval_id = res.json()["approval_id"]
        
        # Approve via test endpoint
        client.post(f"/api/v1/test/approve/{approval_id}")
        
        # Tamper override_reason and execute -> must fail with 403 due to canonical arguments_hash binding mismatch
        tampered_payload = {**payload, "override_reason": "Tampered reason string", "approval_id": approval_id}
        final_res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=tampered_payload, headers=headers)
        assert final_res.status_code == 403
    finally:
        os.environ.pop("ENV", None)
        os.environ.pop("APP_ENV", None)
        os.environ.pop("NODE_ENV", None)


def test_force_commit_hash_binds_scene_json():
    """4. test_force_commit_hash_binds_scene_json — verifies full nested scene_json is bound to payload hash."""
    os.environ["ENV"] = "test"
    os.environ["APP_ENV"] = "test"
    os.environ["NODE_ENV"] = "test"
    try:
        workspace_id = str(uuid4())
        headers = {"X-Workspace-Id": workspace_id}
        
        canvas_id = client.post("/api/v1/canvases", json={"title": "Scene Canvas"}, headers=headers).json()["id"]
        
        scene_orig = {"type": "excalidraw", "elements": [{"id": "orig", "type": "rectangle"}]}
        scene_tampered = {"type": "excalidraw", "elements": [{"id": "tampered", "type": "circle"}]}
        
        checksum_orig = hashlib.sha256(json.dumps(scene_orig, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
        checksum_tampered = hashlib.sha256(json.dumps(scene_tampered, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
        
        payload = {
            "override_reason": "Secure hash binding",
            "parent_revision_number": 0,
            "scene_json": scene_orig,
            "scene_checksum": checksum_orig
        }
        
        # Register approval
        res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=payload, headers=headers)
        approval_id = res.json()["approval_id"]
        
        # Approve
        client.post(f"/api/v1/test/approve/{approval_id}")
        
        # Attempt force-commit with tampered scene_json -> must fail with 403 due to canonical arguments_hash mismatch
        tampered_payload = {
            "override_reason": "Secure hash binding",
            "parent_revision_number": 0,
            "scene_json": scene_tampered,
            "scene_checksum": checksum_tampered,
            "approval_id": approval_id
        }
        final_res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=tampered_payload, headers=headers)
        assert final_res.status_code == 403
    finally:
        os.environ.pop("ENV", None)
        os.environ.pop("APP_ENV", None)
        os.environ.pop("NODE_ENV", None)


def test_approval_id_cannot_be_reused():
    """5. test_approval_id_cannot_be_reused — verifies approved -> consumed state transition and blocks replay."""
    os.environ["ENV"] = "test"
    os.environ["APP_ENV"] = "test"
    os.environ["NODE_ENV"] = "test"
    try:
        workspace_id = str(uuid4())
        headers = {"X-Workspace-Id": workspace_id}
        
        canvas_id = client.post("/api/v1/canvases", json={"title": "Reuse Canvas"}, headers=headers).json()["id"]
        scene = {"type": "excalidraw", "elements": [{"id": "reuse", "type": "circle"}]}
        checksum = hashlib.sha256(json.dumps(scene, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
        
        payload = {
            "override_reason": "One-time usage test",
            "parent_revision_number": 0,
            "scene_json": scene,
            "scene_checksum": checksum
        }
        
        # Register approval
        res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=payload, headers=headers)
        approval_id = res.json()["approval_id"]
        
        # Approve
        client.post(f"/api/v1/test/approve/{approval_id}")
        
        # Execute first force commit -> must succeed with 200
        commit_payload = {**payload, "approval_id": approval_id}
        res1 = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=commit_payload, headers=headers)
        assert res1.status_code == 200
        
        # Attempt second force commit using the SAME approval_id -> must fail with 403 (APPROVAL_ALREADY_CONSUMED)
        res2 = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=commit_payload, headers=headers)
        assert res2.status_code == 403
        assert "CONSUMED" in res2.json()["detail"]
    finally:
        os.environ.pop("ENV", None)
        os.environ.pop("APP_ENV", None)
        os.environ.pop("NODE_ENV", None)


def test_no_internal_MIT_headers():
    """6. test_no_internal_MIT_headers — verifies that no custom internal file has an MIT header."""
    import pathlib
    target_paths = [
        pathlib.Path(ROOT) / "tests/verification",
        pathlib.Path(ROOT) / "visual_shell/open_design/apps/web"
    ]
    
    mit_count = 0
    for path in target_paths:
        if path.exists():
            for filepath in path.rglob("*"):
                if filepath.is_file() and filepath.suffix in [".py", ".ts", ".tsx", ".js", ".jsx"]:
                    p_str = str(filepath).lower()
                    if any(x in p_str for x in ["node_modules", "dist", ".next", "vendor", "third_party", "third-party", "excalidraw", "license"]):
                        continue
                    try:
                        content_str = filepath.read_text(encoding="utf-8")
                        is_internal = "DNK-MRH-HEADER" in content_str or "DNK-INTERNAL" in content_str or "DNK-e.com Maksym" in content_str
                        if is_internal and 'license: ' + '"MIT"' in content_str:
                            print(f"Violation: File {filepath} still has MIT license")
                            mit_count += 1
                    except Exception:
                        pass
    assert mit_count == 0, f"Found {mit_count} internal files incorrectly carrying MIT license headers!"



def test_test_router_isolation_production():
    """7. test_test_router_isolation_production — verifies physical router isolation under production environment configurations."""
    import importlib
    import sys
    import os
    
    # Save original env
    orig_app_env = os.getenv("APP_ENV")
    orig_env = os.getenv("ENV")
    orig_node_env = os.getenv("NODE_ENV")
    
    try:
        # Set up a production-like environment configuration combination where the test router should NOT be registered
        os.environ["APP_ENV"] = "test"
        os.environ["ENV"] = "production"
        os.environ["NODE_ENV"] = "production"
        
        # Reload main.py to trigger the conditional mounting block
        if "services.dnk_canvas_api.main" in sys.modules:
            importlib.reload(sys.modules["services.dnk_canvas_api.main"])
            
        from services.dnk_canvas_api.main import app as reloaded_app
        
        # Check that NO route matching '/api/v1/test/approve/' is in reloaded_app.routes
        paths = [getattr(route, "path", "") for route in reloaded_app.routes]
        assert not any("/api/v1/test/approve" in p for p in paths), "Test router was incorrectly registered in a production environment!"
        
    finally:
        # Restore original env
        for k, v in [("APP_ENV", orig_app_env), ("ENV", orig_env), ("NODE_ENV", orig_node_env)]:
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)
                
        # Reload back to test environment configuration for subsequent tests
        os.environ["APP_ENV"] = "test"
        os.environ["ENV"] = "test"
        os.environ["NODE_ENV"] = "test"
        if "services.dnk_canvas_api.main" in sys.modules:
            importlib.reload(sys.modules["services.dnk_canvas_api.main"])
