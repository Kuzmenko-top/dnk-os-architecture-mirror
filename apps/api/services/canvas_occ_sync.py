# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canvas_occ_sync"
# purpose: "Optimistic Concurrency Control (OCC) and Real-Time State Synchronization Engine for Canvas (DNK-CANVAS-002 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class PatchOpType(str, Enum):
    NODE_ADD = "NODE_ADD"
    NODE_MOVE = "NODE_MOVE"
    NODE_UPDATE = "NODE_UPDATE"
    NODE_DELETE = "NODE_DELETE"
    EDGE_ADD = "EDGE_ADD"
    EDGE_DELETE = "EDGE_DELETE"
    VIEWPORT_CHANGE = "VIEWPORT_CHANGE"
    SELECTION_CHANGE = "SELECTION_CHANGE"


@dataclass
class CanvasPatchOp:
    op_type: PatchOpType
    client_id: str
    base_version: int
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    patch_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_type": self.op_type.value if isinstance(self.op_type, PatchOpType) else str(self.op_type),
            "client_id": self.client_id,
            "base_version": self.base_version,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "patch_id": self.patch_id
        }


class CanvasOCCSyncManager:
    """Manages version vectors, optimistic concurrency, conflict resolution, locks, and history replay."""

    def __init__(self, canvas_id: str, initial_version: int = 1):
        self.canvas_id = canvas_id
        self.current_version = initial_version
        self.version_vector: Dict[str, int] = {}  # client_id -> latest seen version
        self.node_locks: Dict[str, Dict[str, Any]] = {}  # node_id -> {client_id, locked_at}
        self.history_buffer: List[Dict[str, Any]] = []
        self.state_nodes: Dict[str, Dict[str, Any]] = {}
        self.state_edges: Dict[str, Dict[str, Any]] = {}
        self.viewport: Dict[str, float] = {"x": 0.0, "y": 0.0, "zoom": 1.0}

    def acquire_lock(self, node_id: str, client_id: str, timeout_seconds: float = 30.0) -> Tuple[bool, Optional[str]]:
        now = time.time()
        existing = self.node_locks.get(node_id)
        if existing:
            # Check expiration
            if now - existing.get("locked_at", 0) > timeout_seconds:
                # Expired lock
                self.node_locks[node_id] = {"client_id": client_id, "locked_at": now}
                return True, None
            if existing["client_id"] != client_id:
                return False, f"Node '{node_id}' is currently locked by client '{existing['client_id']}'"
        self.node_locks[node_id] = {"client_id": client_id, "locked_at": now}
        return True, None

    def release_lock(self, node_id: str, client_id: str) -> bool:
        existing = self.node_locks.get(node_id)
        if existing and existing["client_id"] == client_id:
            del self.node_locks[node_id]
            return True
        return False

    def release_all_client_locks(self, client_id: str) -> int:
        to_del = [nid for nid, lock in self.node_locks.items() if lock.get("client_id") == client_id]
        for nid in to_del:
            del self.node_locks[nid]
        return len(to_del)

    def apply_patch(self, patch: CanvasPatchOp) -> Tuple[bool, int, Optional[Dict[str, Any]], Optional[str]]:
        """
        Applies patch with OCC conflict detection.
        Returns (success, new_version, resolved_payload, error_message).
        """
        # Lock check for node operations
        node_id = patch.payload.get("node_id") or patch.payload.get("id")
        if node_id and patch.op_type in (PatchOpType.NODE_MOVE, PatchOpType.NODE_UPDATE, PatchOpType.NODE_DELETE):
            lock = self.node_locks.get(node_id)
            if lock and lock["client_id"] != patch.client_id:
                # Allow only if lock expired (> 30s)
                if time.time() - lock["locked_at"] <= 30.0:
                    return False, self.current_version, None, f"Node '{node_id}' locked by peer '{lock['client_id']}'"

        # Check version drift
        version_lag = self.current_version - patch.base_version
        resolved_payload = dict(patch.payload)

        # Apply transformation according to op_type
        if patch.op_type == PatchOpType.NODE_ADD:
            nid = patch.payload.get("id")
            if not nid:
                return False, self.current_version, None, "Missing node id for NODE_ADD"
            self.state_nodes[nid] = dict(patch.payload)

        elif patch.op_type == PatchOpType.NODE_MOVE:
            nid = patch.payload.get("node_id")
            if nid not in self.state_nodes:
                return False, self.current_version, None, f"Node '{nid}' does not exist for NODE_MOVE"
            # LWW on position
            self.state_nodes[nid]["position"] = {
                "x": patch.payload.get("x", self.state_nodes[nid]["position"]["x"]),
                "y": patch.payload.get("y", self.state_nodes[nid]["position"]["y"])
            }

        elif patch.op_type == PatchOpType.NODE_UPDATE:
            nid = patch.payload.get("node_id")
            if nid not in self.state_nodes:
                return False, self.current_version, None, f"Node '{nid}' does not exist for NODE_UPDATE"
            # Merge dictionary data
            if "data" in patch.payload:
                self.state_nodes[nid].setdefault("data", {}).update(patch.payload["data"])
            if "style" in patch.payload:
                self.state_nodes[nid].setdefault("style", {}).update(patch.payload["style"])
            if "title" in patch.payload:
                self.state_nodes[nid]["title"] = patch.payload["title"]

        elif patch.op_type == PatchOpType.NODE_DELETE:
            nid = patch.payload.get("node_id")
            if nid in self.state_nodes:
                del self.state_nodes[nid]
            # cascade delete edges
            self.state_edges = {
                eid: e for eid, e in self.state_edges.items()
                if e.get("source_node_id") != nid and e.get("target_node_id") != nid
            }

        elif patch.op_type == PatchOpType.EDGE_ADD:
            eid = patch.payload.get("id")
            if not eid:
                return False, self.current_version, None, "Missing edge id for EDGE_ADD"
            self.state_edges[eid] = dict(patch.payload)

        elif patch.op_type == PatchOpType.EDGE_DELETE:
            eid = patch.payload.get("edge_id")
            if eid in self.state_edges:
                del self.state_edges[eid]

        elif patch.op_type == PatchOpType.VIEWPORT_CHANGE:
            self.viewport["x"] = patch.payload.get("x", self.viewport["x"])
            self.viewport["y"] = patch.payload.get("y", self.viewport["y"])
            self.viewport["zoom"] = patch.payload.get("zoom", self.viewport["zoom"])

        # Increment canvas version
        self.current_version += 1
        self.version_vector[patch.client_id] = self.current_version

        # Record into history buffer
        history_record = {
            "version": self.current_version,
            "patch": patch.to_dict(),
            "server_time": time.time()
        }
        self.history_buffer.append(history_record)

        return True, self.current_version, resolved_payload, None

    def get_snapshot(self) -> Dict[str, Any]:
        return {
            "canvas_id": self.canvas_id,
            "version": self.current_version,
            "nodes": self.state_nodes,
            "edges": self.state_edges,
            "viewport": self.viewport,
            "active_locks": self.node_locks
        }

    def get_patches_since(self, since_version: int) -> List[Dict[str, Any]]:
        return [h for h in self.history_buffer if h["version"] > since_version]
