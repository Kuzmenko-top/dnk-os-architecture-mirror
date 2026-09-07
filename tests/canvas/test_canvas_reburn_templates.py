# --- DNK-MRH-HEADER ---
# mrh_id: "tests_canvas_test_canvas_reburn_templates"
# purpose: "Unit and REST Integration Tests for Shopify & ReBurn Hardware Workflow Templates (DNK-CANVAS-001 Phase 4)"
# author: "DNK-e.com Maksym"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.schemas.workflow_dag_schemas import (
    WorkflowNodeType,
    NodeExecutionStatus
)
from apps.api.services.canvas_reburn_templates import (
    get_template_registry,
    CanvasTemplateRegistry
)
from apps.api.services.canvas_execution_engine import (
    get_canvas_execution_engine
)
from apps.api.routers.canvas_router import router as canvas_router


@pytest.fixture
def test_client():
    app = FastAPI(title="Canvas Test App")
    app.include_router(canvas_router)
    return TestClient(app)


def test_template_registry_initialization():
    registry = get_template_registry()
    templates = registry.list_templates()
    
    assert len(templates) >= 4
    template_ids = [t.template_id for t in templates]
    assert "template-shopify-fulfillment" in template_ids
    assert "template-shopify-inventory-sync" in template_ids
    assert "template-reburn-sensor-monitor" in template_ids
    assert "template-reburn-emergency-shutdown" in template_ids


def test_template_filtering_by_category():
    registry = get_template_registry()
    
    ecom_templates = registry.list_templates(category="e_commerce")
    assert len(ecom_templates) == 2
    for t in ecom_templates:
        assert t.category == "e_commerce"
        
    hw_templates = registry.list_templates(category="hardware")
    assert len(hw_templates) == 2
    for t in hw_templates:
        assert t.category == "hardware"


@pytest.mark.asyncio
async def test_template_dag_integrity_and_execution():
    registry = get_template_registry()
    engine = get_canvas_execution_engine()
    
    # 1. Shopify Fulfillment Template Execution
    shopify_dag = registry.get_template("template-shopify-fulfillment")
    assert shopify_dag is not None
    assert len(shopify_dag.nodes) == 3
    assert len(shopify_dag.edges) == 2
    
    engine.save_workflow(shopify_dag)
    exec_summary = await engine.execute_workflow(shopify_dag.id)
    assert exec_summary.status == "COMPLETED"
    assert exec_summary.failed_nodes == 0
    assert exec_summary.completed_nodes == 3
    assert "trig-order-created" in exec_summary.node_results
    assert "agent-order-audit" in exec_summary.node_results
    assert "act-create-fulfillment" in exec_summary.node_results

    # 2. ReBurn Emergency Shutdown Execution
    reburn_dag = registry.get_template("template-reburn-emergency-shutdown")
    assert reburn_dag is not None
    assert len(reburn_dag.nodes) == 3
    
    engine.save_workflow(reburn_dag)
    hw_summary = await engine.execute_workflow(reburn_dag.id)
    assert hw_summary.status == "COMPLETED"
    assert hw_summary.failed_nodes == 0
    assert hw_summary.completed_nodes == 3
    assert "hw-shutoff-valve" in hw_summary.node_results


def test_template_rest_api(test_client):
    # 1. List all templates
    resp = test_client.get("/api/v1/canvas/workflows/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4

    # 2. Filter by category
    resp_hw = test_client.get("/api/v1/canvas/workflows/templates?category=hardware")
    assert resp_hw.status_code == 200
    hw_data = resp_hw.json()
    assert len(hw_data) == 2
    assert all(item["category"] == "hardware" for item in hw_data)

    # 3. Get single template
    resp_detail = test_client.get("/api/v1/canvas/workflows/templates/template-shopify-fulfillment")
    assert resp_detail.status_code == 200
    dag_json = resp_detail.json()
    assert dag_json["id"] == "template-shopify-fulfillment"
    assert len(dag_json["nodes"]) == 3
    assert len(dag_json["edges"]) == 2

    # 4. Non-existent template
    resp_404 = test_client.get("/api/v1/canvas/workflows/templates/unknown-template-xyz")
    assert resp_404.status_code == 404
