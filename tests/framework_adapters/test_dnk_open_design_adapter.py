# --- DNK-MRH-HEADER ---
# mrh_id: "tests/framework_adapters/test_dnk_open_design_adapter.py"
# purpose: "Comprehensive Unit Tests for OpenDesignAdapter, Canvas Node AST and Mutation Engine"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-OPEN-DESIGN-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-01"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""Unit tests for DNK Open Design Adapter."""

import pytest
from adapters.dnk_open_design_adapter import (
    OpenDesignAdapter,
    CanvasNode,
    CanvasNodeType,
    CanvasBounds,
    CanvasStyle,
    CanvasMutation,
    MutationType,
)


class TestOpenDesignAdapter:
    """Test suite for OpenDesignAdapter."""

    def test_init_and_session_creation(self) -> None:
        adapter = OpenDesignAdapter(workspace_id="ws-test-001")
        assert adapter.workspace_id == "ws-test-001"

        session = adapter.create_session("ds_123")
        assert session.session_id == "ds_123"
        assert session.workspace_id == "ws-test-001"
        assert "colors" in session.design_tokens

        retrieved = adapter.get_session("ds_123")
        assert retrieved is not None
        assert retrieved.session_id == "ds_123"

    def test_node_serialization_roundtrip(self) -> None:
        adapter = OpenDesignAdapter()
        node = CanvasNode(
            id="node_1",
            type=CanvasNodeType.RECTANGLE,
            name="Main Card",
            bounds=CanvasBounds(x=10.0, y=20.0, width=300.0, height=200.0, rotation=0.0),
            style=CanvasStyle(fill="#1E293B", corner_radius=12.0, opacity=0.9),
            content=None,
        )

        serialized = node.to_dict()
        assert serialized["id"] == "node_1"
        assert serialized["type"] == "RECTANGLE"
        assert serialized["bounds"]["x"] == 10.0
        assert serialized["style"]["cornerRadius"] == 12.0

        deserialized = adapter.deserialize_node(serialized)
        assert deserialized.id == "node_1"
        assert deserialized.type == CanvasNodeType.RECTANGLE
        assert deserialized.bounds.width == 300.0
        assert deserialized.style.corner_radius == 12.0
        assert deserialized.style.opacity == 0.9

    def test_apply_create_and_delete_mutations(self) -> None:
        adapter = OpenDesignAdapter()
        root_nodes = []

        create_mut = CanvasMutation(
            type=MutationType.CREATE_NODE,
            payload={
                "node": {
                    "id": "frame_1",
                    "type": "FRAME",
                    "name": "App Header",
                    "bounds": {"x": 0, "y": 0, "width": 800, "height": 64},
                    "style": {"fill": "#0F172A"},
                }
            },
        )

        roots_after_create = adapter.apply_mutations(root_nodes, [create_mut])
        assert len(roots_after_create) == 1
        assert roots_after_create[0].id == "frame_1"
        assert roots_after_create[0].name == "App Header"

        # Apply update style
        update_style_mut = CanvasMutation(
            type=MutationType.UPDATE_STYLE,
            target_node_id="frame_1",
            payload={"fill": "#1E293B", "cornerRadius": 8.0},
        )
        roots_after_style = adapter.apply_mutations(roots_after_create, [update_style_mut])
        assert roots_after_style[0].style.fill == "#1E293B"
        assert roots_after_style[0].style.corner_radius == 8.0

        # Apply delete
        delete_mut = CanvasMutation(
            type=MutationType.DELETE_NODE,
            target_node_id="frame_1",
        )
        roots_after_delete = adapter.apply_mutations(roots_after_style, [delete_mut])
        assert len(roots_after_delete) == 0

    def test_generate_ui_component_mutations(self) -> None:
        adapter = OpenDesignAdapter()

        # Button component
        btn_mutations = adapter.generate_ui_component_mutations(
            component_type="button",
            name="Subscribe Now",
            x=50.0,
            y=100.0,
        )
        assert len(btn_mutations) == 2
        assert btn_mutations[0].type == MutationType.CREATE_NODE
        assert btn_mutations[1].parent_node_id is not None

        roots = adapter.apply_mutations([], btn_mutations)
        assert len(roots) == 1
        assert len(roots[0].children) == 1
        assert roots[0].children[0].content == "Subscribe Now"

        # Card component
        card_mutations = adapter.generate_ui_component_mutations(
            component_type="card",
            name="AI Analytics",
            x=0.0,
            y=0.0,
        )
        assert len(card_mutations) == 3
        roots = adapter.apply_mutations([], card_mutations)
        assert len(roots) == 1
        assert len(roots[0].children) == 2

    def test_export_to_svg_and_html(self) -> None:
        adapter = OpenDesignAdapter()
        card_node = CanvasNode(
            id="card_export",
            type=CanvasNodeType.FRAME,
            name="Promo Card",
            bounds=CanvasBounds(x=0.0, y=0.0, width=400.0, height=200.0),
            style=CanvasStyle(fill="#1E293B", corner_radius=8.0),
            children=[
                CanvasNode(
                    id="txt_export",
                    type=CanvasNodeType.TEXT,
                    name="Heading",
                    bounds=CanvasBounds(x=20.0, y=20.0, width=360.0, height=30.0),
                    style=CanvasStyle(font_size=18.0, text_color="#FFFFFF"),
                    content="Hello Open Design",
                )
            ],
        )

        svg = adapter.export_to_svg(card_node)
        assert "<rect" in svg
        assert "Hello Open Design" in svg
        assert 'width="400.0"' in svg

        html_bundle = adapter.export_to_html_css(card_node)
        assert "node-card_export" in html_bundle["html"]
        assert "Hello Open Design" in html_bundle["html"]
        assert "background-color: #1E293B" in html_bundle["css"]
