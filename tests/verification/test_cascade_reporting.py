# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "Unit test suite for validating CascadeRollupReporter and its rollup file modification operations."
# canonical_source: true
# alters_files: ["tests/verification/test_cascade_reporting.py"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import os
import sys
import pytest
from pathlib import Path

# Setup paths relative to test file
BASE_DIR = Path(__file__).resolve().parent.parent.parent # Resolve to DNK OS root
sys.path.insert(0, str(BASE_DIR))

from services.dnk_obsidian_task_forest.src.task_graph_reporter import CascadeRollupReporter
from services.dnk_obsidian_task_forest.src.obsidian_task_forest import ObsidianTaskForestParser

VAULT_DIR = "docs/tasks" if Path("docs/tasks").exists() else "docs/tasks"

def test_cascade_rollup_reporter_initialization():
    """Verify that CascadeRollupReporter initializes successfully with default vault paths."""
    reporter = CascadeRollupReporter(vault_path=VAULT_DIR)
    assert reporter.vault_path == VAULT_DIR
    assert len(reporter.nodes) > 0, "Expected preloaded task forest nodes."

def test_cascade_rollup_reporting_execution(tmp_path):
    """Verify that CascadeRollupReporter successfully aggregates child status and updates parent note markdown."""
    # Write a dummy parent node and child note inside temp path
    temp_vault = tmp_path / "tasks"
    temp_vault.mkdir()
    
    # 1. Create subdirs
    (temp_vault / "03_Trees").mkdir()
    (temp_vault / "05_Flowers").mkdir()
    
    # 2. Write tree file
    parent_md = """---
id: tree_999_test_epic
title: "🌳 Test Tree Parent"
plant_scale: tree
status: in_progress
tags:
  - dnk-task-forest
---

# 🌳 Test Tree Parent

## 📋 Опис завдання
Деякий текст.
"""
    parent_file = temp_vault / "03_Trees" / "Tree_999_Test_Epic.md"
    parent_file.write_text(parent_md, encoding="utf-8")
    
    # 3. Write completed flower file
    child_md = """---
id: flower_999_test_task
title: "🌸 Test Flower Child"
plant_scale: flower
parent_id: tree_999_test_epic
status: completed
verification_status: passed
tags:
  - dnk-task-forest
---

# 🌸 Test Flower Child

## 🏁 Чек-лист реалізації
- [x] Створено `core/service_registry.py` та `tests/verification/test_service_registry.py`.
"""
    child_file = temp_vault / "05_Flowers" / "Flower_999_Test_Task.md"
    child_file.write_text(child_md, encoding="utf-8")
    
    # 4. Run CascadeRollupReporter
    reporter = CascadeRollupReporter(vault_path=str(temp_vault))
    updated_count = reporter.generate_cascade_reports()
    
    assert updated_count > 0, "Expected at least one parent file to be updated."
    
    # 5. Read back parent file and verify cascade report block was successfully appended
    updated_parent_content = parent_file.read_text(encoding="utf-8")
    assert "## 📊 Звіт Виконання (Cascade Execution Log)" in updated_parent_content
    assert "[x]" in updated_parent_content
    assert "flower_999_test_task" in updated_parent_content
    assert "service_registry.py" in updated_parent_content
    assert "✅ `PASSED`" in updated_parent_content
