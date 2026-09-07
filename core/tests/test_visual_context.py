# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_visual_context.py"
# purpose: "Unit, integration, and E2E tests for Visual Selection Context Bridge (VSCB) and screenshot ingestion."
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

import os
import json
import pytest
from datetime import datetime
from core.visual_context import VisualContext, VisualContextBridge
from core.swarm_engine import Worker, Supervisor

TEST_UPLOADS_DIR = "core/tests/uploads_sandbox"
TEST_REGISTRY_PATH = "core/tests/visual_context_test_registry.json"
TEST_MEM_STORAGE_PATH = "core/tests/scones_swarm_visual_test.json"

@pytest.fixture
def vscb_setup():
    # Teardown pre-existing files
    if os.path.exists(TEST_REGISTRY_PATH):
        os.remove(TEST_REGISTRY_PATH)
    if os.path.exists(TEST_UPLOADS_DIR):
        for f in os.listdir(TEST_UPLOADS_DIR):
            os.remove(os.path.join(TEST_UPLOADS_DIR, f))
        os.rmdir(TEST_UPLOADS_DIR)
        
    bridge = VisualContextBridge(upload_dir=TEST_UPLOADS_DIR, registry_path=TEST_REGISTRY_PATH)
    
    yield bridge
    
    # Teardown
    if os.path.exists(TEST_REGISTRY_PATH):
        os.remove(TEST_REGISTRY_PATH)
    if os.path.exists(TEST_UPLOADS_DIR):
        for f in os.listdir(TEST_UPLOADS_DIR):
            os.remove(os.path.join(TEST_UPLOADS_DIR, f))
        os.rmdir(TEST_UPLOADS_DIR)


# --- 1. Unit/Integration Tests (Min 8 required) ---

def test_dto_serialization_and_validation(vscb_setup):
    """Test 1: Verify VisualContext DTO validation and serialization using Pydantic."""
    v_ctx = VisualContext(
        context_id="test-ctx-123",
        tenant_id="tenant_1",
        workspace_id="ws_1",
        canvas_id="canvas_99",
        selection_bounds={"x": 100, "y": 200, "width": 400, "height": 300},
        image_asset_id="VSCB-IMG-test.png",
        source_node_ids=["node_1", "node_2"],
        extracted_text="Design mock",
        visual_metadata={"theme": "dark"}
    )
    
    # Verify serialization
    data = v_ctx.dict()
    assert data["context_id"] == "test-ctx-123"
    assert data["selection_bounds"]["width"] == 400
    assert "node_1" in data["source_node_ids"]
    assert isinstance(data["created_at"], datetime)

def test_idempotent_context_id_generation(vscb_setup):
    """Test 2: Verify that stable context_id is generated idempotently for identical selections."""
    bounds = {"x": 10, "y": 20, "w": 100, "h": 100}
    nodes = ["node_B", "node_A"]
    
    id1 = vscb_setup._generate_stable_context_id("canvas_1", nodes, bounds)
    id2 = vscb_setup._generate_stable_context_id("canvas_1", ["node_A", "node_B"], bounds) # different node list ordering
    
    assert id1 == id2 # Sorting is handled, returning stable idempotent key
    
    id_different = vscb_setup._generate_stable_context_id("canvas_1", nodes, {"x": 11, "y": 20, "w": 100, "h": 100})
    assert id1 != id_different

def test_ingest_selection_saving_assets(vscb_setup):
    """Test 3: Verify selection ingestion physically persists screenshot bytes to upload directory."""
    bounds = {"x": 0, "y": 0, "w": 200, "h": 150}
    image_bytes = b"MOCK_PNG_IMAGE_DATA_BYTES"
    
    v_ctx = vscb_setup.ingest_selection(
        tenant_id="tenant_1",
        workspace_id="ws_1",
        canvas_id="canvas_1",
        selection_bounds=bounds,
        image_data=image_bytes,
        source_node_ids=["node_1"],
        extracted_text="Sample OCR outcome"
    )
    
    # Check physical asset presence on disk
    asset_path = os.path.join(vscb_setup.upload_dir, v_ctx.image_asset_id)
    assert os.path.exists(asset_path)
    with open(asset_path, "rb") as f:
        assert f.read() == image_bytes

def test_ingest_selection_idempotency_caching(vscb_setup):
    """Test 4: Verify that multiple identical ingestions do not write duplicates or multiply registry records."""
    bounds = {"x": 15, "y": 30, "w": 250, "h": 200}
    image_bytes = b"PNG_DATA"
    nodes = ["node_A"]
    
    # First Ingestion
    ctx1 = vscb_setup.ingest_selection("t1", "ws_1", "canvas_1", bounds, image_bytes, nodes)
    reg_size_1 = len(vscb_setup.registry)
    
    # Second Ingestion (exact same selection)
    ctx2 = vscb_setup.ingest_selection("t1", "ws_1", "canvas_1", bounds, image_bytes, nodes)
    reg_size_2 = len(vscb_setup.registry)
    
    assert ctx1.context_id == ctx2.context_id
    assert reg_size_1 == reg_size_2 # No registry duplication
    assert len(os.listdir(vscb_setup.upload_dir)) == 1 # Only one screenshot file written

def test_get_context_by_id_isolation_enforcement(vscb_setup):
    """Test 5: Verify absolute security boundaries and permission errors on mismatching tenant context requests."""
    bounds = {"x": 0, "y": 0, "w": 50, "h": 50}
    
    v_ctx = vscb_setup.ingest_selection(
        tenant_id="tenant_A",
        workspace_id="workspace_1",
        canvas_id="canvas_1",
        selection_bounds=bounds,
        image_data=None,
        source_node_ids=[]
    )
    
    # Retrieve with authorized context -> must pass
    ctx_authorized = vscb_setup.get_context_by_id(v_ctx.context_id, "tenant_A", "workspace_1")
    assert ctx_authorized is not None
    assert ctx_authorized.context_id == v_ctx.context_id
    
    # Retrieve with mismatching tenant_id -> must raise PermissionError
    with pytest.raises(PermissionError) as exc:
        vscb_setup.get_context_by_id(v_ctx.context_id, "tenant_B", "workspace_1")
    assert "is unauthorized to access Context" in str(exc.value)

def test_node_workspace_registration_and_strict_ownership(vscb_setup):
    """Test 6: Verify strict node ownership check. Nodes from another workspace block selection ingestion."""
    # Register Node 1 under Tenant A, Workspace 1
    vscb_setup.register_node_workspace("node_1", "tenant_A", "workspace_1")
    
    # Attempt to ingest Node 1 under Tenant B, Workspace 1 -> must raise PermissionError
    with pytest.raises(PermissionError) as exc:
        vscb_setup.ingest_selection(
            tenant_id="tenant_B",
            workspace_id="workspace_1",
            canvas_id="canvas_1",
            selection_bounds={},
            image_data=None,
            source_node_ids=["node_1"]
        )
    assert "Isolation Violation: Node" in str(exc.value)

def test_bind_to_task_context_injection(vscb_setup):
    """Test 7: Verify visual context metadata and OCR is successfully bound to task context payload."""
    bounds = {"x": 100, "y": 100, "w": 500, "h": 400}
    v_ctx = vscb_setup.ingest_selection(
        tenant_id="tenant_1",
        workspace_id="workspace_1",
        canvas_id="canvas_1",
        selection_bounds=bounds,
        image_data=b"test",
        source_node_ids=["node_A"],
        extracted_text="MOCK_OCR_TEXT"
    )
    
    task_payload = {"id": "task_100", "query": "Process visual feedback"}
    
    enriched_task = vscb_setup.bind_to_task_context(
        v_ctx.context_id, task_payload, "tenant_1", "workspace_1"
    )
    
    assert enriched_task["visual_context_id"] == v_ctx.context_id
    assert "MOCK_OCR_TEXT" in enriched_task["additional_context"]
    assert v_ctx.image_asset_id in enriched_task["additional_context"]

def test_failed_ocr_missing_screenshot_resilience(vscb_setup):
    """Test 8: Verify visual context bridge is robust and does not crash task context if visual context is missing."""
    task_payload = {"id": "task_100", "query": "Process visual feedback"}
    
    # Try binding a completely non-existent context_id -> must fail gracefully, returning unmodified payload
    enriched_task = vscb_setup.bind_to_task_context(
        "NON-EXISTENT-ID", task_payload, "tenant_1", "workspace_1"
    )
    
    assert enriched_task == task_payload # No crash, no modification


# --- 2. End-to-End (E2E) Test (1 required) ---

def test_e2e_canvas_selection_to_worker_execution(vscb_setup):
    """
    E2E Test: Verify entire visual context flow.
    Selection ➔ Ingestion ➔ Task Context Binding ➔ Supervisor/Worker execution loop.
    """
    if os.path.exists(TEST_MEM_STORAGE_PATH):
        os.remove(TEST_MEM_STORAGE_PATH)
        
    # 1. Register canvas nodes ownership to Tenant A
    vscb_setup.register_node_workspace("button_save_node", "tenant_A", "workspace_main")
    vscb_setup.register_node_workspace("panel_header_node", "tenant_A", "workspace_main")
    
    # 2. Ingest user selection and screenshot
    v_ctx = vscb_setup.ingest_selection(
        tenant_id="tenant_A",
        workspace_id="workspace_main",
        canvas_id="main_canvas_01",
        selection_bounds={"x": 50, "y": 100, "w": 300, "h": 200},
        image_data=b"SCREENSHOT_E2E_BYTES",
        source_node_ids=["button_save_node", "panel_header_node"],
        extracted_text="Save Changes Button",
        visual_metadata={"browser": "chrome"}
    )
    
    # 3. Setup Supervisor for Tenant A
    supervisor_A = Supervisor("supervisor_A", tenant_id="tenant_A", workspace_id="workspace_main")
    supervisor_A.provider._engine.storage_path = TEST_MEM_STORAGE_PATH
    supervisor_A.provider._engine.memories = []
    supervisor_A.provider._engine.save_memories()
    
    # Setup Worker which processes task, evaluating the context
    received_context = None
    def worker_handler(task, context):
        nonlocal received_context
        received_context = context
        return {"summary": "Processed button alignment from visual context.", "status": "ok"}
        
    worker = Worker("ux_designer_worker", "ui-designer", worker_handler)
    
    # 4. Supervisor executes worker, passing the context_id and context_bridge!
    task = {"id": "t_visual_01", "query": "Align elements matching visual selection details", "topic": "visual-alignment"}
    
    pipeline_res = supervisor_A.execute_task_pipeline(
        task, worker, max_retries=3,
        visual_context_id=v_ctx.context_id,
        context_bridge=vscb_setup
    )
    
    # Verify completed status
    assert pipeline_res["status"] == "completed"
    assert pipeline_res["result"]["status"] == "ok"
    
    # Verify worker context contains BOTH retrieved memory AND the bound visual selection OCR details!
    assert received_context is not None
    assert "Save Changes Button" in received_context
    assert v_ctx.image_asset_id in received_context
    
    # Cleanup memory test storage
    if os.path.exists(TEST_MEM_STORAGE_PATH):
        os.remove(TEST_MEM_STORAGE_PATH)
