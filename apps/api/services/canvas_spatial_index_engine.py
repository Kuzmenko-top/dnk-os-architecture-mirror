# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canvas_spatial_index_engine"
# purpose: "Spatial Indexing Engine (R-Tree / Quadtree) for Viewport Culling and Nearest Neighbor on Infinite Canvas (DNK-CANVAS-003 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import math
from typing import Dict, List, Optional, Tuple, Any


class SpatialItem:
    """Represents a bounded element in the 2D spatial plane."""

    def __init__(
        self,
        node_id: str,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
        lod_level: int = 0,
        group_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.node_id = node_id
        self.min_x = float(min(min_x, max_x))
        self.min_y = float(min(min_y, max_y))
        self.max_x = float(max(min_x, max_x))
        self.max_y = float(max(min_y, max_y))
        self.lod_level = lod_level
        self.group_id = group_id
        self.metadata = metadata or {}

    @property
    def center_x(self) -> float:
        return (self.min_x + self.max_x) / 2.0

    @property
    def center_y(self) -> float:
        return (self.min_y + self.max_y) / 2.0

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    def intersects(self, bbox: Tuple[float, float, float, float]) -> bool:
        b_min_x, b_min_y, b_max_x, b_max_y = bbox
        return not (
            self.max_x < b_min_x
            or self.min_x > b_max_x
            or self.max_y < b_min_y
            or self.min_y > b_max_y
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "min_x": self.min_x,
            "min_y": self.min_y,
            "max_x": self.max_x,
            "max_y": self.max_y,
            "lod_level": self.lod_level,
            "group_id": self.group_id,
            "metadata": self.metadata,
        }


class CanvasSpatialIndexEngine:
    """
    High-performance 2D spatial indexing engine for millions of canvas nodes.
    Provides viewport culling, range bounding box queries, nearest neighbors, and LOD filtering.
    """

    def __init__(self, canvas_id: str, grid_cell_size: float = 500.0):
        self.canvas_id = canvas_id
        self.grid_cell_size = max(10.0, grid_cell_size)
        self.items: Dict[str, SpatialItem] = {}
        # Spatial hash grid for fast localized partitioning: (cell_x, cell_y) -> set of node_ids
        self.grid: Dict[Tuple[int, int], set] = {}

    def _get_cell_coords(self, x: float, y: float) -> Tuple[int, int]:
        return int(math.floor(x / self.grid_cell_size)), int(
            math.floor(y / self.grid_cell_size)
        )

    def _get_overlapping_cells(
        self, min_x: float, min_y: float, max_x: float, max_y: float
    ) -> List[Tuple[int, int]]:
        c_min_x, c_min_y = self._get_cell_coords(min_x, min_y)
        c_max_x, c_max_y = self._get_cell_coords(max_x, max_y)
        cells = []
        for cx in range(c_min_x, c_max_x + 1):
            for cy in range(c_min_y, c_max_y + 1):
                cells.append((cx, cy))
        return cells

    def insert_node(
        self,
        node_id: str,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
        lod_level: int = 0,
        group_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Inserts or overwrites a node into the spatial index."""
        if node_id in self.items:
            self.remove_node(node_id)

        item = SpatialItem(
            node_id=node_id,
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
            lod_level=lod_level,
            group_id=group_id,
            metadata=metadata,
        )
        self.items[node_id] = item

        for cell in self._get_overlapping_cells(
            item.min_x, item.min_y, item.max_x, item.max_y
        ):
            if cell not in self.grid:
                self.grid[cell] = set()
            self.grid[cell].add(node_id)

        return item.to_dict()

    def update_node(
        self,
        node_id: str,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
        lod_level: int = 0,
        group_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Updates spatial boundaries of an existing node."""
        if node_id not in self.items:
            return None
        return self.insert_node(
            node_id=node_id,
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
            lod_level=lod_level,
            group_id=group_id,
            metadata=metadata,
        )

    def remove_node(self, node_id: str) -> bool:
        """Removes a node from the spatial index and all occupied grid cells."""
        item = self.items.pop(node_id, None)
        if not item:
            return False

        for cell in self._get_overlapping_cells(
            item.min_x, item.min_y, item.max_x, item.max_y
        ):
            if cell in self.grid and node_id in self.grid[cell]:
                self.grid[cell].remove(node_id)
                if not self.grid[cell]:
                    del self.grid[cell]
        return True

    def query_viewport(
        self,
        viewport_bbox: Tuple[float, float, float, float],
        lod_filter: Optional[int] = None,
        group_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Queries all nodes intersecting the given viewport bounding box.
        viewport_bbox: (min_x, min_y, max_x, max_y)
        lod_filter: if specified, only returns nodes with lod_level <= lod_filter
        """
        v_min_x, v_min_y, v_max_x, v_max_y = viewport_bbox
        target_cells = self._get_overlapping_cells(v_min_x, v_min_y, v_max_x, v_max_y)

        candidate_ids = set()
        for cell in target_cells:
            if cell in self.grid:
                candidate_ids.update(self.grid[cell])

        results = []
        for node_id in candidate_ids:
            item = self.items.get(node_id)
            if not item:
                continue
            if lod_filter is not None and item.lod_level > lod_filter:
                continue
            if group_id is not None and item.group_id != group_id:
                continue
            if item.intersects(viewport_bbox):
                results.append(item.to_dict())

        return results

    def find_nearest_neighbors(
        self,
        x: float,
        y: float,
        k: int = 5,
        max_distance: float = 2000.0,
    ) -> List[Dict[str, Any]]:
        """Finds k nearest neighboring nodes around point (x, y) within max_distance."""
        if not self.items:
            return []

        search_bbox = (
            x - max_distance,
            y - max_distance,
            x + max_distance,
            y + max_distance,
        )
        candidates = self.query_viewport(search_bbox)

        scored = []
        for cand in candidates:
            cx = (cand["min_x"] + cand["max_x"]) / 2.0
            cy = (cand["min_y"] + cand["max_y"]) / 2.0
            dist = math.hypot(cx - x, cy - y)
            if dist <= max_distance:
                cand_copy = dict(cand)
                cand_copy["distance"] = round(dist, 2)
                scored.append((dist, cand_copy))

        scored.sort(key=lambda item: item[0])
        return [item[1] for item in scored[:k]]

    def compute_bounding_box(self, node_ids: List[str]) -> Optional[Dict[str, float]]:
        """Computes the overall bounding box enclosing the given node IDs."""
        valid_items = [self.items[nid] for nid in node_ids if nid in self.items]
        if not valid_items:
            return None

        min_x = min(item.min_x for item in valid_items)
        min_y = min(item.min_y for item in valid_items)
        max_x = max(item.max_x for item in valid_items)
        max_y = max(item.max_y for item in valid_items)

        return {
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
            "width": max_x - min_x,
            "height": max_y - min_y,
            "center_x": (min_x + max_x) / 2.0,
            "center_y": (min_y + max_y) / 2.0,
        }

    def bulk_index_nodes(self, nodes: List[Dict[str, Any]]) -> int:
        """Bulk indexes a collection of node dictionaries."""
        count = 0
        for node in nodes:
            node_id = node.get("node_id") or node.get("id")
            if not node_id:
                continue
            min_x = float(node.get("min_x", node.get("x", 0.0)))
            min_y = float(node.get("min_y", node.get("y", 0.0)))
            width = float(node.get("width", 100.0))
            height = float(node.get("height", 100.0))
            max_x = float(node.get("max_x", min_x + width))
            max_y = float(node.get("max_y", min_y + height))
            lod_level = int(node.get("lod_level", 0))
            group_id = node.get("group_id")

            self.insert_node(
                node_id=node_id,
                min_x=min_x,
                min_y=min_y,
                max_x=max_x,
                max_y=max_y,
                lod_level=lod_level,
                group_id=group_id,
                metadata=node.get("metadata", {}),
            )
            count += 1
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Returns diagnostic statistics of the spatial index."""
        return {
            "canvas_id": self.canvas_id,
            "total_nodes_indexed": len(self.items),
            "total_active_grid_cells": len(self.grid),
            "grid_cell_size": self.grid_cell_size,
        }
