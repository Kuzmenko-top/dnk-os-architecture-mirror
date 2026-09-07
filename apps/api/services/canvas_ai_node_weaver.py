# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canvas_ai_node_weaver"
# purpose: "Gemini/LLM-Powered Contextual Node Synthesis, Smart Auto-Wiring & Semantic Grouping for Infinite Canvas (DNK-CANVAS-003 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import math
import uuid
from typing import Dict, List, Optional, Any, Tuple


class CanvasAINodeWeaver:
    """
    Context-aware AI node generation & flow synthesis engine for Infinite Canvas.
    Synthesizes nodes, calculates non-overlapping spatial layouts, auto-wires edges,
    and clusters generated nodes into semantic groups.
    """

    NODE_DIMENSIONS = {
        "action": (180.0, 90.0),
        "trigger": (160.0, 80.0),
        "condition": (150.0, 75.0),
        "api": (200.0, 100.0),
        "transformer": (180.0, 90.0),
        "database": (170.0, 85.0),
        "output": (150.0, 80.0),
        "default": (160.0, 80.0),
    }

    def __init__(self, default_spacing: float = 60.0):
        self.default_spacing = default_spacing

    def synthesize_subflow(
        self,
        canvas_id: str,
        prompt: str,
        context_nodes: Optional[List[Dict[str, Any]]] = None,
        target_origin: Optional[Tuple[float, float]] = None,
        auto_group: bool = True,
        group_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes a structured subflow (nodes, edges, group) based on the user prompt
        and surrounding context nodes.
        """
        context_nodes = context_nodes or []
        parsed_steps = self._decompose_prompt_to_steps(prompt)

        # Determine origin point for placement
        origin_x, origin_y = self._calculate_origin_coords(
            context_nodes=context_nodes, target_origin=target_origin
        )

        generated_nodes = []
        generated_edges = []

        curr_x = origin_x
        curr_y = origin_y

        prev_node_id = None
        # If context nodes exist, find nearest terminal/downstream node to connect from
        if context_nodes:
            prev_node_id = context_nodes[-1].get("id") or context_nodes[-1].get(
                "node_id"
            )

        for i, step in enumerate(parsed_steps):
            node_id = f"node-ai-{uuid.uuid4().hex[:8]}"
            node_type = step.get("type", "action")
            width, height = self.NODE_DIMENSIONS.get(
                node_type, self.NODE_DIMENSIONS["default"]
            )

            node_data = {
                "id": node_id,
                "canvas_id": canvas_id,
                "type": node_type,
                "title": step.get("title", f"Step {i+1}"),
                "x": curr_x,
                "y": curr_y,
                "width": width,
                "height": height,
                "config": step.get("config", {}),
                "metadata": {
                    "generated_by": "canvas_ai_node_weaver",
                    "source_prompt": prompt,
                    "step_index": i,
                },
            }
            generated_nodes.append(node_data)

            # Auto-wire edge from previous node
            if prev_node_id:
                edge_id = f"edge-ai-{uuid.uuid4().hex[:8]}"
                generated_edges.append(
                    {
                        "id": edge_id,
                        "canvas_id": canvas_id,
                        "source_node_id": prev_node_id,
                        "target_node_id": node_id,
                        "label": step.get("edge_label", "flow"),
                        "edge_type": "smart_curved",
                    }
                )

            prev_node_id = node_id
            curr_x += width + self.default_spacing

        # Create semantic group if requested
        group = None
        if auto_group and generated_nodes:
            group = self.create_semantic_group(
                canvas_id=canvas_id,
                title=group_title or f"AI Flow: {prompt[:30]}...",
                nodes=generated_nodes,
            )

        return {
            "canvas_id": canvas_id,
            "prompt": prompt,
            "nodes": generated_nodes,
            "edges": generated_edges,
            "group": group,
            "total_nodes_generated": len(generated_nodes),
            "total_edges_generated": len(generated_edges),
        }

    def _decompose_prompt_to_steps(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Parses prompt and extracts step taxonomy.
        """
        lower = prompt.lower()
        steps = []

        if "checkout" in lower or "payment" in lower:
            steps = [
                {
                    "type": "trigger",
                    "title": "Checkout Initiated",
                    "config": {"event": "checkout_started"},
                    "edge_label": "on_start",
                },
                {
                    "type": "condition",
                    "title": "Validate Cart & Inventory",
                    "config": {"rules": ["min_order > 0", "stock_available"]},
                    "edge_label": "is_valid",
                },
                {
                    "type": "api",
                    "title": "Process Shopify Payment",
                    "config": {"gateway": "shopify_payments", "capture": True},
                    "edge_label": "on_success",
                },
                {
                    "type": "output",
                    "title": "Post-Purchase Thank You",
                    "config": {"template": "thank_you_v2"},
                    "edge_label": "rendered",
                },
            ]
        elif "etl" in lower or "pipeline" in lower or "sync" in lower:
            steps = [
                {
                    "type": "trigger",
                    "title": "Data Ingest Trigger",
                    "config": {"source": "webhook_or_cron"},
                    "edge_label": "ingested",
                },
                {
                    "type": "transformer",
                    "title": "Schema Normalizer",
                    "config": {"target_format": "DNK-STD-0075"},
                    "edge_label": "normalized",
                },
                {
                    "type": "database",
                    "title": "PostgreSQL Upsert",
                    "config": {"table": "events_store"},
                    "edge_label": "persisted",
                },
            ]
        else:
            # General step generation based on sentence phrases or default 3-stage pipeline
            phrases = [
                p.strip() for p in prompt.replace("->", ",").split(",") if p.strip()
            ]
            if len(phrases) >= 2:
                for i, p in enumerate(phrases):
                    stype = (
                        "trigger"
                        if i == 0
                        else ("output" if i == len(phrases) - 1 else "action")
                    )
                    steps.append(
                        {
                            "type": stype,
                            "title": p.capitalize(),
                            "config": {"raw_instruction": p},
                            "edge_label": "next",
                        }
                    )
            else:
                steps = [
                    {
                        "type": "trigger",
                        "title": f"Start: {prompt[:20]}",
                        "config": {},
                        "edge_label": "trigger",
                    },
                    {
                        "type": "action",
                        "title": "Process Instruction",
                        "config": {"prompt": prompt},
                        "edge_label": "done",
                    },
                    {
                        "type": "output",
                        "title": "Complete Task",
                        "config": {},
                        "edge_label": "finish",
                    },
                ]

        return steps

    def _calculate_origin_coords(
        self,
        context_nodes: List[Dict[str, Any]],
        target_origin: Optional[Tuple[float, float]],
    ) -> Tuple[float, float]:
        """Calculates optimal top-left origin coordinates to avoid overlap."""
        if target_origin is not None:
            return float(target_origin[0]), float(target_origin[1])

        if not context_nodes:
            return (100.0, 100.0)

        # Place to the right of the rightmost context node
        max_x = max(
            float(n.get("x", 0.0)) + float(n.get("width", 150.0)) for n in context_nodes
        )
        avg_y = sum(float(n.get("y", 100.0)) for n in context_nodes) / len(context_nodes)

        return (max_x + self.default_spacing * 2, avg_y)

    def create_semantic_group(
        self,
        canvas_id: str,
        title: str,
        nodes: List[Dict[str, Any]],
        color: str = "#6366f1",
        padding: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Creates a bounding group encapsulating the given nodes.
        """
        if not nodes:
            return {}

        min_x = min(float(n["x"]) for n in nodes) - padding
        min_y = min(float(n["y"]) for n in nodes) - padding
        max_x = (
            max(float(n["x"]) + float(n.get("width", 150.0)) for n in nodes) + padding
        )
        max_y = (
            max(float(n["y"]) + float(n.get("height", 80.0)) for n in nodes) + padding
        )

        node_ids = [n["id"] for n in nodes]
        group_id = f"group-sem-{uuid.uuid4().hex[:8]}"

        return {
            "id": group_id,
            "canvas_id": canvas_id,
            "title": title,
            "color": color,
            "node_ids": node_ids,
            "bounding_box": {
                "min_x": min_x,
                "min_y": min_y,
                "max_x": max_x,
                "max_y": max_y,
                "width": max_x - min_x,
                "height": max_y - min_y,
            },
            "is_collapsed": False,
        }
