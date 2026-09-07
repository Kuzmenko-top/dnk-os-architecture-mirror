# --- DNK-MRH-HEADER ---
# mrh_id: "test_canvas_e2e_concurrency"
# purpose: "E2E verification tests for FastAPI Save, real SHA-256 validation, secure workspace authorization, Gate-enforced force-commit, and concurrent race-conditions with PostgreSQL/SQLite."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "2.1.0"
# updated_at: "2026-08-11"
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

import os
import pytest
import json
import hashlib
from uuid import uuid4
from fastapi.testclient import TestClient
import httpx
from services.dnk_canvas_api.main import app, Base, engine, SessionLocal, CanvasDocument, CanvasRevision

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db_fixture():
    # Setup test-only environment variables for test approval endpoint to work
    os.environ["ENV"] = "test"
    os.environ["APP_ENV"] = "test"
    os.environ["NODE_ENV"] = "test"
    yield
    # Clean up environment variables after the test module runs
    os.environ.pop("ENV", None)
    os.environ.pop("APP_ENV", None)
    os.environ.pop("NODE_ENV", None)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Rely entirely on pristine Alembic migrations for DB setup (no create_all in tests)
    yield

def compute_sha256(scene_json: dict) -> str:
    # Match server-side exact formatting (zero spacing separators)
    scene_str = json.dumps(scene_json, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(scene_str.encode('utf-8')).hexdigest()

def test_excalidraw_change_save_revision_reload_e2e():
    """9. E2E test: Excalidraw change -> FastAPI save -> PostgreSQL/SQLite revision -> reload."""
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id}
    
    # Create canvas document
    create_payload = {
        "title": "E2E Test Canvas",
        "description": "Validating Excalidraw saving flow",
        "workspace_id": workspace_id
    }
    create_res = client.post("/api/v1/canvases", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    canvas_data = create_res.json()
    canvas_id = canvas_data["id"]
    assert canvas_data["version"] == 0
    
    # 1. Simulate Excalidraw changes
    scene_json = {
        "type": "excalidraw",
        "elements": [
            {
                "id": "elem-1",
                "type": "rectangle",
                "x": 100,
                "y": 150,
                "width": 100,
                "height": 50
            }
        ],
        "app_state": {},
        "files": {}
    }
    
    # 2a. Attempt save with invalid checksum -> must fail with 422!
    invalid_payload = {
        "expected_revision": 0,
        "scene_json": scene_json,
        "scene_checksum": "corrupted-checksum-string",
        "change_summary": "Bad checksum test"
    }
    invalid_res = client.put(f"/api/v1/canvases/{canvas_id}/scene", json=invalid_payload, headers=headers)
    assert invalid_res.status_code == 422
    
    # 2b. Save with correct SHA-256 -> must succeed with 200!
    checksum = compute_sha256(scene_json)
    valid_payload = {
        "expected_revision": 0,
        "scene_json": scene_json,
        "scene_checksum": checksum,
        "change_summary": "Added first rectangle element"
    }
    
    save_res = client.put(f"/api/v1/canvases/{canvas_id}/scene", json=valid_payload, headers=headers)
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["status"] == "success"
    assert save_data["new_revision_number"] == 1
    
    # 3. Reload from server to verify revision and element match
    get_res = client.get(f"/api/v1/canvases/{canvas_id}", headers=headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["version"] == 1
    assert get_data["current_revision_number"] == 1
    assert get_data["scene_json"]["elements"][0]["id"] == "elem-1"


@pytest.mark.anyio
async def test_true_concurrent_save_race_condition_e2e():
    """10. E2E concurrent save test with two clients and a 409 conflict under true asyncio gather."""
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id}
    
    # Use AsyncClient to support concurrent asynchronous HTTP calls
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # Create a canvas
        create_res = await ac.post("/api/v1/canvases", json={"title": "Concurrent Canvas"}, headers=headers)
        assert create_res.status_code == 201
        canvas_id = create_res.json()["id"]
        
        scene_a = {"type": "excalidraw", "elements": [{"id": "a1", "type": "text", "text": "Client A update"}]}
        scene_b = {"type": "excalidraw", "elements": [{"id": "b1", "type": "text", "text": "Client B update"}]}
        
        checksum_a = compute_sha256(scene_a)
        checksum_b = compute_sha256(scene_b)
        
        save_a_payload = {
            "expected_revision": 0,
            "scene_json": scene_a,
            "scene_checksum": checksum_a,
            "change_summary": "Client A change"
        }
        save_b_payload = {
            "expected_revision": 0,
            "scene_json": scene_b,
            "scene_checksum": checksum_b,
            "change_summary": "Client B change"
        }
        
        # Fire both PUT requests at the exact same time
        import asyncio
        res_a, res_b = await asyncio.gather(
            ac.put(f"/api/v1/canvases/{canvas_id}/scene", json=save_a_payload, headers=headers),
            ac.put(f"/api/v1/canvases/{canvas_id}/scene", json=save_b_payload, headers=headers),
            return_exceptions=True
        )
        
        # Exactly one must succeed with 200, and exactly one must fail with 409!
        statuses = [res_a.status_code, res_b.status_code]
        assert 200 in statuses
        assert 409 in statuses
        
        # Ensure database has exactly 1 committed revision
        get_res = await ac.get(f"/api/v1/canvases/{canvas_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["version"] == 1


def test_workspace_isolation_authorization_boundary():
    """Verify that a canvas is strictly protected and isolated by its workspace context."""
    workspace_a = str(uuid4())
    workspace_b = str(uuid4())
    
    # Create canvas in workspace A
    create_res = client.post(
        "/api/v1/canvases", 
        json={"title": "Isolated Canvas"}, 
        headers={"X-Workspace-Id": workspace_a}
    )
    assert create_res.status_code == 201
    canvas_id = create_res.json()["id"]
    
    # Attempt to fetch canvas using Workspace B header -> must fail with 403 Forbidden!
    forbidden_get = client.get(
        f"/api/v1/canvases/{canvas_id}", 
        headers={"X-Workspace-Id": workspace_b}
    )
    assert forbidden_get.status_code == 403
    
    # Attempt to force-commit canvas using Workspace B header -> must fail with 403 Forbidden!
    forbidden_commit = client.post(
        f"/api/v1/canvases/{canvas_id}/force-commit",
        json={
            "override_reason": "Malicious hijacking attempt",
            "parent_revision_number": 0,
            "scene_json": {"type": "excalidraw", "elements": []},
            "scene_checksum": "dummy"
        },
        headers={"X-Workspace-Id": workspace_b}
    )
    assert forbidden_commit.status_code == 403


def test_gate_enforced_force_commit_lifecycle():
    """Verify the secure Supervisor Gate force-commit flow (202 pending_approval -> approved -> 200 force_committed)."""
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id}
    
    # Create canvas document
    create_payload = {"title": "Gate Canvas", "workspace_id": workspace_id}
    canvas_id = client.post("/api/v1/canvases", json=create_payload, headers=headers).json()["id"]
    
    scene = {"type": "excalidraw", "elements": [{"id": "force-1", "type": "rectangle"}]}
    checksum = compute_sha256(scene)
    
    payload = {
        "override_reason": "Relational conflict overwrite",
        "parent_revision_number": 0,
        "scene_json": scene,
        "scene_checksum": checksum
    }
    
    # Step 1: Request force-commit without approval_id -> must return 202 Accepted and status pending_approval!
    first_res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=payload, headers=headers)
    assert first_res.status_code == 202
    first_data = first_res.json()
    assert first_data["status"] == "pending_approval"
    approval_id = first_data["approval_id"]
    
    # Step 2: Attempt to complete force-commit with pending approval_id -> must fail with 403 Forbidden!
    bad_commit_payload = {**payload, "approval_id": approval_id}
    bad_commit_res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=bad_commit_payload, headers=headers)
    assert bad_commit_res.status_code == 403
    
    # Step 3: Simulate Supervisor Gate approval via simulation endpoint
    approve_res = client.post(f"/api/v1/test/approve/{approval_id}")
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"
    
    # Step 4: Execute force-commit with approved approval_id -> must succeed with 200!
    final_res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=bad_commit_payload, headers=headers)
    assert final_res.status_code == 200
    assert final_res.json()["status"] == "success"
    assert final_res.json()["new_revision_number"] == 1


def test_endpoint_blocked_when_NODE_ENV_production():
    """P0 Security: Verify test endpoint is blocked when NODE_ENV is production."""
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
    """P0 Security: Verify test endpoint is blocked when APP_ENV is production."""
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
    """P0 Security: Verify that changing the override_reason breaks the arguments_hash and causes 403."""
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id}
    
    canvas_id = client.post("/api/v1/canvases", json={"title": "Reason Canvas"}, headers=headers).json()["id"]
    scene = {"type": "excalidraw", "elements": [{"id": "r-1", "type": "rectangle"}]}
    checksum = compute_sha256(scene)
    
    payload = {
        "override_reason": "Original reason string",
        "parent_revision_number": 0,
        "scene_json": scene,
        "scene_checksum": checksum
    }
    
    # 1. Register approval
    res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=payload, headers=headers)
    approval_id = res.json()["approval_id"]
    
    # 2. Approve
    client.post(f"/api/v1/test/approve/{approval_id}")
    
    # 3. Attempt force-commit with altered override_reason -> must fail with 403!
    tampered_payload = {**payload, "override_reason": "Altered reason string", "approval_id": approval_id}
    final_res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=tampered_payload, headers=headers)
    assert final_res.status_code == 403


def test_force_commit_hash_binds_scene_json():
    """P0 Security: Verify that changing any field in scene_json breaks the arguments_hash and causes 403."""
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id}
    
    canvas_id = client.post("/api/v1/canvases", json={"title": "Scene Canvas"}, headers=headers).json()["id"]
    
    scene_orig = {"type": "excalidraw", "elements": [{"id": "orig", "type": "rectangle"}]}
    scene_tampered = {"type": "excalidraw", "elements": [{"id": "tampered", "type": "circle"}]}
    
    checksum_orig = compute_sha256(scene_orig)
    checksum_tampered = compute_sha256(scene_tampered)
    
    payload = {
        "override_reason": "Secure hash binding",
        "parent_revision_number": 0,
        "scene_json": scene_orig,
        "scene_checksum": checksum_orig
    }
    
    # 1. Register approval
    res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=payload, headers=headers)
    approval_id = res.json()["approval_id"]
    
    # 2. Approve
    client.post(f"/api/v1/test/approve/{approval_id}")
    
    # 3. Attempt force-commit with tampered scene_json (even with corresponding tampered checksum!) -> must fail with 403!
    tampered_payload = {
        "override_reason": "Secure hash binding",
        "parent_revision_number": 0,
        "scene_json": scene_tampered,
        "scene_checksum": checksum_tampered,
        "approval_id": approval_id
    }
    final_res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=tampered_payload, headers=headers)
    assert final_res.status_code == 403


def test_approval_id_cannot_be_reused():
    """P0 Security: Verify that an approval_id is consumed after one successful execution and cannot be used again."""
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id}
    
    canvas_id = client.post("/api/v1/canvases", json={"title": "Reuse Canvas"}, headers=headers).json()["id"]
    scene = {"type": "excalidraw", "elements": [{"id": "reuse", "type": "circle"}]}
    checksum = compute_sha256(scene)
    
    payload = {
        "override_reason": "One-time usage test",
        "parent_revision_number": 0,
        "scene_json": scene,
        "scene_checksum": checksum
    }
    
    # 1. Register approval
    res = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=payload, headers=headers)
    approval_id = res.json()["approval_id"]
    
    # 2. Approve
    client.post(f"/api/v1/test/approve/{approval_id}")
    
    # 3. Execute first force commit -> must succeed with 200
    commit_payload = {**payload, "approval_id": approval_id}
    res1 = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=commit_payload, headers=headers)
    assert res1.status_code == 200
    
    # 4. Attempt second force commit using the SAME approval_id -> must fail with 403 (APPROVAL_ALREADY_CONSUMED)
    res2 = client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=commit_payload, headers=headers)
    assert res2.status_code == 403
    assert "CONSUMED" in res2.json()["detail"]


@pytest.mark.anyio
async def test_concurrent_force_commits_single_approval():
    """P0 Security: Verify that firing two concurrent force-commits with one approval executes exactly one and rejects the other with 403."""
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id}
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # Create canvas
        create_res = await ac.post("/api/v1/canvases", json={"title": "Concurrent Reuse"}, headers=headers)
        canvas_id = create_res.json()["id"]
        
        scene = {"type": "excalidraw", "elements": [{"id": "c-1", "type": "circle"}]}
        checksum = compute_sha256(scene)
        
        payload = {
            "override_reason": "Concurrent consumption test",
            "parent_revision_number": 0,
            "scene_json": scene,
            "scene_checksum": checksum
        }
        
        # 1. Register approval
        first_res = await ac.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=payload, headers=headers)
        approval_id = first_res.json()["approval_id"]
        
        # 2. Approve
        await ac.post(f"/api/v1/test/approve/{approval_id}")
        
        # 3. Fire concurrent force-commits
        import asyncio
        commit_payload = {**payload, "approval_id": approval_id}
        
        res1, res2 = await asyncio.gather(
            ac.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=commit_payload, headers=headers),
            ac.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=commit_payload, headers=headers),
            return_exceptions=True
        )
        
        statuses = [res1.status_code, res2.status_code]
        assert 200 in statuses
        assert 403 in statuses
        
        # Check that the rejected one had the CONSUMED detail message
        rejected_res = res1 if res1.status_code == 403 else res2
        assert "CONSUMED" in rejected_res.json()["detail"]


def test_no_internal_MIT_headers():
    """P1 Governance: Scan test/verification and visual_shell for any custom internal files incorrectly carrying MIT license headers."""
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
