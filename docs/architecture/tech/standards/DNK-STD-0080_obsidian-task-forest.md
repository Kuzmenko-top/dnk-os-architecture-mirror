# 🛡️ System Standard: Obsidian Task Forest Management (DNK-STD-0080)
## Title: Obsidian Markdown Task Formatting, Metadata Standards & Auto-Synchronization
## Status: Active | Version: 2.0.0 | Author: Maxim | License: MIT

This standard establishes the exact format, filename prefixes, YAML frontmatter schemas, and CLI progress synchronization triggers for representing the Task Forest in Obsidian Markdown files.

### 1. Naming & Filesystem Layout Conventions
All task files live under `docs/tasks/` and MUST use the designated prefix naming style:
1. **🌾 Project Field (`project_field`)**:
   - Path: `docs/tasks/Field_{project_id}.md`
   - Metadata: `type: project_field`, `plant_scale: field`, `tags: [dnk-task-forest, dnk-project-field]`
2. **🏞️ Sector Zone (`sector_zone`)**:
   - Path: `docs/tasks/Sector_{sector_id}.md`
   - Metadata: `type: sector_zone`, `plant_scale: sector`, `project_id: {project_id}`, `tags: [dnk-task-forest, dnk-sector-zone]`
3. **🌳 Epic Tree (`epic_tree`)**:
   - Path: `docs/tasks/Tree_{tree_id}.md`
   - Metadata: `type: epic_tree`, `plant_scale: tree`, `parent_id: {sector_id}`, `tags: [dnk-task-forest, dnk-epic-tree]`
4. **🌿 Feature Bush (`feature_bush`)**:
   - Path: `docs/tasks/Bush_{bush_id}.md`
   - Metadata: `type: feature_bush`, `plant_scale: bush`, `parent_id: {tree_id}`, `tags: [dnk-task-forest, dnk-feature-bush]`
5. **🌱 Task Flower (`task_flower`)**:
   - Path: `docs/tasks/Flower_{flower_id}.md`
   - Metadata: `type: task_flower`, `plant_scale: flower`, `parent_id: {bush_id}`, `status: completed|in_progress|pending`, `tags: [dnk-task-forest, dnk-task-flower]`

### 2. Status Progression & % Progress Synchronization
When task states are updated:
- Update status in YAML: `status: completed`.
- Trigger the automatic progress recalculation engine from your script or CLI:
  ```bash
  uv run python -m services.dnk_obsidian_task_forest.cli --sync
  ```
- This parses all child files, computes progress statistics, and updates the parent `Feature Bush` and `Epic Tree` completeness percentages in a bottom-up cascade.
