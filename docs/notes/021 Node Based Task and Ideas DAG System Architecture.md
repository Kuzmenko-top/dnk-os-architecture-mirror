---
title: "021 Node Based Task & Ideas DAG System Architecture"
created: 2026-09-05
tags:
  - architecture
  - dnk-os
  - task-dag
  - ideas-system
  - react-flow
  - fastapi
  - obsidian-sync
aliases:
  - Node Task DAG System
  - DNK Ideas & Task Graph
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/021 Node Based Task and Ideas DAG System Architecture.md"
purpose: "Architecture specification, data models, and workflow for DNK OS Node Based Task & Ideas DAG System"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym"
--- END DNK-MRH-HEADER -->

# 🧬 021 Node Based Task & Ideas DAG System Architecture

## 1. Executive Summary & Objective

The **Node Based Task & Ideas System** provides an interactive, directed acyclic graph (DAG) workflow engine purpose-built for the ongoing development, architectural iteration, and autonomous execution of **DNK OS**.

It unifies:
1. **Ideation & Brainstorming** (`idea` nodes)
2. **Epics & Major Architectural Workstreams** (`epic` nodes)
3. **Actionable Engineering Tasks** (`task` nodes)
4. **Atomic Execution Slices** (`slice` nodes)
5. **Quality & Security Verification Gates** (`gate` nodes)

All nodes are interconnected with typed dependency edges (`depends_on`, `blocks`, `spawns_from`, `relates_to`), enforcing automated stage transition gating, cycle prevention, swarm agent execution, and bidirectional Obsidian Markdown synchronization.

---

## 2. Core Architecture & Component Stack

```
+-----------------------------------------------------------------------------------+
|                              DNK OS Web UI (Next.js 14)                           |
|  - @xyflow/react DAG Canvas (/tasks)                                              |
|  - CustomTaskNode (visual badges, stage pills, blocked alerts, progress bars)     |
|  - CustomDependencyEdge (bezier paths, satisfaction status, cycle safety)         |
|  - NodeTaskDetailDrawer (stage transition stepper, Swarm Agent dispatcher)        |
|  - CreateNodeModal & CreateEdgeModal (interactive CRUD)                           |
|  - Zustand Store (apps/web/store/nodeTasksStore.ts)                               |
+------------------------------------------+----------------------------------------+
                                           | HTTP Proxy /api/v3/node_tasks/*
                                           v
+-----------------------------------------------------------------------------------+
|                           FastAPI Backend (apps/api)                              |
|  - Router: apps/api/routers/node_tasks_router.py                                  |
|  - Endpoints: /graph, /node, /edge, /stage_transition, /convert_idea,             |
|               /sync_obsidian, /reset_baseline, /execute_agent                     |
+------------------------------------------+----------------------------------------+
                                           | In-Memory Engine & Validations
                                           v
+-----------------------------------------------------------------------------------+
|                        Domain Engine (services/dnk_node_tasks)                    |
|  - models.py: Pydantic v2 schemas (TaskNode, TaskEdge, GraphStats)                |
|  - graph_engine.py: DAG validation, Kahn's topological sort, blocker computation  |
|  - persistence.py: Atomic JSON I/O & Obsidian Markdown sync (./docs/notes/)       |
|  - seed_data.py: Baseline seed graph of DNK OS architectural milestones           |
+-----------------------------------------------------------------------------------+
```

---

## 3. Data Models & Lifecycle

### Node Types
- `idea`: Early-stage concepts and architectural hypotheses. Can be converted to tasks/epics via one click.
- `epic`: High-level initiatives containing multiple interconnected tasks.
- `task`: Standard engineering work item with defined acceptance criteria and progress tracking.
- `slice`: Atomic execution slice bound by ≤ 25 tool calls per turn (MASE protocol).
- `gate`: Quality and security verification gate (Auditor review, test suite, pre-commit barrier).

### Execution Stages & Gating Rules
The system enforces a strict state machine:
```
[ideation] ──> [architecture] ──> [ready] ──> [in_progress] ──> [testing] ──> [completed]
                                      │
                                [blocked]
```

**Stage Gating Invariant**:
- A node cannot transition to `in_progress` or `completed` if any incoming prerequisite node connected via a `depends_on` or `blocks` edge is not yet `completed` (or 100% progress).
- Attempts to transition a blocked node return HTTP 400 with a descriptive list of blocking node titles.
- Transition can be forced with explicit bypass parameter (`force=true`) when human oversight mandates an override.

---

## 4. Obsidian Vault Synchronization

All nodes and dependency relations are automatically synced into `./docs/notes/tasks_and_ideas/`:
- Each node produces a clean Markdown note with YAML frontmatter, MRH header, execution stage badge, and `[[wikilinks]]` to prerequisite and dependent nodes.
- An aggregated index `000_DNK_TASK_AND_IDEAS_INDEX.md` is maintained with summary tables by type and stage.

---

## 5. Verification & Test Suite

The engine is certified green across 12 comprehensive unit and integration tests:
- `tests/core/test_node_task_graph_engine.py`: 6 tests (DAG creation, cycle detection, gating, idea conversion, topological sort, persistence).
- `tests/verification/test_node_tasks_router.py`: 6 tests (REST API endpoints, error handling, stage transition gating, swarm dispatch).

## 6. Related Links
- [[000 DNK HUB Index]]
- [[004 Gerych Task Specification Standard & Zero-Waste Protocol v2.5]]
- [[016 Unified Swarm Control Plane Architecture and Engine Consolidation]]
