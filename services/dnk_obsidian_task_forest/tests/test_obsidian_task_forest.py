# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_obsidian_task_forest/tests/test_obsidian_task_forest.py"
# purpose: "Unit tests for Obsidian Task Forest Engine (Plant Hierarchy Scale & Bottom-Up Rollup)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import tempfile
import pytest
from services.dnk_obsidian_task_forest.src.obsidian_task_forest import (
    PlantNode,
    ObsidianTaskForestParser,
)


def test_plant_node_bottom_up_rollup():
    # 🌾 Field Root
    field_root = PlantNode(id="field_1", title="DNK Ecom Store", plant_scale="field")

    # 🏞️ Sector Zone
    sector = PlantNode(id="sector_ui", title="UI & Design Sector", plant_scale="sector")
    field_root.add_child(sector)

    # 🌳 Epic Tree
    tree = PlantNode(id="tree_builder", title="Open Design System Epic", plant_scale="tree")
    sector.add_child(tree)

    # 🌿 Feature Bushes
    bush1 = PlantNode(id="bush_hero", title="Hero Section Feature", plant_scale="bush", status="completed")
    bush2 = PlantNode(id="bush_cart", title="High-Tech Cart Drawer", plant_scale="bush", status="in_progress", progress=50.0)
    tree.add_child(bush1)
    tree.add_child(bush2)

    # Check Bottom-Up Rollup calculation
    assert bush1.get_completion_percentage() == 100.0
    assert bush2.get_completion_percentage() == 50.0
    # Tree rollup: avg(100, 50) = 75.0%
    assert tree.get_completion_percentage() == 75.0
    # Field root rollup propagates up: 75.0%
    assert field_root.get_completion_percentage() == 75.0


def test_plant_node_mermaid_graph_bt():
    field = PlantNode(id="field_test", title="Test Field", plant_scale="field")
    tree = PlantNode(id="tree_test", title="Test Tree", plant_scale="tree", status="in_progress", progress=40.0)
    field.add_child(tree)

    mermaid = field.to_mermaid(direction="BT")
    assert "graph BT" in mermaid
    assert "field_test" in mermaid
    assert "tree_test" in mermaid
    assert "-->" in mermaid


def test_obsidian_vault_scanner():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create dummy Markdown files
        field_file = os.path.join(tmp_dir, "Project_Field.md")
        tree_file = os.path.join(tmp_dir, "Epic_Tree.md")

        with open(field_file, "w", encoding="utf-8") as f:
            f.write("""---
id: field_main
title: Main Project Field
plant_scale: field
status: in_progress
tags:
  - dnk-task-forest
---
# Main Project Field
""")

        with open(tree_file, "w", encoding="utf-8") as f:
            f.write("""---
id: tree_backend
title: Core Backend Engine
plant_scale: tree
status: completed
parent_id: field_main
tags:
  - dnk-task-forest
---
# Core Backend Engine
""")

        parser = ObsidianTaskForestParser(tmp_dir)
        nodes = parser.scan_vault()

        assert "field_main" in nodes
        assert "tree_backend" in nodes
        assert len(nodes["field_main"].children) == 1
        assert nodes["field_main"].children[0].id == "tree_backend"
        assert nodes["field_main"].get_completion_percentage() == 100.0
