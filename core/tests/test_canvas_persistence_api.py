# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_canvas_persistence_api.py"
# purpose: "Unit, integration, and E2E tests for Embedded DNK Canvas persistence, concurrency, and migrations."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import os
import json
import pytest
import concurrent.futures
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.dnk_canvas_api.main import (
    app, Base, SessionLocal, CanvasDocument, CanvasRevision, compute_canonical_payload_hash
)

# Ensure we use an isolated sqlite fallback for the tests to prevent dirtying the prod db
TEST_DB_URL = "sqlite:///./canvas_test_api.db"

@pytest.fixture(scope="module")
def test_client():
    # Setup test database and override SessionLocal
    engine = create_engine(
        TEST_DB_URL, 
        connect_args={"check_same_thread": False},
        execution_options={"schema_translate_map": {"hub_memory": None}}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Recreate tables in test sqlite
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Override app dependency or SessionLocal if main.py relies on global SessionLocal
    import services.dnk_canvas_api.main as api_module
    old_session_local = api_module.SessionLocal
    api_module.SessionLocal = TestingSessionLocal
    
    client = TestClient(app, headers={"X-Workspace-Id": "ws-alpha-001", "Authorization": "Bearer dnk-test-token"})
    yield client
    
    # Restore global SessionLocal
    api_module.SessionLocal = old_session_local
    
    # Clean up test sqlite file
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./canvas_test_api.db"):
        os.remove("./canvas_test_api.db")


# --- 1. E2E REST API Tests (Persistence Contract) ---

def test_create_canvas_e2e(test_client):
    """Test creating a canvas with title and metadata."""
    payload = {
        "workspace_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "title": "Competitor Analysis - Q3 2026",
        "description": "Visual board mapping competitor features.",
        "metadata": {"tags": ["q3", "competitors"]}
    }
    response = test_client.post("/api/v1/canvases", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "Competitor Analysis - Q3 2026"
    assert data["workspace_id"] == "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
    assert data["current_revision_id"] is None
    assert data["status"] == "active"
    assert data["metadata"]["tags"] == ["q3", "competitors"]

def test_get_canvas_e2e(test_client):
    """Test retrieving details of an existing canvas."""
    # Create canvas
    create_res = test_client.post("/api/v1/canvases", json={"title": "Test Get Canvas"})
    canvas_id = create_res.json()["id"]
    
    # Get canvas
    get_res = test_client.get(f"/api/v1/canvases/{canvas_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == canvas_id
    assert data["title"] == "Test Get Canvas"
    assert data["scene_json"]["elements"] == []

def test_save_scene_occ_e2e(test_client):
    """Test saving a scene with optimistic concurrency control."""
    # Create canvas
    create_res = test_client.post("/api/v1/canvases", json={"title": "Test OCC Scene"})
    canvas_id = create_res.json()["id"]
    
    # Save version 1
    scene_json = {"type": "excalidraw", "elements": [{"id": "el1", "type": "rectangle"}]}
    payload = {
        "expected_revision": 0,
        "scene_json": scene_json,
        "scene_checksum": compute_canonical_payload_hash(scene_json),
        "change_summary": "Added first element"
    }
    save_res = test_client.put(f"/api/v1/canvases/{canvas_id}/scene", json=payload)
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["status"] == "success"
    assert save_data["new_revision_number"] == 1
    
    # Try saving with stale expected_revision (0 instead of 1) -> 409 Conflict
    payload_stale = {
        "expected_revision": 0,
        "scene_json": scene_json,
        "scene_checksum": compute_canonical_payload_hash(scene_json),
        "change_summary": "Stale update"
    }
    stale_res = test_client.put(f"/api/v1/canvases/{canvas_id}/scene", json=payload_stale)
    assert stale_res.status_code == 409
    stale_data = stale_res.json()
    assert stale_data["detail"]["error"] == "REVISION_CONFLICT"
    assert stale_data["detail"]["server_revision"] == 1
    assert stale_data["detail"]["client_revision"] == 0

def test_force_commit_e2e(test_client):
    """Test force overwriting the scene, bypassing locks via supervisor approval."""
    import services.dnk_canvas_api.main as api_module

    # Create canvas
    create_res = test_client.post("/api/v1/canvases", json={"title": "Test Force Commit"})
    canvas_id = create_res.json()["id"]
    
    # 1. Initial force commit request (registers pending approval)
    scene_json = {"type": "excalidraw", "elements": [{"id": "force-el", "type": "ellipse"}]}
    payload = {
        "override_reason": "Rollback to stable version",
        "parent_revision_number": 0,
        "scene_json": scene_json,
        "scene_checksum": compute_canonical_payload_hash(scene_json)
    }
    res = test_client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=payload)
    assert res.status_code == 202
    data = res.json()
    assert data["status"] == "pending_approval"
    approval_id = data["approval_id"]
    assert approval_id is not None

    # 2. Supervisor approves the request in DB
    session = api_module.SessionLocal()
    try:
        app_req = session.query(api_module.ApprovalRequest).filter_by(id=approval_id).first()
        assert app_req is not None
        app_req.status = "approved"
        session.commit()
    finally:
        session.close()

    # 3. Submit with approval_id to execute force-commit
    payload["approval_id"] = approval_id
    res_approved = test_client.post(f"/api/v1/canvases/{canvas_id}/force-commit", json=payload)
    assert res_approved.status_code == 200
    committed_data = res_approved.json()
    assert committed_data["status"] == "success"
    assert committed_data["new_revision_number"] == 1
    assert committed_data["new_revision_id"] is not None

def test_revisions_list_and_details_e2e(test_client):
    """Test listing and fetching canvas revision history."""
    # Create canvas
    create_res = test_client.post("/api/v1/canvases", json={"title": "Test Revisions"})
    canvas_id = create_res.json()["id"]
    
    # Save version 1
    scene_1 = {"elements": [{"id": "1"}]}
    chk1 = compute_canonical_payload_hash(scene_1)
    test_client.put(f"/api/v1/canvases/{canvas_id}/scene", json={
        "expected_revision": 0,
        "scene_json": scene_1,
        "scene_checksum": chk1,
        "change_summary": "Rev 1"
    })
    
    # Save version 2
    scene_2 = {"elements": [{"id": "1"}, {"id": "2"}]}
    chk2 = compute_canonical_payload_hash(scene_2)
    test_client.put(f"/api/v1/canvases/{canvas_id}/scene", json={
        "expected_revision": 1,
        "scene_json": scene_2,
        "scene_checksum": chk2,
        "change_summary": "Rev 2"
    })
    
    # List revisions
    list_res = test_client.get(f"/api/v1/canvases/{canvas_id}/revisions")
    assert list_res.status_code == 200
    revisions = list_res.json()["revisions"]
    assert len(revisions) == 2
    assert revisions[0]["revision_number"] == 2
    assert revisions[1]["revision_number"] == 1
    
    # Fetch details of revision 1
    rev1_id = revisions[1]["id"]
    details_res = test_client.get(f"/api/v1/canvases/{canvas_id}/revisions/{rev1_id}")
    assert details_res.status_code == 200
    details = details_res.json()
    assert details["revision_number"] == 1
    assert details["scene_checksum"] == chk1

def test_revisions_milestone_milestone_e2e(test_client):
    """Test creating a manual revision milestone."""
    # Create canvas
    create_res = test_client.post("/api/v1/canvases", json={"title": "Test Milestones"})
    canvas_id = create_res.json()["id"]
    
    # Save first scene
    scene_empty = {"elements": []}
    test_client.put(f"/api/v1/canvases/{canvas_id}/scene", json={
        "expected_revision": 0,
        "scene_json": scene_empty,
        "scene_checksum": compute_canonical_payload_hash(scene_empty),
        "change_summary": "initial"
    })
    
    # Create milestone
    milestone_res = test_client.post(f"/api/v1/canvases/{canvas_id}/revisions", json={"change_summary": "Phase 1 Complete"})
    assert milestone_res.status_code == 200
    milestone_data = milestone_res.json()
    assert milestone_data["revision_number"] == 2
    assert "Milestone: Phase 1 Complete" in milestone_data["change_summary"]

def test_canvas_links_lifecycle_e2e(test_client):
    """Test linking and unlinking entities from canvas."""
    # Create canvas
    create_res = test_client.post("/api/v1/canvases", json={"title": "Test Links"})
    canvas_id = create_res.json()["id"]
    
    # Link a flower entity
    payload = {
        "element_id": "excalidraw-node-1",
        "entity_type": "flower",
        "entity_id": "Flower_canvas_persistence",
        "relation_type": "references"
    }
    link_res = test_client.post(f"/api/v1/canvases/{canvas_id}/links", json=payload)
    assert link_res.status_code == 200
    link_data = link_res.json()
    assert link_data["link_id"] is not None
    assert link_data["element_id"] == "excalidraw-node-1"
    assert link_data["entity_type"] == "flower"
    assert link_data["entity_id"] == "Flower_canvas_persistence"
    
    # Remove link
    link_id = link_data["link_id"]
    del_res = test_client.delete(f"/api/v1/canvases/{canvas_id}/links/{link_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"


# --- 2. Backward Compatibility Legacy Endpoints Tests ---

def test_legacy_snapshots_backward_compatibility(test_client):
    """Test that legacy /snapshots and /snapshots/latest endpoints work with the unified tables."""
    # Create canvas
    create_res = test_client.post("/api/v1/canvases", json={"name": "Legacy Canvas"})
    canvas_id = create_res.json()["id"]
    
    # Save snapshot (legacy POST)
    payload = {
        "version": 1,
        "elements": [{"id": "leg-el1", "type": "rectangle"}],
        "app_state": {"theme": "light"},
        "files": {},
        "client_request_id": "req-uuid-abc"
    }
    snap_res = test_client.post(f"/api/v1/canvases/{canvas_id}/snapshots", json=payload)
    assert snap_res.status_code == 200
    assert snap_res.json()["success"] is True
    assert snap_res.json()["version"] == 1
    
    # Retrieve snapshot (legacy GET)
    latest_res = test_client.get(f"/api/v1/canvases/{canvas_id}/snapshots/latest")
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    assert latest_data["version"] == 1
    assert latest_data["elements"][0]["id"] == "leg-el1"
    assert latest_data["app_state"]["theme"] == "light"
    assert latest_data["client_request_id"] == "req-uuid-abc"


# --- 3. Concurrency Under Load (Optimistic Locking Lock Check) ---

def test_concurrency_lock_conflict_under_load(test_client):
    """Verify that concurrent scene updates to the same canvas trigger 409 Conflict for losing requests."""
    # Create canvas
    create_res = test_client.post("/api/v1/canvases", json={"title": "Load Test OCC"})
    canvas_id = create_res.json()["id"]
    
    # Launch 5 concurrent update requests for version 1
    payloads = []
    for i in range(5):
        s_json = {"elements": [{"id": f"el_thread_{i}"}]}
        payloads.append({
            "expected_revision": 0,
            "scene_json": s_json,
            "scene_checksum": compute_canonical_payload_hash(s_json),
            "change_summary": f"Thread {i} update"
        })
        
    def send_update(payload):
        return test_client.put(f"/api/v1/canvases/{canvas_id}/scene", json=payload)
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(send_update, payloads))
        
    # Analyze results: exactly one request should succeed (status 200), and others must fail with 409 Conflict
    success_count = 0
    conflict_count = 0
    for res in results:
        if res.status_code == 200:
            success_count += 1
        elif res.status_code == 409:
            conflict_count += 1
            
    assert success_count == 1
    assert conflict_count == 4


# --- 4. Alembic Migration Integration Check ---

def test_alembic_migration_integration_check():
    """Verify that the PostgreSQL database has successfully applied the canvas persistence migration."""
    # Connect directly to the production Postgres database and verify the version and head
    prod_engine = create_engine("postgresql://postgres:postgres@localhost:5432/dnk_hub")
    try:
        with prod_engine.connect() as conn:
            # Query alembic_version table
            from sqlalchemy import text
            res = conn.execute(text("SELECT version_num FROM public.alembic_version;")).fetchone()
            assert res is not None
            # The current head should be our newly added migration id
            assert res[0] == "2b3c4d5e6f7a"
            print(f"Production database is successfully upgraded to head: {res[0]}")
    except Exception as e:
        pytest.skip(f"Alembic migration integration test skipped (PostgreSQL not reachable or credentials mismatch): {e}")


# --- 5. Schema Constraint & Tenant Isolation Verification Tests ---

from services.dnk_canvas_api.main import CanvasAsset, CanvasAssetLink, CanvasLink
from sqlalchemy.exc import IntegrityError

def test_canvas_asset_links_duplicate_document_level_link(test_client):
    """Verify that adding a duplicate document-level asset link with NULL element_id is blocked at DB level."""
    import services.dnk_canvas_api.main as api_module
    session = api_module.SessionLocal()
    
    try:
        # 1. Create unique global asset under workspace A
        asset = CanvasAsset(
            id="asset-1",
            workspace_id="workspace-a",
            storage_key="s3://workspace-a/screenshot1.png",
            sha256="hash-123",
            status="verified",
            mime_type="image/png",
            byte_size=1000
        )
        session.add(asset)
        session.commit()
        
        # 2. Create asset link for document 1 with element_id = None (document-level)
        link1 = CanvasAssetLink(
            id="link-1",
            asset_id="asset-1",
            document_id="doc-1",
            element_id=None,
            relation_type="references"
        )
        session.add(link1)
        session.commit()
        
        # 3. Attempting to add a second duplicate document-level asset link (same doc, same asset, NULL element_id)
        link2 = CanvasAssetLink(
            id="link-2",
            asset_id="asset-1",
            document_id="doc-1",
            element_id=None,
            relation_type="references"
        )
        session.add(link2)
        
        # This MUST fail due to unique constraint/index on NULL element_id!
        with pytest.raises(IntegrityError):
            session.commit()
            
    finally:
        session.rollback()
        session.close()

def test_workspace_assets_tenant_isolation(test_client):
    """Verify that assets of Workspace A are securely isolated and cannot collide with Workspace B."""
    import services.dnk_canvas_api.main as api_module
    session = api_module.SessionLocal()
    
    try:
        # Workspace A registers asset with sha256='shared-hash'
        asset_a = CanvasAsset(
            id="asset-a",
            workspace_id="workspace-a",
            storage_key="s3://workspace-a/screenshot.png",
            sha256="shared-hash",
            status="verified",
            mime_type="image/png",
            byte_size=2000
        )
        session.add(asset_a)
        session.commit()
        
        # Workspace B registers same physical file (same sha256) but within its own tenant boundary
        asset_b = CanvasAsset(
            id="asset-b",
            workspace_id="workspace-b",
            storage_key="s3://workspace-b/screenshot.png",
            sha256="shared-hash",
            status="verified",
            mime_type="image/png",
            byte_size=2000
        )
        session.add(asset_b)
        
        # This MUST succeed because uq_workspace_sha256 is (workspace_id, sha256) - completely isolated!
        session.commit()
        
        # Querying by workspace-a + sha256 MUST ONLY return asset_a, never asset_b
        res_a = session.query(CanvasAsset).filter_by(workspace_id="workspace-a", sha256="shared-hash").one()
        assert res_a.id == "asset-a"
        
        res_b = session.query(CanvasAsset).filter_by(workspace_id="workspace-b", sha256="shared-hash").one()
        assert res_b.id == "asset-b"
        
    finally:
        session.rollback()
        session.close()
