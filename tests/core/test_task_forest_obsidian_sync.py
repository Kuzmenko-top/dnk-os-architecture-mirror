# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_task_forest_obsidian_sync.py"
# purpose: "Regression tests for ObsidianTaskForestSync verifying YAML frontmatter, HTML MRH header, and wikilinks."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import yaml
from pathlib import Path
from core.task_forest.models import NodeType, ExecutionStage, Priority
from core.task_forest.forest import TaskForest
from core.obsidian.task_forest_sync import ObsidianTaskForestSync


def test_task_forest_obsidian_export_frontmatter_and_wikilinks(tmp_path):
    storage_file = tmp_path / "forest.json"
    vault_dir = tmp_path / "docs" / "notes" / "task_forest"
    vault_dir.mkdir(parents=True, exist_ok=True)

    forest = TaskForest(storage_path=str(storage_file))

    # 1. Create 3 nodes: Goal (Epic level) -> Task 1 -> Task 2
    epic_node = forest.add_node(
        node_or_title="Foundation Epic",
        node_type=NodeType.GOAL,
        description="Architecture and core foundation epic",
        priority=Priority.HIGH,
        tags=["core", "arch"],
    )

    task_1 = forest.add_node(
        node_or_title="Implement Forest Engine",
        node_type=NodeType.TASK,
        description="Write task forest graph engine",
        priority=Priority.CRITICAL,
        tags=["core", "engine"],
    )
    forest.add_dependency(task_1.id, epic_node.id)

    task_2 = forest.add_node(
        node_or_title="Obsidian Sync Bridge",
        node_type=NodeType.TASK,
        description="Implement bidirectional markdown and wikilink sync",
        priority=Priority.HIGH,
        tags=["obsidian", "sync"],
    )
    forest.add_dependency(task_2.id, task_1.id)

    # 2. Export to vault directory
    sync = ObsidianTaskForestSync(forest=forest, vault_dir=str(vault_dir))
    count = sync.export_all()
    assert count == 3

    # 3. Verify markdown files
    exported_files = list(vault_dir.glob("*.md"))
    assert len(exported_files) == 3

    files_by_title = {}
    for f in exported_files:
        content = f.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Check line 1 starts with YAML frontmatter delimiter
        assert lines[0] == "---", f"File {f.name} does not start with YAML delimiter on line 1"

        # Check frontmatter can be parsed as valid YAML
        parts = content.split("---", 2)
        assert len(parts) >= 3, f"File {f.name} missing closing YAML frontmatter delimiter"
        fm_data = yaml.safe_load(parts[1])
        assert isinstance(fm_data, dict), f"Frontmatter in {f.name} is not a valid dict"
        assert "id" in fm_data
        assert "type" in fm_data
        assert "title" in fm_data
        assert "stage" in fm_data
        assert "priority" in fm_data
        assert "dependencies" in fm_data

        # Check HTML comment DNK-MRH header
        assert "<!-- --- DNK-MRH-HEADER ---" in content, f"File {f.name} missing HTML comment DNK-MRH start"
        assert "--- END DNK-MRH-HEADER -->" in content, f"File {f.name} missing HTML comment DNK-MRH end"

        files_by_title[fm_data["title"]] = {
            "content": content,
            "fm": fm_data,
            "path": f,
        }

    # Verify wikilinks for dependencies
    # Task 1 depends on Foundation Epic -> [[Foundation Epic]]
    assert "Foundation Epic" in files_by_title
    assert "Implement Forest Engine" in files_by_title
    assert "Obsidian Sync Bridge" in files_by_title

    task_1_content = files_by_title["Implement Forest Engine"]["content"]
    assert "[[Foundation Epic]]" in task_1_content, "Task 1 note does not contain [[Foundation Epic]] wikilink"

    task_2_content = files_by_title["Obsidian Sync Bridge"]["content"]
    assert "[[Implement Forest Engine]]" in task_2_content, "Task 2 note does not contain [[Implement Forest Engine]] wikilink"

    # 4. Test bidirectional import into a fresh TaskForest
    fresh_storage = tmp_path / "fresh_forest.json"
    fresh_forest = TaskForest(storage_path=str(fresh_storage))
    fresh_sync = ObsidianTaskForestSync(forest=fresh_forest, vault_dir=str(vault_dir))
    imported_count = fresh_sync.import_all()
    assert imported_count == 3

    assert fresh_forest.get_node(epic_node.id) is not None
    imported_task_1 = fresh_forest.get_node(task_1.id)
    assert imported_task_1 is not None
    assert epic_node.id in imported_task_1.dependencies

    imported_task_2 = fresh_forest.get_node(task_2.id)
    assert imported_task_2 is not None
    assert task_1.id in imported_task_2.dependencies
