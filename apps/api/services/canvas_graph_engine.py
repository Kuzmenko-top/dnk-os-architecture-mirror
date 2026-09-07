# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canvas_graph_engine"
# purpose: "Canvas Graph Engine for spatial layout, snapping, graph traversal, and edge validation (DNK-CANVAS-002 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field


@dataclass
class Point:
    x: float
    y: float

    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y}


@dataclass
class Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def contains(self, px: float, py: float) -> bool:
        return self.left <= px <= self.right and self.top <= py <= self.bottom

    def intersects(self, other: "Rect") -> bool:
        return not (
            self.right < other.left
            or self.left > other.right
            or self.bottom < other.top
            or self.top > other.bottom
        )

    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}


class CanvasSpatialMath:
    """Provides coordinate transformation between Screen space and World/Canvas space, plus snapping."""

    @staticmethod
    def world_to_screen(
        world_x: float,
        world_y: float,
        viewport_x: float,
        viewport_y: float,
        zoom: float
    ) -> Point:
        screen_x = (world_x - viewport_x) * zoom
        screen_y = (world_y - viewport_y) * zoom
        return Point(x=round(screen_x, 2), y=round(screen_y, 2))

    @staticmethod
    def screen_to_world(
        screen_x: float,
        screen_y: float,
        viewport_x: float,
        viewport_y: float,
        zoom: float
    ) -> Point:
        if zoom == 0:
            zoom = 1.0
        world_x = (screen_x / zoom) + viewport_x
        world_y = (screen_y / zoom) + viewport_y
        return Point(x=round(world_x, 2), y=round(world_y, 2))

    @staticmethod
    def snap_to_grid(val: float, grid_size: int = 16) -> float:
        if grid_size <= 0:
            return val
        return round(val / grid_size) * grid_size

    @staticmethod
    def snap_point(x: float, y: float, grid_size: int = 16, enabled: bool = True) -> Point:
        if not enabled or grid_size <= 0:
            return Point(x=x, y=y)
        return Point(
            x=CanvasSpatialMath.snap_to_grid(x, grid_size),
            y=CanvasSpatialMath.snap_to_grid(y, grid_size)
        )

    @staticmethod
    def calculate_bounding_box(nodes: List[Dict[str, Any]]) -> Optional[Rect]:
        if not nodes:
            return None
        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for n in nodes:
            pos = n.get("position", {})
            dim = n.get("dimensions", {})
            nx = pos.get("x", 0.0)
            ny = pos.get("y", 0.0)
            nw = dim.get("width", 100.0)
            nh = dim.get("height", 100.0)

            min_x = min(min_x, nx)
            min_y = min(min_y, ny)
            max_x = max(max_x, nx + nw)
            max_y = max(max_y, ny + nh)

        return Rect(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y)


class CanvasGraphEngine:
    """Core Canvas Graph Engine managing nodes, edges, spatial layouts, cycles, and traversal."""

    def __init__(self, canvas_id: str, grid_size: int = 16, snap_to_grid: bool = True):
        self.canvas_id = canvas_id
        self.grid_size = grid_size
        self.snap_to_grid = snap_to_grid
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[str, Dict[str, Any]] = {}

    def add_node(
        self,
        node_id: str,
        node_type: str,
        title: str,
        pos_x: float,
        pos_y: float,
        width: float = 200.0,
        height: float = 120.0,
        component_id: Optional[str] = None,
        parent_node_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        style: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        p = CanvasSpatialMath.snap_point(pos_x, pos_y, self.grid_size, self.snap_to_grid)
        node = {
            "id": node_id,
            "canvas_id": self.canvas_id,
            "node_type": node_type,
            "title": title,
            "position": {"x": p.x, "y": p.y},
            "dimensions": {"width": width, "height": height},
            "z_index": 0,
            "is_locked": False,
            "parent_node_id": parent_node_id,
            "component_id": component_id,
            "data": data or {},
            "style": style or {}
        }
        self.nodes[node_id] = node
        return node

    def move_node(self, node_id: str, new_x: float, new_y: float) -> Optional[Dict[str, Any]]:
        node = self.nodes.get(node_id)
        if not node or node.get("is_locked"):
            return None
        p = CanvasSpatialMath.snap_point(new_x, new_y, self.grid_size, self.snap_to_grid)
        node["position"]["x"] = p.x
        node["position"]["y"] = p.y
        return node

    def move_nodes_batch(self, node_ids: List[str], delta_x: float, delta_y: float) -> List[Dict[str, Any]]:
        updated = []
        for nid in node_ids:
            node = self.nodes.get(nid)
            if node and not node.get("is_locked"):
                cur_x = node["position"]["x"]
                cur_y = node["position"]["y"]
                target_x = cur_x + delta_x
                target_y = cur_y + delta_y
                p = CanvasSpatialMath.snap_point(target_x, target_y, self.grid_size, self.snap_to_grid)
                node["position"]["x"] = p.x
                node["position"]["y"] = p.y
                updated.append(node)
        return updated

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self.nodes:
            return False
        del self.nodes[node_id]
        # Cascade remove attached edges
        edges_to_remove = [
            eid for eid, e in self.edges.items()
            if e.get("source_node_id") == node_id or e.get("target_node_id") == node_id
        ]
        for eid in edges_to_remove:
            del self.edges[eid]
        return True

    def add_edge(
        self,
        edge_id: str,
        source_node_id: str,
        target_node_id: str,
        source_port: str = "out",
        target_port: str = "in",
        edge_type: str = "smart_bezier",
        label: Optional[str] = None,
        condition_expression: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        allow_cycles: bool = False
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        if source_node_id not in self.nodes:
            return None, f"Source node '{source_node_id}' does not exist"
        if target_node_id not in self.nodes:
            return None, f"Target node '{target_node_id}' does not exist"
        if source_node_id == target_node_id:
            return None, "Self-referencing edges are not permitted"

        # Check existing edge duplication
        for e in self.edges.values():
            if (
                e["source_node_id"] == source_node_id
                and e["target_node_id"] == target_node_id
                and e["source_port"] == source_port
                and e["target_port"] == target_port
            ):
                return None, "Duplicate edge between specified ports already exists"

        # Cycle check if cycles not allowed
        if not allow_cycles:
            if self._creates_cycle(source_node_id, target_node_id):
                return None, f"Edge from '{source_node_id}' to '{target_node_id}' introduces a cycle in DAG"

        edge = {
            "id": edge_id,
            "canvas_id": self.canvas_id,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "source_port": source_port,
            "target_port": target_port,
            "edge_type": edge_type,
            "label": label,
            "condition_expression": condition_expression,
            "data": data or {},
            "style": {"stroke": "#6366f1", "strokeWidth": 2}
        }
        self.edges[edge_id] = edge
        return edge, None

    def remove_edge(self, edge_id: str) -> bool:
        if edge_id not in self.edges:
            return False
        del self.edges[edge_id]
        return True

    def _creates_cycle(self, source_node_id: str, target_node_id: str) -> bool:
        # Check if source_node_id is reachable from target_node_id
        visited: Set[str] = set()
        queue = [target_node_id]

        while queue:
            curr = queue.pop(0)
            if curr == source_node_id:
                return True
            if curr not in visited:
                visited.add(curr)
                # Find all outgoing neighbors from curr
                for e in self.edges.values():
                    if e["source_node_id"] == curr:
                        nxt = e["target_node_id"]
                        if nxt not in visited:
                            queue.append(nxt)
        return False

    def topological_sort(self) -> Tuple[List[str], bool]:
        """Returns sorted list of node_ids and boolean indicating if DAG is valid (no cycles)."""
        in_degree: Dict[str, int] = {nid: 0 for nid in self.nodes}
        adj: Dict[str, List[str]] = {nid: [] for nid in self.nodes}

        for e in self.edges.values():
            s = e["source_node_id"]
            t = e["target_node_id"]
            if s in self.nodes and t in self.nodes:
                adj[s].append(t)
                in_degree[t] = in_degree.get(t, 0) + 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for nxt in adj.get(curr, []):
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        has_cycle = len(order) < len(self.nodes)
        return order, not has_cycle

    def find_downstream_nodes(self, start_node_id: str) -> List[str]:
        if start_node_id not in self.nodes:
            return []
        visited: Set[str] = set()
        queue = [start_node_id]
        result = []

        while queue:
            curr = queue.pop(0)
            for e in self.edges.values():
                if e["source_node_id"] == curr:
                    nxt = e["target_node_id"]
                    if nxt not in visited and nxt in self.nodes:
                        visited.add(nxt)
                        result.append(nxt)
                        queue.append(nxt)
        return result

    def select_nodes_in_marquee(self, marquee_rect: Rect) -> List[str]:
        selected = []
        for nid, node in self.nodes.items():
            pos = node.get("position", {})
            dim = node.get("dimensions", {})
            node_rect = Rect(
                x=pos.get("x", 0.0),
                y=pos.get("y", 0.0),
                width=dim.get("width", 100.0),
                height=dim.get("height", 100.0)
            )
            if marquee_rect.intersects(node_rect):
                selected.append(nid)
        return selected
