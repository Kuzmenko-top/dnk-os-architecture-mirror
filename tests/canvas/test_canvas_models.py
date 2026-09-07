# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-CANVAS-002-TEST-MODELS"
# purpose: "Unit tests for Canvas & Generative UI 2.0 ORM Models (DNK-CANVAS-002 Phase 1)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone

from apps.api.db.models.canvas import CanvasModel
from apps.api.db.models.canvas_node import CanvasNodeModel
from apps.api.db.models.canvas_edge import CanvasEdgeModel
from apps.api.db.models.canvas_component import CanvasComponentModel
from apps.api.db.models.canvas_session import CanvasSessionModel
from apps.api.db.models.canvas_collaborator import CanvasCollaboratorModel


def test_canvas_model_instantiation_and_serialization():
    canvas = CanvasModel(
        id="canvas_01_test",
        workspace_id="ws_main_001",
        name="Main Product Flow Canvas",
        description="Infinite canvas for customer journeys and generative UI",
        viewport_x=150.0,
        viewport_y=-200.5,
        zoom=1.25,
        grid_size=24,
        snap_to_grid=1,
        background_color="#18181b",
        version=1,
        status="active",
        created_by="user_max_001",
        metadata_payload={"tags": ["generative-ui", "flow-v2"]}
    )

    d = canvas.to_dict()
    assert d["id"] == "canvas_01_test"
    assert d["workspace_id"] == "ws_main_001"
    assert d["name"] == "Main Product Flow Canvas"
    assert d["viewport_x"] == 150.0
    assert d["viewport_y"] == -200.5
    assert d["zoom"] == 1.25
    assert d["grid_size"] == 24
    assert d["snap_to_grid"] is True
    assert d["background_color"] == "#18181b"
    assert d["version"] == 1
    assert d["status"] == "active"
    assert d["created_by"] == "user_max_001"
    assert d["metadata"]["tags"] == ["generative-ui", "flow-v2"]


def test_canvas_node_model_instantiation_and_serialization():
    node = CanvasNodeModel(
        id="node_comp_01",
        canvas_id="canvas_01_test",
        node_type="component",
        title="Hero Banner Component",
        pos_x=320.0,
        pos_y=450.0,
        width=400.0,
        height=220.0,
        z_index=2,
        is_locked=0,
        parent_node_id=None,
        component_id="comp_hero_01",
        data_payload={"headline": "Future of AI Commerce", "cta": "Get Started"},
        style_payload={"borderRadius": "12px", "shadow": "xl"}
    )

    d = node.to_dict()
    assert d["id"] == "node_comp_01"
    assert d["canvas_id"] == "canvas_01_test"
    assert d["node_type"] == "component"
    assert d["title"] == "Hero Banner Component"
    assert d["position"] == {"x": 320.0, "y": 450.0}
    assert d["dimensions"] == {"width": 400.0, "height": 220.0}
    assert d["z_index"] == 2
    assert d["is_locked"] is False
    assert d["component_id"] == "comp_hero_01"
    assert d["data"]["headline"] == "Future of AI Commerce"
    assert d["style"]["shadow"] == "xl"


def test_canvas_edge_model_instantiation_and_serialization():
    edge = CanvasEdgeModel(
        id="edge_01_conn",
        canvas_id="canvas_01_test",
        source_node_id="node_agent_supervisor",
        target_node_id="node_worker_ui",
        source_port="out_dispatch",
        target_port="in_receive",
        edge_type="smart_bezier",
        label="Task Payload Flow",
        condition_expression="event.type == 'UI_GEN_TRIGGER'",
        data_payload={"priority": "high"},
        style_payload={"stroke": "#6366f1", "strokeWidth": 2}
    )

    d = edge.to_dict()
    assert d["id"] == "edge_01_conn"
    assert d["canvas_id"] == "canvas_01_test"
    assert d["source_node_id"] == "node_agent_supervisor"
    assert d["target_node_id"] == "node_worker_ui"
    assert d["source_port"] == "out_dispatch"
    assert d["target_port"] == "in_receive"
    assert d["edge_type"] == "smart_bezier"
    assert d["label"] == "Task Payload Flow"
    assert d["condition_expression"] == "event.type == 'UI_GEN_TRIGGER'"
    assert d["data"]["priority"] == "high"


def test_canvas_component_model_instantiation_and_serialization():
    comp = CanvasComponentModel(
        id="comp_hero_01",
        workspace_id="ws_main_001",
        name="InteractiveProductCard",
        framework="react",
        category="ecommerce",
        source_code="export default function ProductCard({ title, price }) { return <div>{title} - ${price}</div>; }",
        props_schema={"title": "string", "price": "number"},
        default_props={"title": "Smart Watch Ultra", "price": 499},
        preview_image_url="https://assets.dnk-e.com/previews/card-01.png",
        is_generative=1,
        ai_prompt="Create a high-converting glassmorphic product card with instant purchase button",
        version=1,
        status="published",
        created_by="user_max_001"
    )

    d = comp.to_dict()
    assert d["id"] == "comp_hero_01"
    assert d["name"] == "InteractiveProductCard"
    assert d["framework"] == "react"
    assert d["category"] == "ecommerce"
    assert "export default function" in d["source_code"]
    assert d["props_schema"]["price"] == "number"
    assert d["default_props"]["price"] == 499
    assert d["is_generative"] is True
    assert d["status"] == "published"


def test_canvas_session_model_instantiation_and_serialization():
    session = CanvasSessionModel(
        id="session_live_01",
        canvas_id="canvas_01_test",
        workspace_id="ws_main_001",
        active_peers_count=3,
        current_version=14,
        state_snapshot={"nodesCount": 25, "edgesCount": 18},
        active_locks=[{"node_id": "node_comp_01", "user_id": "user_max_001"}],
        status="active"
    )

    d = session.to_dict()
    assert d["id"] == "session_live_01"
    assert d["canvas_id"] == "canvas_01_test"
    assert d["workspace_id"] == "ws_main_001"
    assert d["active_peers_count"] == 3
    assert d["current_version"] == 14
    assert d["state_snapshot"]["nodesCount"] == 25
    assert len(d["active_locks"]) == 1
    assert d["active_locks"][0]["node_id"] == "node_comp_01"


def test_canvas_collaborator_model_instantiation_and_serialization():
    collaborator = CanvasCollaboratorModel(
        id="collab_01",
        session_id="session_live_01",
        canvas_id="canvas_01_test",
        user_id="user_max_001",
        user_name="Maxim Kuzmenko",
        role="editor",
        color="#ec4899",
        cursor_x=540.5,
        cursor_y=810.2,
        selected_node_ids=["node_comp_01", "node_comp_02"],
        client_metadata={"browser": "Chrome", "screen": "Retina 4K"}
    )

    d = collaborator.to_dict()
    assert d["id"] == "collab_01"
    assert d["session_id"] == "session_live_01"
    assert d["canvas_id"] == "canvas_01_test"
    assert d["user_id"] == "user_max_001"
    assert d["user_name"] == "Maxim Kuzmenko"
    assert d["role"] == "editor"
    assert d["color"] == "#ec4899"
    assert d["cursor"] == {"x": 540.5, "y": 810.2}
    assert d["selected_node_ids"] == ["node_comp_01", "node_comp_02"]
    assert d["client_metadata"]["browser"] == "Chrome"
