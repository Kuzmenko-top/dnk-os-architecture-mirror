# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture/tech/specs/DNK-SPEC-TASK-FOREST-SPATIAL-HQ-005.md"
# purpose: "Architecture Blueprint: Task Forest 5-Plant Scale Engine & Spatial Canvas HQ Integration"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🌲 Architectural Specification: Task Forest 5-Plant Scale Engine

## 1. Executive Summary & Paradigm
The **Task Forest** system is an ecological, hierarchical task management paradigm designed for hyper-complex ecosystems and autonomous multi-agent swarms. It replaces flat issue trackers with a **5-Plant Scale Taxonomy**:

$$\text{🌾 Field} \longrightarrow \text{🏞️ Sector} \longrightarrow \text{🌳 Tree} \longrightarrow \text{🌿 Bush} \longrightarrow \text{🌸 Flower}$$

Every leaf unit (Flower) rolls up its completion weight and execution status to parent structures recursively via a **Bottom-Up Rollup Engine**.

---

## 2. Mathematical Formalization & Rollup Algorithm

### 2.1 Weight and Progress Attribution
Let node $u$ have a set of children $C(u) = \{v_1, v_2, \dots, v_k\}$.
Each child $v_i$ has a progress value $P(v_i) \in [0, 100]$ and an assigned execution weight $W(v_i) > 0$. If weights are unassigned, uniform distribution applies ($W(v_i) = 1$).

The rollup progress $P(u)$ is defined as:
$$P(u) = \frac{\sum_{v \in C(u)} W(v) \cdot P(v)}{\sum_{v \in C(u)} W(v)}$$

For leaf nodes (🌸 Flowers):
$$P(v_{\text{flower}}) = \begin{cases} 
100 & \text{if } \text{status} = \text{completed} \\
50 & \text{if } \text{status} = \text{in\_progress} \\
0 & \text{if } \text{status} \in \{\text{pending}, \text{todo}\} \\
\text{invariant} & \text{if } \text{status} = \text{cancelled (excluded from denominator)}
\end{cases}$$

### 2.2 Status Cascade Invariant
The state $S(u)$ of parent node $u$ is strictly determined by its children $C(u)$:
- **completed**: $\forall v \in C(u), S(v) = \text{completed}$ (or $P(u) = 100$)
- **in_progress**: $\exists v \in C(u) \text{ with } S(v) \in \{\text{in\_progress}, \text{completed}\} \land P(u) < 100$
- **pending**: $\forall v \in C(u), S(v) = \text{pending}$

---

## 3. Distributed Architecture & Component Topology

```
+-----------------------------------------------------------------------------------------+
|                                    SPATIAL CANVAS HQ                                    |
|  +--------------------------+  +-------------------------------+  +-------------------+  |
|  | StitchTaskForestDrawer   |  | Canvas Node LOD (Level-of-Det)|  | Time-Travel Rail  |  |
|  | - 5-Level Visual Tree    |  | - Zoom 0.2x: Field/Sector     |  | - Scrubber        |  |
|  | - Genetic DTO Inspector  |  | - Zoom 1.0x: Tree/Bush        |  | - Delta Snapshots |  |
|  | - Status Mutator Form    |  | - Zoom 2.5x: Flowers & Diff   |  | - Rewind/Replay   |  |
|  +------------+-------------+  +---------------+---------------+  +---------+---------+  |
+---------------|--------------------------------|----------------------------|------------+
                |                                |                            |
                +--------------------------------+----------------------------+
                                                 | REST v3 & WebSocket
                                                 v
+-----------------------------------------------------------------------------------------+
|                                   FASTAPI ROUTER V3                                     |
|  +-----------------------------------------------------------------------------------+  |
|  | `GET /api/v3/task_forest/graph`              -> Hierarchical Forest DAG           |  |
|  | `POST /api/v3/task_forest/node/mutate`       -> Bottom-Up Cascade & Event Record  |  |
|  | `GET /api/v3/task_forest/evolution_history`  -> Immutable Event Store             |  |
|  +-----------------------------------------------------------------------------------+  |
+----------------------------------------+------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------------+
|                               PERSISTENCE & SYNC LAYER                                  |
|  +------------------------+  +--------------------------+  +-------------------------+  |
|  | SQLite / Memory Cache  |  | Obsidian Markdown Vault  |  | SCONES Knowledge Base   |  |
|  | (Fast Query & Scrubber)|  | (`DNK-STD-0080` Sync)    |  | (Memory & Multi-Agent)  |  |
|  +------------------------+  +--------------------------+  +-------------------------+  |
+-----------------------------------------------------------------------------------------+
```

---

## 4. Key Implementation Invariants

1. **Deterministic Dependency Resolution (DAG)**:
   A `Flower` cannot be attached to a `Tree` directly; the schema strictly enforces `Flower` $\to$ `Bush` $\to$ `Tree` $\to$ `Sector` $\to$ `Field`.
2. **Atomic Rollup Invariant**:
   Whenever a mutation occurs at level $k$, parent levels $k-1 \dots 1$ MUST be recalculated in a single atomic transaction before emitting events to clients.
3. **Event Sourcing & Time-Travel**:
   Mutations do not overwrite history blindly. Every mutation generates an `EvolutionSnapshot` consisting of `(timestamp, trigger_node_id, mutation_diff, aggregate_progress)`.
4. **Zero-Waste Spatial Rendering**:
   On the Infinite Spatial Canvas, nodes are virtualized. Sub-trees are rendered using Level-of-Detail (LOD) thresholds to guarantee 60 FPS on large task forests.
