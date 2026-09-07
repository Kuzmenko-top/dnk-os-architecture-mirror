# --- DNK-MRH-HEADER ---
# mrh_id: "docs/notes/tasks_and_ideas/tasks/task-node-system.md"
# purpose: "Task & Idea Node: Node Based TASK & Ideas System with DAG Dependencies"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

---
node_id: task-node-system
title: "Node Based TASK & Ideas System with DAG Dependencies"
node_type: task
stage: in_progress
status: in_progress
progress: 85.0
priority: critical
assigned_agent: gerych_builder
target_module: services/dnk_node_tasks
is_blocked: false
tags: [task_graph, ideas, dag, orchestration]
---

# Node Based TASK & Ideas System with DAG Dependencies

**Type**: `TASK` | **Stage**: `in_progress` | **Status**: `in_progress` | **Progress**: `85.0%`

### Description
Interactive node-based task and ideas engine with stage lifecycle gating and Obsidian vault sync.

### Target Module & Files
**Module**: `services/dnk_node_tasks`
- `services/dnk_node_tasks/models.py`
- `services/dnk_node_tasks/graph_engine.py`
- `apps/api/routers/node_tasks_router.py`
- `apps/web/app/tasks/page.tsx`

### Acceptance Criteria (Definition of Done)
- [ ] Pydantic models for Ideas, Tasks, Slices, Gates
- [ ] Cycle detection and topological sorting
- [ ] Blocked status computed dynamically from dependencies
- [ ] Full interactive React Flow UI on /tasks

### Upstream Dependencies (Prerequisites)
- **parent_of** from [[epic-canvas-v2]] (Node task system is child component of Canvas v2)
- **validates** from [[gate-canvas-qa]] (Gate certifies task-node-system readiness)

### Downstream Dependents
- **depends_on** to [[task-occ-merge]] (OCC Merge depends on Node Task System schema stabilization)
- **depends_on** to [[gate-canvas-qa]] (Task must be implemented before Canvas QA gate can complete)

> Node Position on Canvas: `x=880.0, y=100.0`
> Backlink to Master Index: [[000_DNK_TASK_AND_IDEAS_INDEX]]
