# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canvas_collaboration_arbiter"
# purpose: "Lock Arbiter, Multi-User Conflict Resolution & Presence Tracker for Infinite Canvas (DNK-CANVAS-003 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import time
from typing import Dict, List, Optional, Any


class NodeLock:
    """Represents an active exclusive lock on a canvas node or group."""

    def __init__(
        self,
        node_id: str,
        user_id: str,
        user_name: str,
        ttl_sec: float = 15.0,
    ):
        self.node_id = node_id
        self.user_id = user_id
        self.user_name = user_name
        self.ttl_sec = ttl_sec
        self.acquired_at = time.time()
        self.expires_at = self.acquired_at + ttl_sec

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def renew(self, ttl_sec: Optional[float] = None) -> None:
        if ttl_sec is not None:
            self.ttl_sec = ttl_sec
        self.expires_at = time.time() + self.ttl_sec

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "ttl_sec": self.ttl_sec,
            "acquired_at": self.acquired_at,
            "expires_at": self.expires_at,
            "is_expired": self.is_expired,
        }


class CanvasCollaborationArbiter:
    """
    Arbitrates multi-user concurrency, lock disputes, real-time presence heartbeats,
    and cursor event streams across collaborative canvas sessions.
    """

    def __init__(self, canvas_id: str):
        self.canvas_id = canvas_id
        # node_id -> NodeLock
        self.node_locks: Dict[str, NodeLock] = {}
        # user_id -> presence dict
        self.presences: Dict[str, Dict[str, Any]] = {}
        # user_id -> list of recent cursor stream events
        self.cursor_streams: Dict[str, List[Dict[str, Any]]] = {}

    def acquire_node_lock(
        self,
        node_id: str,
        user_id: str,
        user_name: str = "Anonymous",
        ttl_sec: float = 15.0,
    ) -> Dict[str, Any]:
        """
        Attempts to acquire an exclusive lock on a node.
        Returns lock status dict.
        """
        self._prune_expired_locks()
        current_lock = self.node_locks.get(node_id)

        if current_lock and not current_lock.is_expired:
            if current_lock.user_id == user_id:
                current_lock.renew(ttl_sec)
                return {
                    "success": True,
                    "status": "RENEWED",
                    "lock": current_lock.to_dict(),
                }
            return {
                "success": False,
                "status": "LOCKED_BY_OTHER",
                "locked_by": current_lock.to_dict(),
            }

        new_lock = NodeLock(
            node_id=node_id,
            user_id=user_id,
            user_name=user_name,
            ttl_sec=ttl_sec,
        )
        self.node_locks[node_id] = new_lock
        return {
            "success": True,
            "status": "ACQUIRED",
            "lock": new_lock.to_dict(),
        }

    def release_node_lock(self, node_id: str, user_id: str) -> bool:
        """Releases lock if owned by user_id or already expired."""
        current_lock = self.node_locks.get(node_id)
        if not current_lock:
            return True
        if current_lock.user_id == user_id or current_lock.is_expired:
            del self.node_locks[node_id]
            return True
        return False

    def renew_node_lock(
        self, node_id: str, user_id: str, ttl_sec: float = 15.0
    ) -> bool:
        """Renews an active lock held by user_id."""
        current_lock = self.node_locks.get(node_id)
        if current_lock and current_lock.user_id == user_id and not current_lock.is_expired:
            current_lock.renew(ttl_sec)
            return True
        return False

    def get_locked_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Returns all currently active (non-expired) node locks."""
        self._prune_expired_locks()
        return {nid: lock.to_dict() for nid, lock in self.node_locks.items()}

    def record_presence_heartbeat(
        self,
        user_id: str,
        user_name: str,
        user_color: str,
        cursor_x: float = 0.0,
        cursor_y: float = 0.0,
        viewport_bounds: Optional[Dict[str, float]] = None,
        selected_node_ids: Optional[List[str]] = None,
        active_tool: str = "select",
    ) -> Dict[str, Any]:
        """Updates or registers a collaborator's presence state."""
        now = time.time()
        presence_data = {
            "canvas_id": self.canvas_id,
            "user_id": user_id,
            "user_name": user_name,
            "user_color": user_color,
            "cursor_x": cursor_x,
            "cursor_y": cursor_y,
            "viewport_bounds": viewport_bounds
            or {"min_x": 0, "min_y": 0, "max_x": 1920, "max_y": 1080},
            "selected_node_ids": selected_node_ids or [],
            "active_tool": active_tool,
            "last_heartbeat_at": now,
            "is_online": True,
        }
        self.presences[user_id] = presence_data
        return presence_data

    def get_active_presences(self, timeout_sec: float = 30.0) -> List[Dict[str, Any]]:
        """Returns all users who sent a presence heartbeat within timeout_sec."""
        now = time.time()
        active = []
        for user_id, pres in self.presences.items():
            if now - pres["last_heartbeat_at"] <= timeout_sec:
                active.append(pres)
        return active

    def prune_stale_presences(self, timeout_sec: float = 30.0) -> int:
        """Removes collaborators whose heartbeat has expired."""
        now = time.time()
        stale_user_ids = [
            uid
            for uid, pres in self.presences.items()
            if now - pres["last_heartbeat_at"] > timeout_sec
        ]
        for uid in stale_user_ids:
            del self.presences[uid]
            if uid in self.cursor_streams:
                del self.cursor_streams[uid]
            # also release any locks held by this user
            locks_to_release = [
                nid for nid, lock in self.node_locks.items() if lock.user_id == uid
            ]
            for nid in locks_to_release:
                del self.node_locks[nid]

        return len(stale_user_ids)

    def process_cursor_event(
        self,
        user_id: str,
        event_type: str,
        x: float,
        y: float,
        payload: Optional[Dict[str, Any]] = None,
        max_stream_history: int = 50,
    ) -> Dict[str, Any]:
        """
        Records a cursor or pointer action, updating local presence cursor position.
        """
        now = time.time()
        event = {
            "canvas_id": self.canvas_id,
            "user_id": user_id,
            "event_type": event_type,
            "x": x,
            "y": y,
            "payload": payload or {},
            "timestamp": now,
        }

        if user_id not in self.cursor_streams:
            self.cursor_streams[user_id] = []

        self.cursor_streams[user_id].append(event)
        if len(self.cursor_streams[user_id]) > max_stream_history:
            self.cursor_streams[user_id] = self.cursor_streams[user_id][
                -max_stream_history:
            ]

        # Update presence cursor coordinates if user registered
        if user_id in self.presences:
            self.presences[user_id]["cursor_x"] = x
            self.presences[user_id]["cursor_y"] = y
            self.presences[user_id]["last_heartbeat_at"] = now

        return event

    def get_cursor_stream(
        self, user_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Returns recent cursor events for a given user."""
        stream = self.cursor_streams.get(user_id, [])
        return stream[-limit:]

    def _prune_expired_locks(self) -> None:
        expired_nids = [nid for nid, lock in self.node_locks.items() if lock.is_expired]
        for nid in expired_nids:
            del self.node_locks[nid]
