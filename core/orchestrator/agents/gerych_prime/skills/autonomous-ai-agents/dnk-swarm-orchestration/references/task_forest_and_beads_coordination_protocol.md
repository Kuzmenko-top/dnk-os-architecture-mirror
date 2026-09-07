# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/task_forest_and_beads_coordination_protocol.md"
# purpose: "Operational guidelines for integrating gastownhall/beads (bd) graph issue tracking with DNK OS Task Forest & Swarm"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🌲📿 Task Forest & gastownhall/beads (bd) Distributed Graph Coordination Protocol

## 1. Context & Architectural Role
- **Beads (`bd`)**: Distributed graph issue tracker for AI coding agents powered by Dolt (Git-for-Data). Serves as the distributed transaction, dependency graph, and concurrency arbitration layer.
- **DNK OS Task Forest**: 5-Plant Scale Taxonomy (`Field` -> `Sector` -> `Tree` -> `Bush` -> `Flower`), bottom-up mathematical progress rollups, and Infinite Spatial Canvas HQ (React Flow + Whiteboard Overlay).

## 2. Ontological Mapping

| Task Forest Entity | Beads Entity | Identifier Syntax | Role in Swarm |
| :--- | :--- | :--- | :--- |
| **Field** | Project Workspace | `ws-alpha-001` | Root repository / monorepo workspace boundary |
| **Sector** | Domain Epic Group | Domain Namespace | Architectural subsystem (`core`, `canvas`, `shopify`, `video`) |
| **Tree** | Epic | `bd-a3f8` | Major strategic feature / milestone |
| **Bush** | Task | `bd-a3f8.1` | Deliverable component or multi-file package |
| **Flower** | Sub-task | `bd-a3f8.1.1` | Atomic actionable unit executed by a single specialized agent |

## 3. Swarm Execution Lifecycle with Beads

### Step 1: Topological Work Discovery
Swarm workers do not poll arbitrarily or parse flat markdown TODOs. The dispatcher queries:
```bash
bd ready --json
```
Returns all `Flower` nodes whose blocker dependencies are 100% resolved (`status = closed`).

### Step 2: Atomic Concurrency Claim
To prevent collisions between parallel agents (`gerych_builder`, `dnk_dev_fullstack`, `dnk_shopify`):
```bash
bd update <flower_id> --claim --assignee <agent_name>
```
If two workers attempt to claim the same flower simultaneously, the underlying Dolt transaction enforces single-writer locking and rejects the collision.

### Step 3: Execution & Verification
The agent executes code changes following the Zero-Waste High-Velocity Protocol, running targeted tests and pre-commit checks (`scripts/verify_all.sh`).

### Step 4: Quality Gate & Task Closure
Upon generating signed evidence (`generate_evidence.py`):
```bash
bd close <flower_id>
```
Closing the flower triggers:
1. Unblocking of downstream dependent flowers in the Beads DAG.
2. Bottom-up recalculation of parent progress ($P_{\text{bush}}, P_{\text{tree}}$) via the Rollup Engine.
3. WebSocket event emission to the Spatial Canvas HQ to update node status badges.

## 4. Dolt Branching for Speculative Swarms
For high-risk or exploratory agent tasks:
```bash
dolt branch experiment/<feature_name>
```
If the swarm succeeds and passes adversarial testing, the task branch is merged. If tests fail, the branch is discarded without polluting the canonical project backlog.
