# --- DNK-MRH-HEADER ---
# mrh_id: "docs/task-forest/ARCHITECTURE.md"
# purpose: "System architecture, graph invariants, and lifecycle documentation for DNK Task Forest."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🌲 DNK OS Task Forest System Architecture

## 1. Overview
The **DNK Task Forest** is a graph-driven task and ideation management engine that combines DAG-based dependency tracking, strict stage lifecycle gates, dynamic React Flow canvas visualization, and bidirectional synchronization with Obsidian Vaults.

```
       [ Obsidian Vault (Markdown + Frontmatter + [[wikilinks]]) ]
                                 ▲
                                 │ Bidirectional Sync
                                 ▼
                     [ TaskForest Engine (Python) ]
                     ├── DependencyGraph (Cycle DFS & Topo Sort)
                     ├── StageManager (Backlog → Done Gate)
                     └── Storage Persistence (forest.json)
                                 ▲
                                 │ REST / WebSocket / State
                                 ▼
                    [ Visual TaskForest Canvas ]
                     ├── React Flow Canvas UI
                     └── Zustand State Store (taskForestStore)
```

---

## 2. Node Types & Models

| Node Type | Icon | Purpose | Key Metadata Fields |
|:---|:---:|:---|:---|
| `task` | 📋 | Standard executable work item | `tags`, `dependencies`, `priority` |
| `idea` | 💡 | Proposed feature or hypothesis | `votes`, `status` (`proposed`, `approved`, `rejected`) |
| `goal` | 🎯 | Strategic milestone / KPI | `milestone`, `progress` (0.0 – 1.0) |
| `bug` | 🐛 | Defect or regression report | `severity`, `reported_by`, `fixed_in_version` |
| `documentation` | 📚 | Documentation unit / spec | `doc_type`, `version` |

---

## 3. Execution Stages & Lifecycle Transitions

```
[ BACKLOG ] ───► [ PLANNED ] ───► [ IN_PROGRESS ] ───► [ REVIEW ] ───► [ DONE ]
     ▲                │                  │                 │
     │                ▼                  ▼                 │
     └────────────────┴──────────────────┴─────────────────┘
                   (Deprioritize / Reopen)
```

### Transition Invariants:
1. **Backlog** can only transition to **Planned**.
2. **Planned** can transition to **In Progress** or return to **Backlog**.
3. **In Progress** can transition to **Review** or return to **Backlog**.
4. **Review** can transition to **Done** or return to **In Progress** (for rework).
5. **Done** is a terminal state.
6. **Dependency Gate**: A node cannot advance into `IN_PROGRESS`, `REVIEW`, or `DONE` if any of its upstream dependencies are not in the `DONE` stage.

---

## 4. Dependency Graph & Cycle Detection
- Directed edge `A -> B` specifies that **A depends on B** (B blocks A).
- Cycle detection via Depth-First Search with recursion call stacks prevents deadlocks before committing edges.
- Topological sorting (`topological_sort()`) resolves valid execution orders where blocking prerequisites execute first.

---

## 5. Obsidian Vault Integration
- Notes are stored in `./docs/notes/task_forest/` with YAML frontmatter containing `id`, `type`, `stage`, `priority`, `tags`, and `dependencies`.
- Cross-node dependencies are rendered as native Obsidian `[[Title]]` or `[[ID]]` wikilinks.
- `ObsidianTaskForestSync.sync()` maintains continuous two-way consistency between the file-based knowledge base and the live graph state.

---

## 6. Frontend Canvas (React Flow + Zustand)
- Interactive drag-and-drop canvas supporting node positioning, color-coded stage/type badges, and dependency edge drawing.
- State is managed via `taskForestStore.ts` with instant undo/redo, stage transitions, and persistence sync.
