# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canvas_history_time_travel_engine"
# purpose: "Time-Travel Snapshots, Undo/Redo Stacks & Branch-Merge Engine for Infinite Canvas (DNK-CANVAS-003 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import copy
import time
import uuid
from typing import Dict, List, Optional, Any


class CanvasSnapshot:
    """Represents an immutable point-in-time snapshot of the canvas state."""

    def __init__(
        self,
        snapshot_id: str,
        canvas_id: str,
        version_index: int,
        author_id: str,
        state_data: Dict[str, Any],
        snapshot_tag: Optional[str] = None,
        parent_snapshot_id: Optional[str] = None,
    ):
        self.id = snapshot_id
        self.canvas_id = canvas_id
        self.version_index = version_index
        self.author_id = author_id
        # state_data contains nodes list, edges list, groups list
        self.state_data = copy.deepcopy(state_data)
        self.snapshot_tag = snapshot_tag
        self.parent_snapshot_id = parent_snapshot_id
        self.created_at = time.time()

    @property
    def nodes_count(self) -> int:
        return len(self.state_data.get("nodes", []))

    @property
    def edges_count(self) -> int:
        return len(self.state_data.get("edges", []))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "canvas_id": self.canvas_id,
            "version_index": self.version_index,
            "author_id": self.author_id,
            "snapshot_tag": self.snapshot_tag,
            "parent_snapshot_id": self.parent_snapshot_id,
            "nodes_count": self.nodes_count,
            "edges_count": self.edges_count,
            "created_at": self.created_at,
        }


class CanvasHistoryTimeTravelEngine:
    """
    Manages snapshot timelines, undo/redo delta stacks, and branching/merging
    for collaborative canvas workspaces.
    """

    def __init__(self, canvas_id: str):
        self.canvas_id = canvas_id
        # Timeline: list of snapshots in chronological order
        self.snapshots: List[CanvasSnapshot] = []
        # Index in timeline of current active snapshot (-1 if empty)
        self.current_cursor: int = -1
        # Named branches: branch_name -> list of snapshot IDs
        self.branches: Dict[str, List[str]] = {"main": []}
        self.active_branch: str = "main"

    def record_snapshot(
        self,
        author_id: str,
        state_data: Dict[str, Any],
        snapshot_tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates a new snapshot and moves current cursor to it.
        If we are in the middle of history (after undo), discards forward redo stack.
        """
        if self.current_cursor < len(self.snapshots) - 1:
            self.snapshots = self.snapshots[: self.current_cursor + 1]

        version_index = len(self.snapshots) + 1
        snapshot_id = f"snap-{uuid.uuid4().hex[:8]}"
        parent_id = (
            self.snapshots[self.current_cursor].id
            if self.current_cursor >= 0
            else None
        )

        snapshot = CanvasSnapshot(
            snapshot_id=snapshot_id,
            canvas_id=self.canvas_id,
            version_index=version_index,
            author_id=author_id,
            state_data=state_data,
            snapshot_tag=snapshot_tag,
            parent_snapshot_id=parent_id,
        )

        self.snapshots.append(snapshot)
        self.current_cursor = len(self.snapshots) - 1
        self.branches[self.active_branch].append(snapshot_id)

        return snapshot.to_dict()

    def undo(self) -> Optional[Dict[str, Any]]:
        """Moves cursor backward one step and returns the restored state."""
        if self.current_cursor <= 0:
            return None
        self.current_cursor -= 1
        return copy.deepcopy(self.snapshots[self.current_cursor].state_data)

    def redo(self) -> Optional[Dict[str, Any]]:
        """Moves cursor forward one step and returns the restored state."""
        if self.current_cursor >= len(self.snapshots) - 1:
            return None
        self.current_cursor += 1
        return copy.deepcopy(self.snapshots[self.current_cursor].state_data)

    def jump_to_version(self, version_index: int) -> Optional[Dict[str, Any]]:
        """Jumps directly to a specific version index."""
        for idx, snap in enumerate(self.snapshots):
            if snap.version_index == version_index:
                self.current_cursor = idx
                return copy.deepcopy(snap.state_data)
        return None

    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """Returns the state data at the current timeline cursor."""
        if self.current_cursor < 0 or not self.snapshots:
            return None
        return copy.deepcopy(self.snapshots[self.current_cursor].state_data)

    def create_branch(
        self, branch_name: str, from_snapshot_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates a new branch from a specific snapshot or current cursor."""
        if branch_name in self.branches:
            raise ValueError(f"Branch '{branch_name}' already exists")

        base_snap_id = from_snapshot_id
        if not base_snap_id and self.current_cursor >= 0:
            base_snap_id = self.snapshots[self.current_cursor].id

        self.branches[branch_name] = [base_snap_id] if base_snap_id else []
        return {
            "branch_name": branch_name,
            "base_snapshot_id": base_snap_id,
            "total_branches": len(self.branches),
        }

    def merge_branch(
        self,
        source_branch: str,
        target_branch: str = "main",
        strategy: str = "theirs",
    ) -> Dict[str, Any]:
        """
        Merges source_branch into target_branch.
        Strategies:
        - 'theirs': overwrite with source branch's latest state
        - 'union': combine nodes & edges from both branches (deduplicating by ID)
        """
        if source_branch not in self.branches:
            raise ValueError(f"Source branch '{source_branch}' not found")
        if target_branch not in self.branches:
            raise ValueError(f"Target branch '{target_branch}' not found")

        source_snap_id = (
            self.branches[source_branch][-1]
            if self.branches[source_branch]
            else None
        )
        target_snap_id = (
            self.branches[target_branch][-1]
            if self.branches[target_branch]
            else None
        )

        source_snap = next(
            (s for s in self.snapshots if s.id == source_snap_id), None
        )
        target_snap = next(
            (s for s in self.snapshots if s.id == target_snap_id), None
        )

        merged_state: Dict[str, Any] = {"nodes": [], "edges": [], "groups": []}

        if strategy == "theirs" and source_snap:
            merged_state = copy.deepcopy(source_snap.state_data)
        elif strategy == "union":
            node_map = {}
            edge_map = {}

            if target_snap:
                for n in target_snap.state_data.get("nodes", []):
                    node_map[n["id"]] = n
                for e in target_snap.state_data.get("edges", []):
                    edge_map[e["id"]] = e

            if source_snap:
                for n in source_snap.state_data.get("nodes", []):
                    node_map[n["id"]] = n
                for e in source_snap.state_data.get("edges", []):
                    edge_map[e["id"]] = e

            merged_state["nodes"] = list(node_map.values())
            merged_state["edges"] = list(edge_map.values())

        # Record merge snapshot onto target branch
        old_branch = self.active_branch
        self.active_branch = target_branch
        merge_record = self.record_snapshot(
            author_id="system_merge_engine",
            state_data=merged_state,
            snapshot_tag=f"merge_{source_branch}_into_{target_branch}",
        )
        self.active_branch = old_branch

        return {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "strategy": strategy,
            "merge_snapshot": merge_record,
            "total_merged_nodes": len(merged_state.get("nodes", [])),
            "total_merged_edges": len(merged_state.get("edges", [])),
        }

    def list_history(self) -> List[Dict[str, Any]]:
        """Lists all snapshots in history timeline."""
        return [s.to_dict() for s in self.snapshots]
