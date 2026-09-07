# Optimistic Concurrency Control (OCC) Engine Reference Architecture

## Overview
The OCC Engine manages concurrent graph/state edits in collaborative workspaces through a 3-way structural comparison between `base` (ancestor state), `current` (server/remote state), and `incoming` (client/local state).

---

## 1. 3-Way Structural Diff (`compute_3way_diff`)
Compares `base_state`, `current_state`, and `incoming_state` across nodes, edges, and graph metadata.
- **Remote Changes:** Modifications between `base` and `current`.
- **Local Changes:** Modifications between `base` and `incoming`.
- **Conflict Determination:** `can_auto_merge` is `True` only when remote and local changes affect disjoint elements or non-conflicting properties.

---

## 2. Auto-Merge Mechanics (`merge_graph_state`)
When `can_auto_merge` is `True`, the engine constructs the merged state automatically:
- **Node Additions:** Nodes present in `incoming` but missing in `base` and `current` are appended.
- **Node Attribute Merges:** Fine-grained property merges when `current` and `incoming` modify different attributes of the same node ID (e.g., `current` updates `x` coordinate while `incoming` updates `label`).
- **Edge & Metadata Merges:** Non-overlapping edge additions/deletions and metadata field updates are combined into `merged_state`.

---

## 3. Conflict Detection (`ConflictDetail` & `ConflictType`)
Triggers explicit `ConflictType` classifications when operations collide:
- **NODE_MODIFICATION_CONFLICT:** Both `current` and `incoming` modify the same attribute of a node with different values.
- **DELETE_VS_MODIFY_CONFLICT:** One side deleted a node/edge while the other modified it.
- **PROPERTY_CONFLICT:** Top-level graph metadata/properties modified concurrently with conflicting values.

---

## 4. Manual Conflict Resolution (`resolve_conflicts_manually`)
When auto-merge is impossible, the client provides a resolution map:
```python
resolutions = {
    "title": "use_incoming",
    "node-1": "use_current",
    "node-2": {"action": "custom", "value": {"id": "node-2", "label": "Merged Value"}}
}
```
Strategies:
- `use_incoming`: Accept client/local change.
- `use_current`: Retain server/remote state.
- `use_base`: Revert to baseline state.
- `custom`: Explicitly supply resolved dictionary payload.

---

## 5. Version Bumping (`bump_version`)
Atomic version incrementing after successful merge or manual resolution:
- Calculates `new_version = max(current_version, base_version) + 1`.
- Updates state version field and returns the new version index.
