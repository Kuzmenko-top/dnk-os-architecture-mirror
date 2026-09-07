# --- DNK-MRH-HEADER ---
# mrh_id: "adapters/dnk_open_design_adapter.py"
# purpose: "Hexagonal bidirectional adapter bridging nexu-io/open-design Canvas AST with Gerych Core Swarm and SCONES Memory"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-OPEN-DESIGN-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-01"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
DNK Open Design Adapter for Gerych Core & Canvas AI Orchestration.

Provides bidirectional synchronization between Open Design visual nodes (AST),
atomic mutations, vector layout generation, and Gerych AI Swarm execution.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union
import uuid

logger = logging.getLogger("DNKOpenDesignAdapter")


class CanvasNodeType(str, Enum):
    FRAME = "FRAME"
    GROUP = "GROUP"
    RECTANGLE = "RECTANGLE"
    TEXT = "TEXT"
    VECTOR = "VECTOR"
    IMAGE = "IMAGE"
    COMPONENT = "COMPONENT"


class MutationType(str, Enum):
    CREATE_NODE = "CREATE_NODE"
    UPDATE_NODE = "UPDATE_NODE"
    UPDATE_STYLE = "UPDATE_STYLE"
    TRANSFORM = "TRANSFORM"
    DELETE_NODE = "DELETE_NODE"
    BATCH = "BATCH"


@dataclass
class CanvasBounds:
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 100.0
    rotation: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation,
        }


@dataclass
class CanvasStyle:
    fill: Optional[str] = "#FFFFFF"
    stroke: Optional[str] = None
    stroke_width: float = 0.0
    opacity: float = 1.0
    corner_radius: float = 0.0
    font_family: Optional[str] = "Inter"
    font_size: Optional[float] = 16.0
    font_weight: Optional[str] = "400"
    text_color: Optional[str] = "#000000"
    box_shadow: Optional[str] = None
    custom_css: Optional[Dict[str, str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fill": self.fill,
            "stroke": self.stroke,
            "strokeWidth": self.stroke_width,
            "opacity": self.opacity,
            "cornerRadius": self.corner_radius,
            "fontFamily": self.font_family,
            "fontSize": self.font_size,
            "fontWeight": self.font_weight,
            "textColor": self.text_color,
            "boxShadow": self.box_shadow,
            "customCss": self.custom_css or {},
        }


@dataclass
class CanvasNode:
    id: str = field(default_factory=lambda: f"node_{uuid.uuid4().hex[:8]}")
    type: CanvasNodeType = CanvasNodeType.FRAME
    name: str = "Untitled Node"
    bounds: CanvasBounds = field(default_factory=CanvasBounds)
    style: CanvasStyle = field(default_factory=CanvasStyle)
    content: Optional[str] = None
    children: List["CanvasNode"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, CanvasNodeType) else str(self.type),
            "name": self.name,
            "bounds": self.bounds.to_dict() if hasattr(self.bounds, "to_dict") else asdict(self.bounds),
            "style": self.style.to_dict() if hasattr(self.style, "to_dict") else asdict(self.style),
            "content": self.content,
            "children": [child.to_dict() for child in self.children],
            "metadata": self.metadata,
        }


@dataclass
class CanvasMutation:
    mutation_id: str = field(default_factory=lambda: f"mut_{uuid.uuid4().hex[:8]}")
    type: MutationType = MutationType.UPDATE_NODE
    target_node_id: Optional[str] = None
    parent_node_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mutationId": self.mutation_id,
            "type": self.type.value if isinstance(self.type, MutationType) else str(self.type),
            "targetNodeId": self.target_node_id,
            "parentNodeId": self.parent_node_id,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


@dataclass
class DesignSession:
    session_id: str = field(default_factory=lambda: f"ds_{uuid.uuid4().hex[:8]}")
    workspace_id: str = "ws-alpha-001"
    active_selection: List[str] = field(default_factory=list)
    root_nodes: List[CanvasNode] = field(default_factory=list)
    design_tokens: Dict[str, Any] = field(default_factory=dict)
    history: List[CanvasMutation] = field(default_factory=list)


class OpenDesignAdapter:
    """
    Bidirectional bridge connecting Open Design visual canvas with Gerych Core.
    """

    def __init__(
        self,
        workspace_id: str = "ws-alpha-001",
        memory_engine: Optional[Any] = None,
        swarm_router: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
    ) -> None:
        self.workspace_id = workspace_id
        self.memory_engine = memory_engine
        self.swarm_router = swarm_router
        self._sessions: Dict[str, DesignSession] = {}

    def create_session(
        self,
        session_id: Optional[str] = None,
        design_tokens: Optional[Dict[str, Any]] = None
    ) -> DesignSession:
        sid = session_id or f"ds_{uuid.uuid4().hex[:8]}"
        session = DesignSession(
            session_id=sid,
            workspace_id=self.workspace_id,
            design_tokens=design_tokens or {
                "colors": {
                    "primary": "#3B82F6",
                    "surface": "#1E293B",
                    "text": "#F8FAFC",
                    "accent": "#10B981",
                },
                "spacing": {"sm": 8, "md": 16, "lg": 24},
                "radii": {"sm": 4, "md": 8, "lg": 16},
            },
        )
        self._sessions[sid] = session
        return session

    def get_session(self, session_id: str) -> Optional[DesignSession]:
        return self._sessions.get(session_id)

    def deserialize_node(self, data: Dict[str, Any]) -> CanvasNode:
        bounds_data = data.get("bounds", {})
        bounds = CanvasBounds(
            x=float(bounds_data.get("x", 0.0)),
            y=float(bounds_data.get("y", 0.0)),
            width=float(bounds_data.get("width", 100.0)),
            height=float(bounds_data.get("height", 100.0)),
            rotation=float(bounds_data.get("rotation", 0.0)),
        )

        style_data = data.get("style", {})
        style = CanvasStyle(
            fill=style_data.get("fill", "#FFFFFF"),
            stroke=style_data.get("stroke"),
            stroke_width=float(style_data.get("strokeWidth", style_data.get("stroke_width", 0.0))),
            opacity=float(style_data.get("opacity", 1.0)),
            corner_radius=float(style_data.get("cornerRadius", style_data.get("corner_radius", 0.0))),
            font_family=style_data.get("fontFamily", style_data.get("font_family", "Inter")),
            font_size=float(style_data.get("fontSize", style_data.get("font_size", 16.0))),
            font_weight=str(style_data.get("fontWeight", style_data.get("font_weight", "400"))),
            text_color=style_data.get("textColor", style_data.get("text_color", "#000000")),
            box_shadow=style_data.get("boxShadow", style_data.get("box_shadow")),
            custom_css=style_data.get("customCss", style_data.get("custom_css", {})),
        )

        node_type_str = data.get("type", "FRAME")
        try:
            node_type = CanvasNodeType(node_type_str)
        except ValueError:
            node_type = CanvasNodeType.FRAME

        children = [self.deserialize_node(child) for child in data.get("children", [])]

        return CanvasNode(
            id=data.get("id", f"node_{uuid.uuid4().hex[:8]}"),
            type=node_type,
            name=data.get("name", "Untitled Node"),
            bounds=bounds,
            style=style,
            content=data.get("content"),
            children=children,
            metadata=data.get("metadata", {}),
        )

    def serialize_nodes(self, nodes: List[CanvasNode]) -> List[Dict[str, Any]]:
        return [node.to_dict() for node in nodes]

    def apply_mutations(
        self,
        root_nodes: List[CanvasNode],
        mutations: List[CanvasMutation]
    ) -> List[CanvasNode]:
        node_map: Dict[str, CanvasNode] = {}
        parent_map: Dict[str, str] = {}

        def index_tree(node: CanvasNode, parent_id: Optional[str] = None):
            node_map[node.id] = node
            if parent_id:
                parent_map[node.id] = parent_id
            for child in node.children:
                index_tree(child, node.id)

        for r in root_nodes:
            index_tree(r)

        result_roots = list(root_nodes)

        for mut in mutations:
            if mut.type == MutationType.CREATE_NODE:
                node_data = mut.payload.get("node", {})
                new_node = self.deserialize_node(node_data) if isinstance(node_data, dict) else node_data
                node_map[new_node.id] = new_node
                if mut.parent_node_id and mut.parent_node_id in node_map:
                    parent = node_map[mut.parent_node_id]
                    parent.children.append(new_node)
                    parent_map[new_node.id] = parent.id
                else:
                    result_roots.append(new_node)

            elif mut.type == MutationType.UPDATE_STYLE:
                if mut.target_node_id and mut.target_node_id in node_map:
                    target = node_map[mut.target_node_id]
                    for k, v in mut.payload.items():
                        if hasattr(target.style, k):
                            setattr(target.style, k, v)
                        elif k in ("fill", "stroke", "opacity", "cornerRadius"):
                            if k == "cornerRadius":
                                target.style.corner_radius = float(v)
                            else:
                                setattr(target.style, k, v)

            elif mut.type == MutationType.TRANSFORM:
                if mut.target_node_id and mut.target_node_id in node_map:
                    target = node_map[mut.target_node_id]
                    for attr in ("x", "y", "width", "height", "rotation"):
                        if attr in mut.payload:
                            setattr(target.bounds, attr, float(mut.payload[attr]))

            elif mut.type == MutationType.UPDATE_NODE:
                if mut.target_node_id and mut.target_node_id in node_map:
                    target = node_map[mut.target_node_id]
                    if "name" in mut.payload:
                        target.name = mut.payload["name"]
                    if "content" in mut.payload:
                        target.content = mut.payload["content"]
                    if "metadata" in mut.payload and isinstance(mut.payload["metadata"], dict):
                        target.metadata.update(mut.payload["metadata"])

            elif mut.type == MutationType.DELETE_NODE:
                if mut.target_node_id and mut.target_node_id in node_map:
                    del_id = mut.target_node_id
                    if del_id in parent_map:
                        p_node = node_map.get(parent_map[del_id])
                        if p_node:
                            p_node.children = [c for c in p_node.children if c.id != del_id]
                    else:
                        result_roots = [r for r in result_roots if r.id != del_id]

        return result_roots

    def generate_ui_component_mutations(
        self,
        component_type: str,
        name: str,
        x: float = 0.0,
        y: float = 0.0,
        design_tokens: Optional[Dict[str, Any]] = None
    ) -> List[CanvasMutation]:
        """
        Generate atomic mutations for common UI components (cards, buttons, banners, headers).
        """
        tokens = design_tokens or {
            "colors": {"primary": "#3B82F6", "surface": "#1E293B", "text": "#F8FAFC", "accent": "#10B981"},
            "radii": {"md": 8, "lg": 16},
        }
        mutations: List[CanvasMutation] = []

        if component_type.lower() in ("button", "cta"):
            btn_id = f"btn_{uuid.uuid4().hex[:6]}"
            text_id = f"txt_{uuid.uuid4().hex[:6]}"

            btn_node = CanvasNode(
                id=btn_id,
                type=CanvasNodeType.FRAME,
                name=f"Button / {name}",
                bounds=CanvasBounds(x=x, y=y, width=160.0, height=48.0),
                style=CanvasStyle(
                    fill=tokens["colors"].get("primary", "#3B82F6"),
                    corner_radius=float(tokens["radii"].get("md", 8)),
                ),
            )

            text_node = CanvasNode(
                id=text_id,
                type=CanvasNodeType.TEXT,
                name="Button Text",
                bounds=CanvasBounds(x=20.0, y=14.0, width=120.0, height=20.0),
                style=CanvasStyle(
                    font_size=16.0,
                    font_weight="600",
                    text_color="#FFFFFF",
                ),
                content=name,
            )

            mutations.append(CanvasMutation(
                type=MutationType.CREATE_NODE,
                payload={"node": btn_node.to_dict()}
            ))
            mutations.append(CanvasMutation(
                type=MutationType.CREATE_NODE,
                parent_node_id=btn_id,
                payload={"node": text_node.to_dict()}
            ))

        elif component_type.lower() in ("card", "hero_card", "feature_card"):
            card_id = f"card_{uuid.uuid4().hex[:6]}"
            title_id = f"title_{uuid.uuid4().hex[:6]}"
            body_id = f"body_{uuid.uuid4().hex[:6]}"

            card_node = CanvasNode(
                id=card_id,
                type=CanvasNodeType.FRAME,
                name=f"Card / {name}",
                bounds=CanvasBounds(x=x, y=y, width=320.0, height=200.0),
                style=CanvasStyle(
                    fill=tokens["colors"].get("surface", "#1E293B"),
                    corner_radius=float(tokens["radii"].get("lg", 16)),
                    stroke="#334155",
                    stroke_width=1.0,
                ),
            )

            title_node = CanvasNode(
                id=title_id,
                type=CanvasNodeType.TEXT,
                name="Card Title",
                bounds=CanvasBounds(x=20.0, y=20.0, width=280.0, height=28.0),
                style=CanvasStyle(
                    font_size=20.0,
                    font_weight="700",
                    text_color=tokens["colors"].get("text", "#F8FAFC"),
                ),
                content=name,
            )

            body_node = CanvasNode(
                id=body_id,
                type=CanvasNodeType.TEXT,
                name="Card Description",
                bounds=CanvasBounds(x=20.0, y=56.0, width=280.0, height=60.0),
                style=CanvasStyle(
                    font_size=14.0,
                    font_weight="400",
                    text_color="#94A3B8",
                ),
                content="Generative UI component synthesized by Gerych Swarm.",
            )

            mutations.append(CanvasMutation(
                type=MutationType.CREATE_NODE,
                payload={"node": card_node.to_dict()}
            ))
            mutations.append(CanvasMutation(
                type=MutationType.CREATE_NODE,
                parent_node_id=card_id,
                payload={"node": title_node.to_dict()}
            ))
            mutations.append(CanvasMutation(
                type=MutationType.CREATE_NODE,
                parent_node_id=card_id,
                payload={"node": body_node.to_dict()}
            ))

        return mutations

    def export_to_svg(self, node: CanvasNode) -> str:
        """
        Recursively compile Canvas Node AST into clean SVG format.
        """
        b = node.bounds
        s = node.style

        if node.type == CanvasNodeType.TEXT:
            escaped_content = (node.content or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            return (
                f'<text x="{b.x}" y="{b.y + (s.font_size or 16)}" '
                f'font-family="{s.font_family or "Inter"}" font-size="{s.font_size or 16}" '
                f'font-weight="{s.font_weight or "400"}" fill="{s.text_color or "#000000"}" '
                f'opacity="{s.opacity}">{escaped_content}</text>'
            )

        # Container / Frame / Rectangle
        fill_attr = f'fill="{s.fill}"' if s.fill else 'fill="none"'
        stroke_attr = f'stroke="{s.stroke}" stroke-width="{s.stroke_width}"' if s.stroke and s.stroke_width > 0 else ''
        rx_attr = f'rx="{s.corner_radius}"' if s.corner_radius > 0 else ''

        children_svg = "\n  ".join(self.export_to_svg(c) for c in node.children)
        rect_tag = f'<rect x="{b.x}" y="{b.y}" width="{b.width}" height="{b.height}" {rx_attr} {fill_attr} {stroke_attr} opacity="{s.opacity}"/>'

        if children_svg:
            return f'<g id="{node.id}">\n  {rect_tag}\n  {children_svg}\n</g>'
        return rect_tag

    def export_to_html_css(self, node: CanvasNode) -> Dict[str, str]:
        """
        Compile Canvas Node AST into responsive HTML & CSS markup.
        """
        b = node.bounds
        s = node.style

        css_classes: List[str] = []
        css_rules: List[str] = []

        class_name = f"node-{node.id}"
        css_rules.append(f".{class_name} {{")
        css_rules.append(f"  position: relative;")
        css_rules.append(f"  width: {b.width}px;")
        css_rules.append(f"  min-height: {b.height}px;")
        if s.fill:
            css_rules.append(f"  background-color: {s.fill};")
        if s.corner_radius > 0:
            css_rules.append(f"  border-radius: {s.corner_radius}px;")
        if s.stroke and s.stroke_width > 0:
            css_rules.append(f"  border: {s.stroke_width}px solid {s.stroke};")
        if s.opacity < 1.0:
            css_rules.append(f"  opacity: {s.opacity};")
        css_rules.append("}")

        if node.type == CanvasNodeType.TEXT:
            html = f'<p class="{class_name}" style="color: {s.text_color}; font-size: {s.font_size}px; font-weight: {s.font_weight};">{node.content or ""}</p>'
        else:
            inner_html = "\n".join(self.export_to_html_css(c)["html"] for c in node.children)
            html = f'<div class="{class_name}">\n{inner_html}\n</div>'

        return {
            "html": html,
            "css": "\n".join(css_rules),
        }
