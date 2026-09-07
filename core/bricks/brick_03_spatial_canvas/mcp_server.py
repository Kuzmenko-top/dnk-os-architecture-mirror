# --- DNK-MRH-HEADER ---
# mrh_id: "core/bricks/brick_03_spatial_canvas/mcp_server.py"
# purpose: "FastMCP Server exposing Brick 03 Spatial Canvas V3 Engine tools to the swarm."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from core.bricks.brick_03_spatial_canvas.contracts.schemas import CanvasNode, CanvasEdge, CanvasGraphState

mcp = FastMCP("brick_03_spatial_canvas")


@mcp.tool()
def canvas_get_state(canvas_id: str) -> Dict[str, Any]:
    """
    Fetches the live Spatial Canvas V3 node graph state including all agent, task, and media nodes.
    """
    state = CanvasGraphState(
        canvas_id=canvas_id,
        nodes=[
            CanvasNode(id="node_1", type="SwarmAgentNode", position={"x": 100.0, "y": 100.0}, data={"agent": "gerych_prime"}),
            CanvasNode(id="node_2", type="ShopifyBuilderNode", position={"x": 400.0, "y": 100.0}, data={"theme": "Dawn OS 2.0"}),
        ],
        edges=[
            CanvasEdge(id="edge_1_2", source="node_1", target="node_2"),
        ],
        version=1,
    )
    return state.model_dump()


@mcp.tool()
def canvas_upsert_node(canvas_id: str, node_id: str, node_type: str, x: float, y: float, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Creates or updates a node position and metadata on the interactive Visual Canvas.
    """
    node = CanvasNode(
        id=node_id,
        type=node_type,
        position={"x": x, "y": y},
        data=data or {},
    )
    return {"status": "upserted", "canvas_id": canvas_id, "node": node.model_dump()}


@mcp.tool()
def canvas_connect_nodes(canvas_id: str, edge_id: str, source: str, target: str, edge_type: str = "default") -> Dict[str, Any]:
    """
    Connects two spatial nodes with a directional dataflow edge on the Visual Canvas.
    """
    edge = CanvasEdge(
        id=edge_id,
        source=source,
        target=target,
        type=edge_type,
    )
    return {"status": "connected", "canvas_id": canvas_id, "edge": edge.model_dump()}


if __name__ == "__main__":
    mcp.run()
