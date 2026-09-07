# --- DNK-MRH-HEADER ---
# mrh_id: "references/occ_structural_graph_merge.md"
# purpose: "Operational Guide & Reference for 3-Way OCC Structural Graph Mutation Resolver in Canvas & Task Forest"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "Antigravity (Mentor) & DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🧬 OCC 3-Way Structural Graph Mutation Resolver

## 📌 Overview
The 3-Way Graph Mutation Resolver (`core/occ_merge.py`, API: `/api/v3/node_tasks/merge`) provides zero-data-loss optimistic concurrency control (OCC) for real-time collaborative editing on spatial canvases and Task Forest DAGs.

When multiple users or autonomous AI agents concurrently mutate graph topology or node metadata, a simple Last-Write-Wins (LWW) strategy drops concurrent edits. 3-Way merge computes structural diffs relative to the common ancestor (`base_state`).

---

## 🏗️ Core Algorithms & Resolution Strategies

### 1. Node Addition, Deletion & Updates
- **Concurrent Additions**: Nodes added in `mine` or `theirs` that did not exist in `base` are merged deterministically.
- **Concurrent Deletions**: If one party deletes a node and the other did not modify it, the node is safely deleted. If one party deleted while the other edited properties, a `CONFLICT_RECORD` is surfaced.

### 2. Node Position Resolution
When both `mine` and `theirs` moved a node from its `base` coordinates:
- **`shift` (Recommended)**: Shifts the incoming node vector by `(+20px, +20px)` to avoid visual overlap while preserving both movements.
- **`last_write_wins`**: Overwrites remote coordinates with local incoming coordinates.
- **`conflict_record`**: Emits a `MergeConflict(conflict_type=ConflictType.POSITION_OVERLAP)` without applying movement.

### 3. Node Metadata Resolution
- **Tags**: Set union (`sorted(list(set(mine_tags) | set(theirs_tags)))`).
- **Descriptions**: If both edited from base, non-destructively concatenates both contents via `\n---\n`.
- **Target Files & Criteria**: Set union of list items, deduplicated and sorted.

### 4. Edge Mutations & DAG Cycle Detection
- Edges added or deleted by either party are merged cleanly.
- **Strict Invariant**: Graph topology must remain a Directed Acyclic Graph (DAG).
- Before applying any new edge, `NodeTaskGraphEngine.detect_cycle_with_new_edge(source, target)` and `core.task_forest.dependencies.DependencyGraph.has_cycle()` validate the resulting graph.
- If a cycle is detected:
  - Conflict marked as `ConflictType.CYCLE_DETECTED`.
  - The offending edge is skipped.
  - The API endpoint returns `HTTP 409 Conflict` with error details.

---

## ⚠️ Critical Pitfalls & Distilled Solutions

### Pitfall 1: Python 3.11+ Enum String Comparison
- In Python 3.11+, `str(Enum.VALUE)` produces `"ConflictType.CYCLE_DETECTED"` rather than `"CYCLE_DETECTED"`.
- **Solution**: Inherit from `(str, Enum)` and explicitly normalize in initializers:
  ```python
  class ConflictType(str, Enum):
      CYCLE_DETECTED = "CYCLE_DETECTED"
      POSITION_OVERLAP = "POSITION_OVERLAP"
  
  # Always normalize string representation
  self.conflict_type = getattr(conflict_type, "value", str(conflict_type)).upper()
  ```

### Pitfall 2: Test Baseline Seed Data Isolation
- Do **not** mutate runtime test baseline files (e.g. `services/dnk_node_tasks/seed_data.py`) to mark tasks completed.
- Existing regression suites (such as `test_stage_transition_gating` in `test_node_tasks_router.py`) rely on tasks like `task-node-system` being `IN_PROGRESS` to verify that dependent tasks (`task-occ-merge`) correctly reject stage advancement with `400 Bad Request`.
- Mutate local notes (`docs/local_notes/tasks_and_ideas/*.md`) and transient persistence instances, not immutable baseline seed data.

### Pitfall 3: Regression Suite Timeout in High-Scale Repos
- When executing `scripts/verify_all.sh` across 5,700+ AST checks and 1,750+ tests, total runtime is ~130–150 seconds.
- Always allocate `timeout: 300` in agent tool calls to avoid false-positive SIGTERM timeouts.
