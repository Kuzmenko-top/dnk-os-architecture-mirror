---
name: "dnk-task-graph-manager"
description: "DNK OS Task Graph Manager and Execution Cycle Auto-Reporter"
version: "2.0.0"
category: "general"
assimilated_at: "2026-08-10"
---

# 🌐 Task Graph & Reporting Assimilation Index

Meta-index tracking task node placements and execution cycle auto-reports.

## 📁 Core Specifications

1. **[Architecture Specification](../../docs/tech/specs/DNK-ARCH-004_task-graph-reporting.md)**
   - Plant-scale taxonomy rules (Field -> Sector -> Tree -> Bush -> Flower) and automated Execution Cycle Reports.

## 🧪 Quick Recipes (How to Use This Skill)

### Recipe A: Taxonomical Node Placement

**Goal:** Correctly register a new task node inside the local task forest database or markdown.

- Read node scale from `DNK-ARCH-004_task-graph-reporting.md`.
- Determine correct `plant_scale` (e.g. `flower`) and associate with parent Bush:
  ```json
  {
    "id": "Flower_05_Canvas_Sync",
    "parent_id": "Bush_WebSockets_Canvas_Sync",
    "plant_scale": "flower",
    "status": "pending"
  }
  ```

### Recipe B: Generating Execution Cycle Reports

**Goal:** Auto-generate and format a cycle report when all child flowers are completed.

- Once 100% of flowers under a Bush are marked `completed`, write the report:
  - Place in: `docs/reports/execution_cycles/`
  - See `DNK-ARCH-004_task-graph-reporting.md` for mandatory sections.
