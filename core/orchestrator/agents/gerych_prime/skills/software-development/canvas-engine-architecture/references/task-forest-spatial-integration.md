# --- DNK-MRH-HEADER ---
# mrh_id: "references/task-forest-spatial-integration.md"
# purpose: "Technical specification and architectural pattern for 5-Level Plant Scale Task Forest in Spatial Canvas HQ."
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🌲 Task Forest Spatial Integration: 5-Level Plant Scale Taxonomy & Bottom-Up Rollup

This reference guide documents the architectural blueprint for integrating the **Task Forest (Ліс Задач)** taxonomic spatial engine into the **Infinite Spatial Canvas HQ** system.

---

## 🌾 1. The 5-Level Plant Scale Taxonomy
Tasks are structured hierarchically using biological entities representing scale and granularity:

1. **🌾 Field (Поле)**: The master container or boundary (e.g., `DNK_HUB Master HQ`).
2. **🏞️ Sector (Сектор)**: Major modules or domains within the field (e.g., `Spatial Studio & Infinite Canvas`).
3. **🌳 Tree (Дерево)**: Core architectural epics or major feature streams.
4. **🌿 Bush (Кущ)**: Sub-features, sub-modules, or distinct milestones.
5. **🌸 Flower (Квітка)**: Leaf nodes, atomic tasks, and pull-request/commit level actions.

---

## ⚡ 2. Bottom-Up Rollup Algorithm
Progress calculation propagates recursively from leaf nodes (🌸 Flowers) up to the master boundary (🌾 Field):

- **Atomic Leaf (🌸 Flower)**: Has a base progress `[0 - 100]`.
- **Parent Node Progress**: Calculated as the mathematical average of the progress of all its direct children.
- **Propagation Hook**:
  ```python
  def calculate_node_progress(node, all_nodes):
      children = [n for n in all_nodes if n.parent_id == node.id]
      if not children:
          return node.progress
      
      # Recursively compute children's progress first
      total_progress = sum(calculate_node_progress(c, all_nodes) for c in children)
      return round(total_progress / len(children), 1)
  ```
- **Cascade Trigger**: Any mutation to a node's progress or status (`todo`, `in_progress`, `completed`, `cancelled`) must immediately trigger a bottom-up recalculation of parent paths.

---

## 🎨 3. Spatial Double-Panel Inspector UI Pattern
To keep the spatial canvas clutter-free while providing deep atomic context, a double-panel drawer pattern is used:

1. **Left Panel (Overview & Navigator)**:
   - Tree navigation mapping the 5-plant taxonomy.
   - Interactive progress-bars with status-themed colors:
     - `bg-emerald-600` (Completed / Active 🟢)
     - `bg-amber-500` (In Progress 🟡)
     - `bg-slate-700` (To Do / Draft ⚪)
2. **Right Sliding Panel (Genetic Node Inspector)**:
   - Activates upon selecting a node in the tree.
   - Displays metadata (`assigned_agent`, `author`).
   - Renders a raw JSON/DTO schema box for technical audit.
   - Integrates live status-mutation inputs triggering instant canvas state updates.
   - Renders simulated git diff / verification report for pull-request tasks.

---

## 🕰️ 4. Time-Travel Scrubber (Mutation Log)
Every node mutation registers a snapshot of the entire Forest tree inside a persistent log with timestamps:

```json
{
  "timestamp": "2026-09-02T15:30:00Z",
  "mutated_node_id": "flw-12345",
  "mutation_details": { "status": "completed", "progress": 100 },
  "snapshot": { ... }
}
```

- **Scrubber UI**: A continuous timeline slider at the bottom of the drawer.
- **Behavior**: Sliding changes the current index, swapping the rendered canvas tree with historical snapshots to allow immediate rollback visualization.
