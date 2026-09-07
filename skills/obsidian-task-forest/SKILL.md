---
name: "obsidian-task-forest"
description: "Obsidian Task Forest Markdown formatting, YAML headers, and bottom-up progress synchronization."
version: "2.0.0"
category: "general"
assimilated_at: "2026-08-10"
---

# 🌐 Obsidian Task Forest Index

Meta-index tracking Obsidian-based task layouts, naming conventions, and progress syncs.

## 📁 Core Specifications

1. **[System Standard](../../docs/tech/standards/DNK-STD-0080_obsidian-task-forest.md)**
   - Naming conventions (`Field_`, `Sector_`, `Tree_`, `Bush_`, `Flower_`), YAML schema, and bottom-up synchronization command.

## 🧪 Quick Recipes (How to Use This Skill)

### Recipe A: Formatting a Task Flower Note

**Goal:** Create a correctly formatted Obsidian task markdown file under `docs/tasks/`.

- Format the file per `DNK-STD-0080_obsidian-task-forest.md`:
  ```markdown
  ---
  mrh_id: "Flower_09_Canvas"
  type: "task_flower"
  plant_scale: "flower"
  parent_id: "Bush_WebSockets_Canvas_Sync"
  status: "pending"
  tags: [dnk-task-forest, dnk-task-flower]
  ---
  
  # 🌱 Task Flower: Implementing Canvas WS Sync
  [Description goes here]
  ```

### Recipe B: Running Progress Synchronizer CLI

**Goal:** Force synchronization and update all parent trees/bushes percentages.

- Run standard command defined in `DNK-STD-0080_obsidian-task-forest.md`:
  ```bash
  uv run python -m services.dnk_obsidian_task_forest.cli --sync
  ```
