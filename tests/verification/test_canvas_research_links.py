# --- DNK-MRH-HEADER ---
# mrh_id: "test_canvas_research_links.py"
# purpose: "Comprehensive verification suite for Phase 2 DNK Canvas Research Integration & Entity Linking"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import pytest
import hashlib
import uuid
from fastapi.testclient import TestClient

from services.dnk_canvas_api.main import app, SessionLocal, CanvasDocument, CanvasAsset, CanvasLink, CanvasAssetLink, CanvasAuditEvent

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_test_db():
    db = SessionLocal()
    try:
        # Cleanup
        db.query(CanvasAssetLink).delete()
        db.query(CanvasLink).delete()
        db.query(CanvasAsset).delete()
        db.query(CanvasAuditEvent).delete()
        db.query(CanvasDocument).delete()
        db.commit()
    finally:
        db.close()
    yield

def create_test_canvas(workspace_id: str, title: str = "Research Canvas") -> str:
    db = SessionLocal()
    try:
        doc_id = str(uuid.uuid4())
        doc = CanvasDocument(
            id=doc_id,
            workspace_id=workspace_id,
            title=title,
            document_type="excalidraw",
            created_by="user-test",
            status="active"
        )
        db.add(doc)
        db.commit()
        return doc_id
    finally:
        db.close()

def test_document_and_element_level_link_creation():
    ws_id = str(uuid.uuid4())
    canvas_id = create_test_canvas(ws_id)
    headers = {"X-Workspace-Id": ws_id, "X-Actor-Type": "human", "X-Actor-Id": "user-1"}

    # 1. Document-level link
    res1 = client.post(
        f"/api/v1/canvases/{canvas_id}/links",
        json={"entity_type": "competitor", "entity_id": "comp-123", "relation_type": "references"},
        headers=headers
    )
    assert res1.status_code == 200, res1.text
    data1 = res1.json()
    assert data1["canvas_id"] == canvas_id
    assert data1["element_id"] is None
    assert data1["entity_type"] == "competitor"

    # 2. Element-level link
    res2 = client.post(
        f"/api/v1/canvases/{canvas_id}/links",
        json={"element_id": "elem-456", "entity_type": "flower", "entity_id": "flower-789", "relation_type": "references"},
        headers=headers
    )
    assert res2.status_code == 200, res2.text
    data2 = res2.json()
    assert data2["element_id"] == "elem-456"
    assert data2["entity_type"] == "flower"

def test_duplicate_link_rejection_and_idempotency():
    ws_id = str(uuid.uuid4())
    canvas_id = create_test_canvas(ws_id)
    headers = {"X-Workspace-Id": ws_id}

    payload = {"element_id": "elem-100", "entity_type": "insight", "entity_id": "ins-1", "relation_type": "evidence"}
    
    res1 = client.post(f"/api/v1/canvases/{canvas_id}/links", json=payload, headers=headers)
    assert res1.status_code == 200
    link_id_1 = res1.json()["link_id"]

    res2 = client.post(f"/api/v1/canvases/{canvas_id}/links", json=payload, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["link_id"] == link_id_1
    assert res2.json().get("already_exists") is True

def test_workspace_isolation_and_cross_access_denial():
    ws_a = str(uuid.uuid4())
    ws_b = str(uuid.uuid4())
    canvas_a = create_test_canvas(ws_a, "Canvas Workspace A")

    # Try creating link with wrong workspace header
    res = client.post(
        f"/api/v1/canvases/{canvas_a}/links",
        json={"entity_type": "adr", "entity_id": "adr-001"},
        headers={"X-Workspace-Id": ws_b}
    )
    assert res.status_code == 403

def test_asset_presign_commit_lifecycle_and_validation():
    ws_id = str(uuid.uuid4())
    canvas_id = create_test_canvas(ws_id)
    headers = {"X-Workspace-Id": ws_id}

    sha256_hash = hashlib.sha256(b"screenshot-bytes-1").hexdigest()

    # 1. Reject invalid MIME type
    res_invalid_mime = client.post(
        f"/api/v1/canvases/{canvas_id}/assets/presign",
        json={"sha256": sha256_hash, "mime_type": "application/x-sh", "byte_size": 1024},
        headers=headers
    )
    assert res_invalid_mime.status_code == 400

    # 2. Valid presign
    res_presign = client.post(
        f"/api/v1/canvases/{canvas_id}/assets/presign",
        json={"sha256": sha256_hash, "mime_type": "image/png", "byte_size": 2048},
        headers=headers
    )
    assert res_presign.status_code == 200
    presign_data = res_presign.json()
    assert presign_data["status"] == "pending_upload"
    assert presign_data["deduplicated"] is False
    asset_id = presign_data["asset_id"]

    # 3. Commit with byte size mismatch -> rejected
    res_bad_commit = client.post(
        f"/api/v1/canvases/{canvas_id}/assets/{asset_id}/commit",
        json={"uploaded_byte_size": 9999},
        headers=headers
    )
    assert res_bad_commit.status_code == 400

    # Re-presign after rejection
    res_presign2 = client.post(
        f"/api/v1/canvases/{canvas_id}/assets/presign",
        json={"sha256": sha256_hash, "mime_type": "image/png", "byte_size": 2048},
        headers=headers
    )
    asset_id2 = res_presign2.json()["asset_id"]

    # 4. Valid commit
    res_commit = client.post(
        f"/api/v1/canvases/{canvas_id}/assets/{asset_id2}/commit",
        json={"uploaded_byte_size": 2048, "element_id": "img-elem-1"},
        headers=headers
    )
    assert res_commit.status_code == 200
    assert res_commit.json()["status"] == "verified"

    # 5. Re-presign same SHA in same workspace -> deduplicated (instant verified)
    res_dedup = client.post(
        f"/api/v1/canvases/{canvas_id}/assets/presign",
        json={"sha256": sha256_hash, "mime_type": "image/png", "byte_size": 2048},
        headers=headers
    )
    assert res_dedup.status_code == 200
    dedup_data = res_dedup.json()
    assert dedup_data["status"] == "verified"
    assert dedup_data["deduplicated"] is True
    assert dedup_data["asset_id"] == asset_id2

    # 6. Re-presign same SHA in DIFFERENT workspace -> NOT deduplicated, separate asset
    ws_other = str(uuid.uuid4())
    canvas_other = create_test_canvas(ws_other)
    res_other_ws = client.post(
        f"/api/v1/canvases/{canvas_other}/assets/presign",
        json={"sha256": sha256_hash, "mime_type": "image/png", "byte_size": 2048},
        headers={"X-Workspace-Id": ws_other}
    )
    assert res_other_ws.status_code == 200
    other_data = res_other_ws.json()
    assert other_data["asset_id"] != asset_id2
    assert other_data["deduplicated"] is False

def test_agent_delete_approval_gate_contract():
    ws_id = str(uuid.uuid4())
    canvas_id = create_test_canvas(ws_id)

    # Create link as human
    res_link = client.post(
        f"/api/v1/canvases/{canvas_id}/links",
        json={"entity_type": "flower", "entity_id": "flower-001"},
        headers={"X-Workspace-Id": ws_id, "X-Actor-Type": "human"}
    )
    link_id = res_link.json()["link_id"]

    # Delete link as agent without approval -> 202 Accepted pending_approval
    res_agent_del = client.delete(
        f"/api/v1/canvases/{canvas_id}/links/{link_id}",
        headers={"X-Workspace-Id": ws_id, "X-Actor-Type": "agent", "X-Actor-Id": "agent-gerych"}
    )
    assert res_agent_del.status_code == 202
    del_data = res_agent_del.json()
    assert del_data["status"] == "pending_approval"
    approval_id = del_data["approval_id"]
    assert "binding" in del_data
    assert del_data["binding"]["canvas_id"] == canvas_id
    assert del_data["binding"]["link_id"] == link_id

    # Delete link as human -> 200 OK deleted immediately
    res_human_del = client.delete(
        f"/api/v1/canvases/{canvas_id}/links/{link_id}",
        headers={"X-Workspace-Id": ws_id, "X-Actor-Type": "human", "X-Actor-Id": "user-maxim"}
    )
    assert res_human_del.status_code == 200
    assert res_human_del.json()["status"] == "deleted"

def test_base64_scene_rejection():
    ws_id = str(uuid.uuid4())
    canvas_id = create_test_canvas(ws_id)
    headers = {"X-Workspace-Id": ws_id}

    scene_with_base64 = {
        "expected_revision": 0,
        "scene_json": {
            "type": "excalidraw",
            "elements": [
                {"id": "el1", "type": "image", "src": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}
            ]
        },
        "scene_checksum": "dummy"
    }

    # Compute checksum
    scene_str = client.app.json_dump if hasattr(client.app, "json_dump") else None
    import json
    s_str = json.dumps(scene_with_base64["scene_json"], sort_keys=True, separators=(',', ':'))
    scene_with_base64["scene_checksum"] = hashlib.sha256(s_str.encode('utf-8')).hexdigest()

    res = client.put(f"/api/v1/canvases/{canvas_id}/scene", json=scene_with_base64, headers=headers)
    assert res.status_code == 400
    assert "Base64" in res.json()["detail"]
