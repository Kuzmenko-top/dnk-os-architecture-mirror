# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture/TASK_FOREST_BEADS_SYNTHESIS.md"
# purpose: "Architectural Synthesis & Integration Analysis: gastownhall/beads (bd) vs DNK OS Task Forest Engine"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-FOREST-BEADS-001"]
# status: "Draft"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🌲🧬 Architectural Synthesis: DNK OS Task Forest & gastownhall/beads (bd)

## 1. Executive Summary & Verdict

**Verdict: 100% Compatible & Synergistic (Tier-1 Match).**

`gastownhall/beads` (`bd`) and DNK OS **Task Forest** solve the same fundamental problem — the breakdown of flat markdown TODOs and linear task queues during long-horizon autonomous multi-agent engineering — from complementary layers:
- **Beads (`bd`)**: Provides a lightweight, headless, distributed graph issue tracker powered by **Dolt** (Git-for-Data), featuring transactional atomic task claiming (`bd update --claim`), deterministic topological dependency traversal (`bd ready`), and cross-agent insight indexing (`bd remember`).
- **DNK OS Task Forest**: Provides an ecological **5-Plant Scale Taxonomy** (`Field` $\to$ `Sector` $\to$ `Tree` $\to$ `Bush` $\to$ `Flower`), bottom-up mathematical progress rollups, an interactive Infinite Spatial Canvas HQ (LOD zoom, time-travel, Whiteboard overlay), and direct integration into the 14-agent Swarm (`gerych_builder`, `dnk_shopify`, `gerych_auditor`).

Merging the two creates an unmatched architecture: **Beads serves as the distributed transaction & sync engine**, while **Task Forest serves as the cognitive model, swarm orchestrator, and spatial visual command center**.

---

## 2. Deep Structural Comparison Matrix

| Dimension | gastownhall/beads (`bd`) | DNK OS Task Forest | Unified Synergy Mode |
| :--- | :--- | :--- | :--- |
| **Underlying Topology** | Directed Acyclic Graph (DAG) with parent-child and blocking edges | 5-Plant Scale Hierarchical Forest DAG (`Field -> Sector -> Tree -> Bush -> Flower`) | Beads hierarchical IDs (`bd-xxx.y.z`) map 1:1 onto `Tree -> Bush -> Flower`. |
| **Storage / Engine** | Dolt (SQL database with Git-like commits, branches, merges) | PostgreSQL 16 + SQLite + Obsidian Markdown Vault (`DNK-STD-0080`) | Beads/Dolt acts as the Git-native decentralized issue database alongside Postgres. |
| **Multi-Agent Coordination** | CLI-based atomic claiming (`bd update <id> --claim`) | Swarm Parallel Dispatcher (`dnk_swarm_parallel`, `dnk_swarm_dispatch`) | Swarm workers claim tasks via Beads to prevent race conditions across parallel agents. |
| **Dependency Resolution** | `bd ready` (returns tasks with 0 pending blockers) | Bottom-Up Rollup Algorithm & Status Cascade Invariant | Orchestrator uses `bd ready` to feed unblocked `Flowers` directly into the agent queue. |
| **User Interface** | CLI-centric (`bd prime`, `bd show`, `bd list`) | React Flow Spatial Canvas HQ, Whiteboard Overlay, LOD Zoom (0.2x–2.5x) | Spatial Canvas visualizes the Beads graph in real time; visual edits sync back to Beads. |
| **Memory / Context** | `bd remember` (project-scoped insights) | SCONES L1/L2/L3 Memory Engine (`scones_memory.py`) | Federated memory: micro-task insights in Beads; macro patterns & ADRs in SCONES. |
| **Audit & Quality Gate** | Dolt commit history & audit trail | Master Quality Gate (`verify_all.sh`, Adversarial Gate, Evidence JSON) | Closing a task in Beads (`bd close`) requires verified Master Quality Gate output. |

---

## 3. Ontological Mapping: Beads IDs ⟷ 5-Plant Scale

Beads uses hierarchical IDs:
- Epic: `bd-a3f8`
- Task: `bd-a3f8.1`
- Sub-task: `bd-a3f8.1.1`

In DNK OS Task Forest (`DNK-SPEC-TASK-FOREST-SPATIAL-HQ-005.md`):
```
🌾 Field (Workspace / Repository Scope, e.g. ws-alpha-001)
  └── 🏞️ Sector (Domain Boundary: Core / Canvas / Ecom / Media)
        └── 🌳 Tree  <=======> Beads Epic (`bd-a3f8`)
              └── 🌿 Bush <=======> Beads Task (`bd-a3f8.1`)
                    └── 🌸 Flower <=======> Beads Sub-task (`bd-a3f8.1.1`)
```

When an agent defines a new `Tree` on the Spatial Canvas, a root epic is registered in Beads. As the subagent decomposes work via `dnk_decompose_task_dna`, Beads creates child issues with deterministic blocker relationships (`bd dep add <child> <parent>`).

---

## 4. Key Architectural Synergies

### 4.1. Race-Free Swarm Concurrency (`bd update --claim`)
In multi-agent systems with 4–14 active workers (`dnk_dev_fullstack`, `gerych_builder`, `dnk_shopify`, `gerych_auditor`), task collisions are a common failure mode. 
- With Beads, when multiple subagents poll for work, they execute an atomic claim:
  ```bash
  bd update bd-4c2a.1.2 --claim --assignee gerych_builder
  ```
- If another agent attempts to claim the same sub-task, Beads rejects it with a conflict, guaranteeing strict zero-waste separation of concerns.

### 4.2. Instant Topological Scheduling via `bd ready`
Instead of complex polling algorithms in Python, the swarm orchestrator simply queries:
```bash
bd ready --json
```
This returns exactly the set of `Flowers` whose upstream prerequisites have completed (`status = closed`). The orchestrator immediately maps these to available specialized agents in `dnk_swarm_parallel`.

### 4.3. Dolt Branching for Speculative / Sandbox Agent Runs
Because Beads runs on Dolt:
- An agent swarm can branch the task database (`dolt branch feat/canvas-stitch`) just like git code.
- If a speculative swarm run fails adversarial tests, the task branch is discarded without polluting the main project backlog.
- If it succeeds, the task state is cleanly merged back to main with full commit-level audit history.

### 4.4. Two-Way Spatial Canvas Sync
- **Headless $\to$ Visual**: Changes committed by CLI agents via `bd` emit WebSocket events to the FastAPI backend, updating React Flow node positions, progress rings, and status badges on the Spatial Canvas.
- **Visual $\to$ Headless**: A user dragging a node, creating an edge, or sketching an arrow on the Whiteboard Overlay mutates the underlying Beads graph via the Task Forest API bridge.

---

## 5. Unified Integration Blueprint

```
+-------------------------------------------------------------------------+
|                    DNK OS SPATIAL CANVAS HQ                             |
|  - React Flow Nodes (Trees / Bushes / Flowers)                          |
|  - Whiteboard Overlay (Sketches & Annotations)                          |
|  - Stitch Prompt Dock (Natural Language -> Task Node generation)        |
+------------------------------------+------------------------------------+
                                     | 
                          REST API / WebSockets
                                     v
+------------------------------------+------------------------------------+
|                TASK FOREST DUAL-SYNC ENGINE (FastAPI)                   |
|  - Bottom-Up Progress Rollup (Mathematical Cascade)                     |
|  - LOD Virtualizer & Event Sourcing History                             |
|  - SCONES Knowledge Integration                                         |
+-----------------+-----------------------------------+-------------------+
                  |                                   |
                  v                                   v
+---------------------------------+   +-----------------------------------+
|      BEADS ENGINE (bd / Dolt)   |   |        SWARM WORKERS (x14)        |
|  - Transactional DAG Database   |   |  - gerych_builder                 |
|  - Atomic Claiming & Locking    |<--|  - dnk_dev_fullstack              |
|  - `bd ready` Work Queue        |   |  - dnk_shopify                    |
|  - Branching & Diffing          |   |  - gerych_auditor                 |
+---------------------------------+   +-----------------------------------+
```

---

## 6. Recommended Next Steps for DNK OS

1. **Phase 1: Beads Adapter Layer (`core/adapters/beads_adapter.py`)**:
   Implement a Python wrapper around the `bd` CLI / Dolt engine to translate between `TaskForestNode` and Beads issue schemas.
2. **Phase 2: Swarm Integration**:
   Update `dnk_swarm_engine.py` to check `bd ready` before dispatching tasks and require `--claim` during agent execution.
3. **Phase 3: Spatial Canvas Bridge**:
   Connect the Stitch Prompt Dock directly to Beads issue creation so typing a prompt on canvas immediately mints trackable, dependency-linked Beads tasks.
