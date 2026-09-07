# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-CANVAS-002-TEST-GENUI-SANDBOX"
# purpose: "Unit tests for Generative UI Engine and Component Sandbox (DNK-CANVAS-002 Phase 3)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.canvas_generative_ui_engine import (
    CanvasGenerativeUIEngine,
    GeneratedComponent
)
from apps.api.services.canvas_component_sandbox import (
    CanvasComponentSandbox,
    ComponentLifecycleState,
    SandboxSecurityConfig
)


def test_generative_ui_synthesis_templates():
    # Test KPI card prompt synthesis
    kpi_comp = CanvasGenerativeUIEngine.synthesize_component_from_prompt("Generate real-time analytics KPI card")
    assert isinstance(kpi_comp, GeneratedComponent)
    assert kpi_comp.category == "analytics"
    assert "KPICard" in kpi_comp.name
    assert "title" in kpi_comp.props_schema["properties"]
    assert "value" in kpi_comp.props_schema["properties"]

    # Test E-commerce product card prompt
    ecom_comp = CanvasGenerativeUIEngine.synthesize_component_from_prompt("E-commerce cart checkout product card")
    assert ecom_comp.category == "ecommerce"
    assert "ProductCard" in ecom_comp.name
    ecom_dict = ecom_comp.to_dict()
    assert "price" in ecom_dict["props_schema"]["properties"]

    # Test Chat bubble prompt
    chat_comp = CanvasGenerativeUIEngine.synthesize_component_from_prompt("Agent chat bubble message container")
    assert chat_comp.category == "ai_assistant"
    assert "AgentBubble" in chat_comp.name

    # Test generic fallback prompt
    generic_comp = CanvasGenerativeUIEngine.synthesize_component_from_prompt("Custom 3D volume slider")
    assert generic_comp.category == "general"
    assert "Custom 3D volume slider" in generic_comp.default_props["title"]


def test_props_schema_validation():
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "count": {"type": "number"},
            "active": {"type": "boolean"},
            "status": {"type": "string", "enum": ["open", "closed"]}
        },
        "required": ["title", "count"]
    }

    # Valid props
    valid, errors = CanvasGenerativeUIEngine.validate_props(
        {"title": "Card", "count": 10, "active": True, "status": "open"},
        schema
    )
    assert valid is True
    assert len(errors) == 0

    # Missing required
    valid_missing, errors_missing = CanvasGenerativeUIEngine.validate_props(
        {"count": 5},
        schema
    )
    assert valid_missing is False
    assert any("Missing required prop 'title'" in e for e in errors_missing)

    # Invalid types and enum
    valid_type, errors_type = CanvasGenerativeUIEngine.validate_props(
        {"title": 123, "count": "not_a_number", "active": "yes", "status": "unknown"},
        schema
    )
    assert valid_type is False
    assert len(errors_type) >= 3


def test_auto_layout_and_smart_connectors():
    nodes = [
        {"id": "sup_1", "node_type": "supervisor", "position": {"x": 0, "y": 0}},
        {"id": "ag_1", "node_type": "agent", "position": {"x": 0, "y": 0}},
        {"id": "comp_1", "node_type": "component", "position": {"x": 0, "y": 0}},
        {"id": "comp_2", "node_type": "component", "position": {"x": 0, "y": 0}}
    ]

    # Horizontal flow layout
    h_nodes = CanvasGenerativeUIEngine.suggest_auto_layout(nodes, layout_type="horizontal_flow", spacing_x=200, start_x=50)
    assert h_nodes[0]["position"]["x"] == 50
    assert h_nodes[1]["position"]["x"] == 250
    assert h_nodes[2]["position"]["x"] == 450

    # Grid 2 col layout
    g_nodes = CanvasGenerativeUIEngine.suggest_auto_layout(nodes, layout_type="grid_2col", spacing_x=300, spacing_y=150, start_x=0, start_y=0)
    assert g_nodes[0]["position"] == {"x": 0, "y": 0}
    assert g_nodes[1]["position"] == {"x": 300, "y": 0}
    assert g_nodes[2]["position"] == {"x": 0, "y": 150}
    assert g_nodes[3]["position"] == {"x": 300, "y": 150}

    # Smart connectors inference
    edges = CanvasGenerativeUIEngine.infer_smart_connectors(nodes)
    assert len(edges) >= 3
    # Check supervisor -> agent edge
    assert any(e["source_node_id"] == "sup_1" and e["target_node_id"] == "ag_1" for e in edges)
    # Check agent -> components edges
    assert any(e["source_node_id"] == "ag_1" and e["target_node_id"] == "comp_1" for e in edges)
    assert any(e["source_node_id"] == "ag_1" and e["target_node_id"] == "comp_2" for e in edges)


def test_canvas_component_sandbox_lifecycle_and_messaging():
    sandbox = CanvasComponentSandbox()

    # Generate iframe envelope
    envelope = sandbox.generate_iframe_envelope(
        component_code="function Card() { return <div>Test</div> }",
        props={"metric": "99.9%"},
        instance_id="inst_test_1"
    )
    assert "<!DOCTYPE html>" in envelope
    assert "Content-Security-Policy" in envelope
    assert "inst_test_1" in envelope

    # Generate shadow DOM descriptor
    shadow_desc = sandbox.generate_shadow_dom_descriptor(
        component_name="UserCard",
        css_scoped=":host { display: block; }",
        html_template="<div class='card'>Hello</div>"
    )
    assert shadow_desc["tag_name"] == "dnk-usercard"
    assert shadow_desc["mode"] == "open"

    # Lifecycle tracking
    events = []
    sandbox.register_listener("lifecycle", lambda data: events.append(data))

    inst = sandbox.mount_component(
        instance_id="inst_1",
        component_id="comp_100",
        node_id="node_50",
        initial_props={"count": 1}
    )
    assert inst.state == ComponentLifecycleState.MOUNTED
    assert inst.props["count"] == 1
    assert len(events) == 1
    assert events[0]["action"] == "mount"

    # Update props
    updated = sandbox.update_props("inst_1", {"count": 2, "label": "Updated"})
    assert updated is not None
    assert updated.props["count"] == 2
    assert updated.props["label"] == "Updated"
    assert len(events) == 2

    # Messaging
    received_msgs = []
    sandbox.register_listener("message:node_worker", lambda msg: received_msgs.append(msg))

    msg = sandbox.send_message(
        sender_id="node_supervisor",
        target_id="node_worker",
        action="EXECUTE_TASK",
        payload={"task": "render_chart"}
    )
    assert msg["sender_id"] == "node_supervisor"
    assert len(received_msgs) == 1
    assert received_msgs[0]["action"] == "EXECUTE_TASK"

    # Unmount
    unmounted = sandbox.unmount_component("inst_1")
    assert unmounted is True
    assert "inst_1" not in sandbox.instances
    assert len(events) == 3
    assert events[2]["action"] == "unmount"
