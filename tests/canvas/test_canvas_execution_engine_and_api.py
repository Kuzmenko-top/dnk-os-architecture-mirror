# --- DNK-MRH-HEADER ---
# mrh_id: "tests_canvas_test_canvas_execution_engine_and_api"
# purpose: "Integration Tests for Canvas Execution Engine, Step Runner, and Workflow REST API (DNK-CANVAS-001 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.schemas.workflow_dag_schemas import (
    WorkflowDAG,
    WorkflowNode,
    WorkflowNodeType,
    WorkflowEdge,
    NodePosition,
    WorkflowExecuteRequest
)
from apps.api.services.canvas_execution_engine import CanvasExecutionEngine

client = TestClient(app)


@pytest.mark.asyncio
async def test_execution_engine_step_runner_direct():
    engine = CanvasExecutionEngine()

    n1 = WorkflowNode(
        id="step_trigger",
        type=WorkflowNodeType.EVENT_TRIGGER,
        label="Start Event",
        config={"stream_topic": "reburn.manufacturing"}
    )
    n2 = WorkflowNode(
        id="step_batch",
        type=WorkflowNodeType.BATCH_TASK,
        label="Batch Ingestion",
        config={"batch_job_type": "mesh_task_prep"}
    )
    n3 = WorkflowNode(
        id="step_agent",
        type=WorkflowNodeType.A2A_AGENT,
        label="A2A Agent Mesh",
        config={"agent_id": "gerych_builder", "task_prompt": "Synthesize CAD model"}
    )
    n4 = WorkflowNode(
        id="step_shopify",
        type=WorkflowNodeType.SHOPIFY_ACTION,
        label="Shopify Fulfillment",
        config={"action_type": "order_fulfillment_create", "shop_domain": "store.dnk-e.com"}
    )
    n5 = WorkflowNode(
        id="step_hardware",
        type=WorkflowNodeType.HARDWARE_ACTION,
        label="ReBurn Laser Activation",
        config={"device_id": "reburn_laser_01", "action_type": "gpio_write", "pin": 21}
    )

    edges = [
        WorkflowEdge(id="e1", source="step_trigger", target="step_batch"),
        WorkflowEdge(id="e2", source="step_batch", target="step_agent"),
        WorkflowEdge(id="e3", source="step_agent", target="step_shopify"),
        WorkflowEdge(id="e4", source="step_shopify", target="step_hardware"),
    ]

    dag = WorkflowDAG(
        id="wf_exec_test_01",
        name="End-to-End ReBurn Workflow",
        nodes=[n1, n2, n3, n4, n5],
        edges=edges
    )

    engine.save_workflow(dag)
    assert engine.get_workflow("wf_exec_test_01") is not None

    req = WorkflowExecuteRequest(
        initial_context={"sku": "REBURN-PRO-V1", "quantity": 5},
        trigger_event={"stream": "reburn.manufacturing", "order_id": 999}
    )

    summary = await engine.execute_workflow("wf_exec_test_01", req)

    assert summary.status == "COMPLETED"
    assert summary.total_nodes == 5
    assert summary.completed_nodes == 5
    assert summary.failed_nodes == 0
    assert "step_hardware" in summary.node_results
    assert summary.node_results["step_hardware"]["hardware_state"] == "ACK_CONFIRMED"


def test_canvas_workflow_rest_api_lifecycle():
    # 1. Create Workflow
    payload = {
        "id": "wf_rest_demo_01",
        "name": "Shopify to Hardware Sync",
        "workspace_id": "ws-alpha-001",
        "nodes": [
            {
                "id": "node_trig_rest",
                "type": "event_trigger",
                "label": "Webhook Trigger",
                "position": {"x": 0.0, "y": 0.0},
                "config": {"stream_topic": "shopify.orders"}
            },
            {
                "id": "node_hw_rest",
                "type": "hardware_action",
                "label": "Buzzer Alert",
                "position": {"x": 250.0, "y": 0.0},
                "config": {"device_id": "buzzer_1", "action_type": "gpio_write", "pin": 12}
            }
        ],
        "edges": [
            {
                "id": "edge_trig_to_hw",
                "source": "node_trig_rest",
                "target": "node_hw_rest"
            }
        ]
    }

    resp = client.post("/api/v1/canvas/workflows", json=payload)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["id"] == "wf_rest_demo_01"
    assert len(created["nodes"]) == 2

    # 2. Validate Endpoint
    val_resp = client.post("/api/v1/canvas/workflows/validate", json=payload)
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["valid"] is True
    assert val_data["topological_order"] == ["node_trig_rest", "node_hw_rest"]

    # 3. Get Workflow
    get_resp = client.get("/api/v1/canvas/workflows/wf_rest_demo_01")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Shopify to Hardware Sync"

    # 4. List Workflows
    list_resp = client.get("/api/v1/canvas/workflows?workspace_id=ws-alpha-001")
    assert list_resp.status_code == 200
    assert any(wf["id"] == "wf_rest_demo_01" for wf in list_resp.json())

    # 5. Execute Workflow
    exec_payload = {
        "initial_context": {"test_run": True},
        "trigger_event": {"event": "order_paid"}
    }
    exec_resp = client.post("/api/v1/canvas/workflows/wf_rest_demo_01/execute", json=exec_payload)
    assert exec_resp.status_code == 200
    exec_summary = exec_resp.json()
    assert exec_summary["status"] == "COMPLETED"
    assert exec_summary["completed_nodes"] == 2

    # 6. Delete Workflow
    del_resp = client.delete("/api/v1/canvas/workflows/wf_rest_demo_01")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

    # Verify not found after delete
    get_after_del = client.get("/api/v1/canvas/workflows/wf_rest_demo_01")
    assert get_after_del.status_code == 404
