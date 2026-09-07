# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canvas_generative_ui_engine"
# purpose: "Generative UI 2.0 Engine for LLM component synthesis, props schema generation, auto-layout, and smart connectors (DNK-CANVAS-002 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import re
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class GeneratedComponent:
    component_id: str
    name: str
    framework: str
    category: str
    source_code: str
    props_schema: Dict[str, Any]
    default_props: Dict[str, Any]
    ai_prompt: str
    preview_markup: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "name": self.name,
            "framework": self.framework,
            "category": self.category,
            "source_code": self.source_code,
            "props_schema": self.props_schema,
            "default_props": self.default_props,
            "ai_prompt": self.ai_prompt,
            "preview_markup": self.preview_markup
        }


class CanvasGenerativeUIEngine:
    """Generative UI 2.0 Engine providing template synthesis, schema validation, layout auto-suggestions, and smart connector resolution."""

    BUILTIN_TEMPLATES = {
        "kpi_card": {
            "name": "KPIMetricCard",
            "category": "analytics",
            "react_code": (
                "export default function KPIMetricCard({ title, value, change, trend = 'up' }) {\n"
                "  return (\n"
                "    <div className='p-4 rounded-xl bg-slate-900/80 border border-slate-700/50 backdrop-blur shadow-lg'>\n"
                "      <div className='text-xs font-semibold uppercase tracking-wider text-slate-400'>{title}</div>\n"
                "      <div className='text-2xl font-bold text-white mt-1'>{value}</div>\n"
                "      <div className={`text-xs mt-2 font-medium flex items-center ${trend === 'up' ? 'text-emerald-400' : 'text-rose-400'}`}>\n"
                "        {change}\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}"
            ),
            "props_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "value": {"type": "string"},
                    "change": {"type": "string"},
                    "trend": {"type": "string", "enum": ["up", "down", "neutral"]}
                },
                "required": ["title", "value"]
            },
            "default_props": {
                "title": "Real-time Conversion",
                "value": "4.82%",
                "change": "+14.2% vs last week",
                "trend": "up"
            }
        },
        "ecommerce_card": {
            "name": "EcomProductCard",
            "category": "ecommerce",
            "react_code": (
                "export default function EcomProductCard({ title, price, currency = '$', inStock = true, onBuy }) {\n"
                "  return (\n"
                "    <div className='w-full max-w-sm rounded-2xl bg-zinc-900 border border-zinc-800 p-5 shadow-xl text-white'>\n"
                "      <div className='text-lg font-bold'>{title}</div>\n"
                "      <div className='text-xl font-extrabold text-indigo-400 mt-2'>{currency}{price}</div>\n"
                "      <div className='mt-4 flex gap-2'>\n"
                "        <button disabled={!inStock} onClick={onBuy} className='w-full py-2 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-sm transition'>\n"
                "          {inStock ? 'Instant Checkout' : 'Out of Stock'}\n"
                "        </button>\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}"
            ),
            "props_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "price": {"type": "number"},
                    "currency": {"type": "string"},
                    "inStock": {"type": "boolean"}
                },
                "required": ["title", "price"]
            },
            "default_props": {
                "title": "Quantum ANC Headphones",
                "price": 299,
                "currency": "$",
                "inStock": True
            }
        },
        "chat_bubble": {
            "name": "AgentChatBubble",
            "category": "ai_assistant",
            "react_code": (
                "export default function AgentChatBubble({ agentName, message, timestamp, role = 'agent' }) {\n"
                "  return (\n"
                "    <div className={`flex gap-3 p-3 rounded-xl ${role === 'agent' ? 'bg-indigo-950/40 border border-indigo-800/40' : 'bg-zinc-800'}`}>\n"
                "      <div className='font-bold text-xs text-indigo-300'>{agentName}</div>\n"
                "      <div className='text-sm text-zinc-200'>{message}</div>\n"
                "    </div>\n"
                "  );\n"
                "}"
            ),
            "props_schema": {
                "type": "object",
                "properties": {
                    "agentName": {"type": "string"},
                    "message": {"type": "string"},
                    "role": {"type": "string", "enum": ["agent", "user", "supervisor"]}
                },
                "required": ["agentName", "message"]
            },
            "default_props": {
                "agentName": "Gerych Builder",
                "message": "Component generated and verified against test suite.",
                "role": "agent"
            }
        }
    }

    @classmethod
    def synthesize_component_from_prompt(
        cls,
        prompt: str,
        framework: str = "react",
        category: Optional[str] = None
    ) -> GeneratedComponent:
        """
        Synthesizes a Generative UI component matching prompt requirements with schema and markup.
        """
        cid = f"gen_comp_{uuid.uuid4().hex[:8]}"
        lower_prompt = prompt.lower()

        # Match template heuristic or synthesize custom
        if "kpi" in lower_prompt or "metric" in lower_prompt or "analytics" in lower_prompt:
            tpl = cls.BUILTIN_TEMPLATES["kpi_card"]
            comp_name = "CustomKPICard"
            cat = category or tpl["category"]
            code = tpl["react_code"].replace("KPIMetricCard", comp_name)
            schema = tpl["props_schema"]
            defaults = tpl["default_props"]
        elif "shop" in lower_prompt or "product" in lower_prompt or "ecom" in lower_prompt or "cart" in lower_prompt:
            tpl = cls.BUILTIN_TEMPLATES["ecommerce_card"]
            comp_name = "CustomProductCard"
            cat = category or tpl["category"]
            code = tpl["react_code"].replace("EcomProductCard", comp_name)
            schema = tpl["props_schema"]
            defaults = tpl["default_props"]
        elif "agent" in lower_prompt or "chat" in lower_prompt or "bubble" in lower_prompt:
            tpl = cls.BUILTIN_TEMPLATES["chat_bubble"]
            comp_name = "CustomAgentBubble"
            cat = category or tpl["category"]
            code = tpl["react_code"].replace("AgentChatBubble", comp_name)
            schema = tpl["props_schema"]
            defaults = tpl["default_props"]
        else:
            # Generic interactive container
            comp_name = f"GeneratedUI_{cid}"
            cat = category or "general"
            code = (
                f"export default function {comp_name}(props) {{\n"
                f"  return (\n"
                f"    <div className='p-6 rounded-2xl bg-zinc-900 border border-zinc-700 text-white shadow-lg'>\n"
                f"      <h3 className='text-md font-semibold'>Generated UI: {prompt[:40]}</h3>\n"
                f"      <p className='text-xs text-zinc-400 mt-2'>Dynamic interactive container generated via prompt.</p>\n"
                f"    </div>\n"
                f"  );\n"
                f"}}"
            )
            schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
            defaults = {"title": prompt[:30], "description": "Interactive Generative UI"}

        preview_html = f"<div class='dnk-gen-preview'>{comp_name} ({cat})</div>"

        return GeneratedComponent(
            component_id=cid,
            name=comp_name,
            framework=framework,
            category=cat,
            source_code=code,
            props_schema=schema,
            default_props=defaults,
            ai_prompt=prompt,
            preview_markup=preview_html
        )

    @staticmethod
    def validate_props(props: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validates provided props against JSON schema requirements."""
        errors: List[str] = []
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in props:
                errors.append(f"Missing required prop '{field}'")

        properties = schema.get("properties", {})
        for k, v in props.items():
            if k in properties:
                expected_type = properties[k].get("type")
                if expected_type == "string" and not isinstance(v, str):
                    errors.append(f"Prop '{k}' expected string, got {type(v).__name__}")
                elif expected_type == "number" and not isinstance(v, (int, float)):
                    errors.append(f"Prop '{k}' expected number, got {type(v).__name__}")
                elif expected_type == "boolean" and not isinstance(v, bool):
                    errors.append(f"Prop '{k}' expected boolean, got {type(v).__name__}")

                enum_vals = properties[k].get("enum")
                if enum_vals and v not in enum_vals:
                    errors.append(f"Prop '{k}' value '{v}' not in enum {enum_vals}")

        return len(errors) == 0, errors

    @staticmethod
    def suggest_auto_layout(
        nodes: List[Dict[str, Any]],
        layout_type: str = "horizontal_flow",
        spacing_x: float = 240.0,
        spacing_y: float = 160.0,
        start_x: float = 100.0,
        start_y: float = 100.0
    ) -> List[Dict[str, Any]]:
        """
        Calculates optimized positions for nodes based on layout algorithm.
        Supports: 'horizontal_flow', 'vertical_stack', 'grid_2col'.
        """
        positioned_nodes = []
        for i, node in enumerate(nodes):
            updated = dict(node)
            pos = dict(updated.get("position", {}))

            if layout_type == "horizontal_flow":
                pos["x"] = start_x + i * spacing_x
                pos["y"] = start_y
            elif layout_type == "vertical_stack":
                pos["x"] = start_x
                pos["y"] = start_y + i * spacing_y
            elif layout_type == "grid_2col":
                row = i // 2
                col = i % 2
                pos["x"] = start_x + col * spacing_x
                pos["y"] = start_y + row * spacing_y

            updated["position"] = pos
            positioned_nodes.append(updated)

        return positioned_nodes

    @staticmethod
    def infer_smart_connectors(
        nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Infers semantic edge connections based on node types (e.g. supervisor -> agent -> component).
        """
        edges = []
        supervisors = [n for n in nodes if n.get("node_type") == "supervisor"]
        agents = [n for n in nodes if n.get("node_type") in ("agent", "worker")]
        components = [n for n in nodes if n.get("node_type") in ("component", "ui")]

        # Connect supervisor to all agents
        for sup in supervisors:
            for ag in agents:
                edges.append({
                    "id": f"edge_sup_{sup['id']}_{ag['id']}",
                    "source_node_id": sup["id"],
                    "target_node_id": ag["id"],
                    "source_port": "dispatch",
                    "target_port": "task_in",
                    "edge_type": "smart_bezier",
                    "label": "Orchestrate"
                })

        # Connect agents to components
        for ag in agents:
            for comp in components:
                edges.append({
                    "id": f"edge_ag_{ag['id']}_{comp['id']}",
                    "source_node_id": ag["id"],
                    "target_node_id": comp["id"],
                    "source_port": "render_out",
                    "target_port": "view_in",
                    "edge_type": "smart_bezier",
                    "label": "Render State"
                })

        return edges
