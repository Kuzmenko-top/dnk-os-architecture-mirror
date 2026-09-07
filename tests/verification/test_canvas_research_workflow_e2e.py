import json
# --- DNK-MRH-HEADER ---
# mrh_id: "test_canvas_research_workflow_e2e.py"
# purpose: "E2E verification tests for DNK Canvas Research Workflow MVP (Competitor -> Evidence Screenshot -> Canvas Element -> Insight -> Flower Draft)."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

import os
os.environ["ENV"] = "test"
os.environ["APP_ENV"] = "test"
os.environ["NODE_ENV"] = "test"

import sys
import pathlib
import hashlib
from uuid import uuid4
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2] # DNK OS
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
services_path = ROOT / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

import pytest
from fastapi.testclient import TestClient
from services.dnk_canvas_api.main import (
    app, Base, engine, SessionLocal,
    CanvasDocument, CanvasCompetitor, CanvasEvidence, CanvasInsight, FlowerDraft, CanvasAuditEvent
)

client = TestClient(app)

import base64
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x03\x00\x05\xfe\x02\xfe\xa7\x9a\x08\x01\x00\x00\x00\x00IEND\xaeB`\x82"
VALID_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\x09\x08\n\x0c\x14\x08\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000062 00000 n \n0000000125 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n200\n%%EOF\n"
UNKNOWN_BINARY_BYTES = b"UNRECOGNIZED_BINARY_DATA_PAYLOAD_123456789"


@pytest.fixture(scope="module", autouse=True)
def setup_db_fixture():
    Base.metadata.create_all(bind=engine)
    yield


def test_end_to_end_research_workflow():
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id, "X-Actor-Type": "user", "X-Actor-Id": "test-user-1"}

    # 1. Create a Canvas Document in Workspace Context
    canvas_res = client.post("/api/v1/canvases", json={
        "title": "Competitor Analysis Canvas",
        "description": "Canvas for competitor breakdown",
        "workspace_id": workspace_id
    }, headers=headers)
    assert canvas_res.status_code == 201
    canvas_id = canvas_res.json()["id"]

    # 2. Create Competitor Record
    comp_res = client.post(f"/api/v1/workspaces/{workspace_id}/competitors", json={
        "name": "Acme Commerce",
        "website_url": "https://acme-commerce.example.com",
        "description": "Direct competitor in headless checkout space"
    }, headers=headers)
    assert comp_res.status_code == 201
    comp_data = comp_res.json()
    competitor_id = comp_data["id"]
    assert comp_data["name"] == "Acme Commerce"
    assert comp_data["status"] == "active"

    # 3. Add Evidence Screenshot with Metadata (storage_mode: fixture)
    fake_image_payload = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    import base64
    raw_bytes = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    expected_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    evidence_res = client.post(f"/api/v1/workspaces/{workspace_id}/evidence/fixture", json={
        "source_url": "https://acme-commerce.example.com/checkout",
        "competitor_id": competitor_id,
        "image_bytes_base64": fake_image_payload,
        "evidence_status": "captured"
    }, headers=headers)
    assert evidence_res.status_code == 201, evidence_res.json()
    evidence_data = evidence_res.json()
    evidence_id = evidence_data["id"]
    assert evidence_data["sha256"] == expected_sha256
    assert evidence_data["evidence_status"] == "captured"
    assert evidence_data["storage_mode"] == "fixture"
    assert evidence_data["source_url"] == "https://acme-commerce.example.com/checkout"

    # 4. Link Evidence Screenshot to Canvas Element (element_id: elem_checkout_cta)
    element_id = "elem_checkout_cta"
    link_res = client.post(f"/api/v1/canvases/{canvas_id}/elements/{element_id}/evidence", json={
        "evidence_id": evidence_id
    }, headers=headers)
    assert link_res.status_code == 201
    assert link_res.json()["status"] == "linked"

    # 5. Verify screenshot is NOT stored as base64 in Canvas Scene
    scene_dict = {
        "elements": [
            {
                "id": element_id,
                "type": "rectangle",
                "customData": {
                    "asset_id": evidence_data["asset_id"],
                    "storage_key": evidence_data["storage_key"]
                }
            }
        ],
        "app_state": {},
        "files": {}
    }
    scene_bytes = json.dumps(scene_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")
    scene_checksum = hashlib.sha256(scene_bytes).hexdigest()

    scene_res = client.put(f"/api/v1/canvases/{canvas_id}/scene", json={
        "expected_revision": 0,
        "scene_json": scene_dict,
        "scene_checksum": scene_checksum,
        "change_summary": "Added linked research asset"
    }, headers=headers)
    print('SCENE RES:', scene_res.status_code, scene_res.text)
    assert scene_res.status_code in [200, 201]
    scene_data = scene_res.json()
    # Confirm base64 is not present in stored elements
    elements_str = str(scene_data)
    assert "data:image/png;base64" not in elements_str

    # 6. Create Insight in proposed status
    insight_res = client.post(f"/api/v1/canvases/{canvas_id}/elements/{element_id}/insights", json={
        "title": "One-Click Checkout Optimization",
        "summary": "Competitor Acme utilizes 1-step checkout resulting in 20% lower friction.",
        "evidence_id": evidence_id,
        "competitor_id": competitor_id
    }, headers=headers)
    assert insight_res.status_code == 201
    insight_data = insight_res.json()
    insight_id = insight_data["id"]
    assert insight_data["status"] == "proposed"
    assert insight_data["source_references"]["evidence_sha256"] == expected_sha256
    assert insight_data["source_references"]["competitor_name"] == "Acme Commerce"

    # 7. Create Flower Draft from Insight (status: draft)
    flower_res = client.post(f"/api/v1/canvases/{canvas_id}/elements/{element_id}/flowers", json={
        "insight_id": insight_id,
        "title": "Flower: Build Accelerated One-Step Checkout Flow",
        "flower_type": "task_flower",
        "content": {
            "mrh_id": "Flower_Checkout_Accel",
            "plant_scale": "flower",
            "acceptance_criteria": ["1-step modal checkout", "Apple Pay support"]
        }
    }, headers=headers)
    assert flower_res.status_code == 201
    flower_data = flower_res.json()
    flower_id = flower_data["id"]
    assert flower_data["status"] == "draft"
    assert flower_data["source_references"]["insight_id"] == insight_id
    assert flower_data["source_references"]["document_id"] == canvas_id

    # 8. Query Aggregated Research Context for Canvas Element
    research_res = client.get(f"/api/v1/canvases/{canvas_id}/elements/{element_id}/research", headers=headers)
    assert research_res.status_code == 200
    research_data = research_res.json()
    assert len(research_data["evidences"]) >= 1
    assert len(research_data["insights"]) >= 1
    assert len(research_data["flowers"]) >= 1

    # 9. Verify Complete Audit Trail Recorded
    audit_events = [a["event_type"] for a in research_data["audit_trail"]]
    assert "asset_linked" in audit_events
    assert "insight_created" in audit_events
    assert "flower_drafted" in audit_events


def test_cross_workspace_access_denial():
    workspace_a = str(uuid4())
    workspace_b = str(uuid4())

    headers_a = {"X-Workspace-Id": workspace_a}
    headers_b = {"X-Workspace-Id": workspace_b}

    # Create Competitor in Workspace A
    comp_res = client.post(f"/api/v1/workspaces/{workspace_a}/competitors", json={
        "name": "Secret Competitor A"
    }, headers=headers_a)
    assert comp_res.status_code == 201
    comp_id = comp_res.json()["id"]

    # Attempt cross-workspace competitor read from Workspace B (Header B vs path A) -> 403
    forbidden_res = client.get(f"/api/v1/workspaces/{workspace_a}/competitors", headers=headers_b)
    assert forbidden_res.status_code == 403

    # Create Evidence in Workspace B
    ev_res = client.post(f"/api/v1/workspaces/{workspace_b}/evidence/fixture", json={
        "source_url": "https://secret-b.example.com",
        "image_bytes_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    }, headers=headers_b)
    assert ev_res.status_code == 201
    evidence_b_id = ev_res.json()["id"]

    # Create Canvas in Workspace A
    canvas_res = client.post("/api/v1/canvases", json={"title": "Canvas A", "workspace_id": workspace_a}, headers=headers_a)
    assert canvas_res.status_code == 201
    canvas_a_id = canvas_res.json()["id"]

    # Attempt linking Workspace B evidence to Workspace A Canvas -> 403 Forbidden
    link_forbidden = client.post(f"/api/v1/canvases/{canvas_a_id}/elements/elem_1/evidence", json={
        "evidence_id": evidence_b_id
    }, headers=headers_a)
    assert link_forbidden.status_code == 403


def test_duplicate_asset_idempotency():
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id, "X-Actor-Type": "user"}

    # Presign, upload, and commit an asset
    presign_res = client.post(f"/api/v1/workspaces/{workspace_id}/assets/presign", json={
        "filename": "idempotency.png", "mime_type": "image/png"
    }, headers=headers)
    asset_id = presign_res.json()["asset_id"]
    upload_url = presign_res.json()["upload_url"]
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    client.put(upload_url, content=png_bytes, headers=headers)
    client.post(f"/api/v1/workspaces/{workspace_id}/assets/{asset_id}/commit", json={}, headers=headers)

    # First post
    res1 = client.post(f"/api/v1/workspaces/{workspace_id}/evidence", json={
        "asset_id": asset_id,
        "source_url": "https://example.com/asset1"
    }, headers=headers)
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["idempotent"] is False

    # Second post with identical asset in same workspace -> returns existing evidence idempotently
    res2 = client.post(f"/api/v1/workspaces/{workspace_id}/evidence", json={
        "asset_id": asset_id,
        "source_url": "https://example.com/asset1"
    }, headers=headers)
    assert res2.status_code in [200, 201]
    data2 = res2.json()
    assert data2["id"] == data1["id"]
    assert data2["idempotent"] is True


def test_agent_self_approval_prevention():
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id}

    # Setup canvas, element, insight, flower
    canvas_res = client.post("/api/v1/canvases", json={"title": "Approval Test Canvas", "workspace_id": workspace_id}, headers=headers)
    canvas_id = canvas_res.json()["id"]

    insight_res = client.post(f"/api/v1/canvases/{canvas_id}/elements/el_approval/insights", json={
        "title": "Insight to Approve",
        "summary": "Summary"
    }, headers=headers)
    insight_id = insight_res.json()["id"]

    flower_res = client.post(f"/api/v1/canvases/{canvas_id}/elements/el_approval/flowers", json={
        "insight_id": insight_id,
        "title": "Flower to Approve"
    }, headers=headers)
    flower_id = flower_res.json()["id"]

    # 1. Agent attempts to self-approve Insight -> 403 Forbidden
    agent_insight_res = client.post(
        f"/api/v1/insights/{insight_id}/approve",
        json={"actor_type": "agent", "actor_id": "agent-autonomy-007"},
        headers={"X-Workspace-Id": workspace_id, "X-Actor-Type": "agent"}
    )
    assert agent_insight_res.status_code == 403
    assert "Agent cannot self-approve" in agent_insight_res.json()["detail"]

    # 2. Agent attempts to self-approve Flower -> 403 Forbidden
    agent_flower_res = client.post(
        f"/api/v1/flowers/{flower_id}/approve",
        json={"actor_type": "agent", "actor_id": "agent-autonomy-007"},
        headers={"X-Workspace-Id": workspace_id, "X-Actor-Type": "agent"}
    )
    assert agent_flower_res.status_code == 403
    assert "Agent cannot self-approve" in agent_flower_res.json()["detail"]

    # 3. Human User approves Insight -> 200 OK
    user_insight_res = client.post(
        f"/api/v1/insights/{insight_id}/approve",
        json={"actor_type": "user", "actor_id": "human-reviewer"},
        headers={"X-Workspace-Id": workspace_id, "X-Actor-Type": "user"}
    )
    assert user_insight_res.status_code == 200
    assert user_insight_res.json()["status"] == "approved"

    # 4. Human User approves Flower -> 200 OK
    user_flower_res = client.post(
        f"/api/v1/flowers/{flower_id}/approve",
        json={"actor_type": "user", "actor_id": "human-reviewer"},
        headers={"X-Workspace-Id": workspace_id, "X-Actor-Type": "user"}
    )
    assert user_flower_res.status_code == 200
    assert user_flower_res.json()["status"] == "approved"


def test_flower_creation_requires_saved_insight():
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id}

    canvas_res = client.post("/api/v1/canvases", json={"title": "Test Canvas", "workspace_id": workspace_id}, headers=headers)
    canvas_id = canvas_res.json()["id"]

    # Attempt to draft Flower with non-existent insight_id -> 400 Bad Request
    fake_insight_id = str(uuid4())
    res = client.post(f"/api/v1/canvases/{canvas_id}/elements/el_fake/flowers", json={
        "insight_id": fake_insight_id,
        "title": "Invalid Flower"
    }, headers=headers)
    assert res.status_code == 400
    assert "Valid Insight is required" in res.json()["detail"]


def test_production_binary_asset_evidence_flow():
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id, "X-Actor-Type": "user"}

    # 1. Request Presigned Upload URL for binary screenshot
    presign_res = client.post(f"/api/v1/workspaces/{workspace_id}/assets/presign", json={
        "filename": "checkout_pdp_screenshot.png",
        "mime_type": "image/png"
    }, headers=headers)
    assert presign_res.status_code == 201
    presign_data = presign_res.json()
    asset_id = presign_data["asset_id"]
    upload_url = presign_data["upload_url"]

    # 2. Simulate Binary Upload & Commit Asset
    raw_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    binary_sha256 = hashlib.sha256(raw_png_bytes).hexdigest()

    upload_res = client.put(upload_url, content=raw_png_bytes, headers=headers)
    assert upload_res.status_code == 200

    commit_res = client.post(f"/api/v1/workspaces/{workspace_id}/assets/{asset_id}/commit", json={
        "client_sha256": binary_sha256,
        "client_byte_size": len(raw_png_bytes)
    }, headers=headers)
    assert commit_res.status_code in [200, 201]

    # 3. Create Evidence referencing committed CanvasAsset ID
    ev_res = client.post(f"/api/v1/workspaces/{workspace_id}/evidence", json={
        "source_url": "https://acme-commerce.example.com/pdp",
        "asset_id": asset_id
    }, headers=headers)
    assert ev_res.status_code == 201
    ev_data = ev_res.json()
    assert ev_data["asset_id"] == asset_id
    assert ev_data["sha256"] == binary_sha256


def test_asset_hardening_and_contract_verification(monkeypatch):
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id, "X-Actor-Type": "user"}

    # 1. Missing storage object -> rejected / 400
    presign_res = client.post(f"/api/v1/workspaces/{workspace_id}/assets/presign", json={
        "filename": "test.png", "mime_type": "image/png"
    }, headers=headers)
    asset_id_1 = presign_res.json()["asset_id"]
    commit_res_1 = client.post(f"/api/v1/workspaces/{workspace_id}/assets/{asset_id_1}/commit", json={}, headers=headers)
    assert commit_res_1.status_code == 400
    assert "Missing storage object" in commit_res_1.json()["detail"]
    
    # 1.5 Retry commit on rejected asset -> 409 Conflict
    commit_res_1b = client.post(f"/api/v1/workspaces/{workspace_id}/assets/{asset_id_1}/commit", json={}, headers=headers)
    assert commit_res_1b.status_code == 409
    assert "Cannot commit asset in terminal status 'rejected'" in commit_res_1b.json()["detail"]

    # 2. Fake client SHA -> rejected / 400
    presign_res = client.post(f"/api/v1/workspaces/{workspace_id}/assets/presign", json={
        "filename": "fake_sha.png", "mime_type": "image/png"
    }, headers=headers)
    asset_id_2 = presign_res.json()["asset_id"]
    upload_url_2 = presign_res.json()["upload_url"]
    client.put(upload_url_2, content=VALID_PNG_BYTES, headers=headers)
    commit_res_2 = client.post(f"/api/v1/workspaces/{workspace_id}/assets/{asset_id_2}/commit", json={
        "client_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
    }, headers=headers)
    assert commit_res_2.status_code == 400
    assert "SHA256 mismatch" in commit_res_2.json()["detail"]

    # 3. Byte-size mismatch -> rejected / 400
    presign_res = client.post(f"/api/v1/workspaces/{workspace_id}/assets/presign", json={
        "filename": "size_mismatch.png", "mime_type": "image/png"
    }, headers=headers)
    asset_id_3 = presign_res.json()["asset_id"]
    client.put(presign_res.json()["upload_url"], content=VALID_PNG_BYTES, headers=headers)
    commit_res_3 = client.post(f"/api/v1/workspaces/{workspace_id}/assets/{asset_id_3}/commit", json={
        "client_byte_size": 99999
    }, headers=headers)
    assert commit_res_3.status_code == 400
    assert "Byte size mismatch" in commit_res_3.json()["detail"]
    
    # 3.5 Retry commit on rejected asset -> 409 Conflict
    commit_res_3b = client.post(f"/api/v1/workspaces/{workspace_id}/assets/{asset_id_3}/commit", json={}, headers=headers)
    assert commit_res_3b.status_code == 409

    # 4. MIME checking combinations
    # 4a. Unknown binary -> rejected
    presign_res = client.post(f"/api/v1/workspaces/{workspace_id}/assets/presign", json={
        "filename": "unknown.bin", "mime_type": "image/png"
    }, headers=headers)
    asset_id_4a = presign_res.json()["asset_id"]
    client.put(presign_res.json()["upload_url"], content=UNKNOWN_BINARY_BYTES, headers=headers)
    commit_res_4a = client.post(f"/api/v1/workspaces/{workspace_id}/assets/{asset_id_4a}/commit", json={}, headers=headers)
    assert commit_res_4a.status_code == 400
    assert "MIME mismatch" in commit_res_4a.json()["detail"]
    
    # 4b. MIME mismatch (JPEG content but claimed PNG) -> rejected
    presign_res = client.post(f"/api/v1/workspaces/{workspace_id}/assets/presign", json={
        "filename": "fake_png.png", "mime_type": "image/png"
    }, headers=headers)
    asset_id_4b = presign_res.json()["asset_id"]
    client.put(presign_res.json()["upload_url"], content=VALID_JPEG_BYTES, headers=headers)
    commit_res_4b = client.post(f"/api/v1/workspaces/{workspace_id}/assets/{asset_id_4b}/commit", json={}, headers=headers)
    assert commit_res_4b.status_code == 400
    assert "MIME mismatch" in commit_res_4b.json()["detail"]

    # 5. Actual valid binary upload -> verified
    presign_res = client.post(f"/api/v1/workspaces/{workspace_id}/assets/presign", json={
        "filename": "valid.png", "mime_type": "image/png"
    }, headers=headers)
    asset_id_5 = presign_res.json()["asset_id"]
    valid_sha = hashlib.sha256(VALID_PNG_BYTES).hexdigest()
    client.put(presign_res.json()["upload_url"], content=VALID_PNG_BYTES, headers=headers)
    commit_res_5 = client.post(f"/api/v1/workspaces/{workspace_id}/assets/{asset_id_5}/commit", json={
        "client_sha256": valid_sha,
        "client_byte_size": len(VALID_PNG_BYTES)
    }, headers=headers)
    assert commit_res_5.status_code == 200
    assert commit_res_5.json()["status"] == "verified"
    
    # 5.5 Retry commit on verified asset -> 409 Conflict
    commit_res_5b = client.post(f"/api/v1/workspaces/{workspace_id}/assets/{asset_id_5}/commit", json={}, headers=headers)
    assert commit_res_5b.status_code == 409
    assert "Cannot commit asset in terminal status 'verified'" in commit_res_5b.json()["detail"]

    # 6. Canonical evidence metadata includes S3 verified: False
    ev_res_6 = client.post(f"/api/v1/workspaces/{workspace_id}/evidence", json={
        "asset_id": asset_id_5,
        "source_url": "https://example.com/valid"
    }, headers=headers)
    assert ev_res_6.status_code == 201
    assert ev_res_6.json()["sha256"] == valid_sha
    assert ev_res_6.json()["production_s3_verified"] is False
    assert ev_res_6.json()["runtime_scope"] == "local_fixture_storage"

    # 7. Missing canvas -> 404
    missing_canvas_id = str(uuid4())
    res_7 = client.get(f"/api/v1/canvases/{missing_canvas_id}/elements/elem_1/research", headers=headers)
    assert res_7.status_code == 404
    assert "Canvas document not found" in res_7.json()["detail"]

    # 8. Wrong workspace -> 403
    other_workspace_headers = {"X-Workspace-Id": str(uuid4()), "X-Actor-Type": "user"}
    canvas_res_8 = client.post("/api/v1/canvases", json={"title": "Canvas 8", "workspace_id": workspace_id}, headers=headers)
    canvas_id_8 = canvas_res_8.json()["id"]
    res_8 = client.get(f"/api/v1/canvases/{canvas_id_8}/elements/elem_1/research", headers=other_workspace_headers)
    assert res_8.status_code == 403

    # 9. Legacy canonical Base64 payload -> 422
    legacy_res = client.post(f"/api/v1/workspaces/{workspace_id}/evidence", json={
        "source_url": "https://example.com/legacy",
        "image_bytes_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    }, headers=headers)
    assert legacy_res.status_code == 422

    # 10. Fixture Base64 in production -> 404 (using monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    prod_res = client.post(f"/api/v1/workspaces/{workspace_id}/evidence/fixture", json={
        "source_url": "https://example.com/fixture",
        "image_bytes_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    }, headers=headers)
    assert prod_res.status_code == 404
    monkeypatch.delenv("APP_ENV", raising=False)


def test_actor_type_conflict_recrejection():
    workspace_id = str(uuid4())
    headers = {"X-Workspace-Id": workspace_id}

    canvas_res = client.post("/api/v1/canvases", json={"title": "Actor Test Canvas", "workspace_id": workspace_id}, headers=headers)
    canvas_id = canvas_res.json()["id"]

    insight_res = client.post(f"/api/v1/canvases/{canvas_id}/elements/el_actor/insights", json={
        "title": "Actor Test Insight",
        "summary": "Summary"
    }, headers=headers)
    insight_id = insight_res.json()["id"]

    # Discrepancy: Header claims agent, body claims user -> 400 Bad Request
    conflict_res = client.post(
        f"/api/v1/insights/{insight_id}/approve",
        json={"actor_type": "user", "actor_id": "spoofed-user"},
        headers={"X-Workspace-Id": workspace_id, "X-Actor-Type": "agent"}
    )
    assert conflict_res.status_code == 400
    assert "Actor type discrepancy" in conflict_res.json()["detail"]


def test_missing_workspace_header_unauthorized():
    # Attempting to query endpoints without X-Workspace-Id or Authorization header -> 401 Unauthorized
    res = client.get("/api/v1/workspaces/00000000-0000-0000-0000-000000000000/competitors")
    assert res.status_code == 401
    assert "Workspace identity context missing" in res.json()["detail"]
