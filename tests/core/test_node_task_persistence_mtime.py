# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_node_task_persistence_mtime.py"
# purpose: "Unit tests verifying automatic mtime cache invalidation and hot-sync in NodeTaskPersistenceManager."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import os
import time
from pathlib import Path
import pytest

from services.dnk_node_tasks.models import (
    ExecutionStage,
    NodeItem,
    NodeStatus,
    NodeTaskGraph,
    ProjectInfo,
)
from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager


@pytest.fixture
def temp_persistence_env(tmp_path: Path):
    """Fixture providing isolated temporary paths for graph, obsidian, and projects."""
    data_file = tmp_path / "node_task_graph.json"
    obsidian_dir = tmp_path / "obsidian"
    projects_file = tmp_path / "projects.json"
    obsidian_dir.mkdir(parents=True, exist_ok=True)

    manager = NodeTaskPersistenceManager(
        data_file_path=str(data_file),
        obsidian_dir=str(obsidian_dir),
        projects_file_path=str(projects_file),
    )
    return manager, data_file, projects_file


def test_initial_load_and_caching(temp_persistence_env):
    """Verifies that subsequent calls return cached graph if file mtime is unchanged."""
    manager, data_file, _ = temp_persistence_env

    # 1. First load initializes seed and saves to disk
    graph1 = manager.load_graph()
    assert data_file.exists()
    assert len(graph1.nodes) > 0
    assert manager._last_loaded_mtime > 0.0

    # 2. Second load returns the cached in-memory graph instance
    graph2 = manager.load_graph()
    assert graph1 is graph2


def test_external_disk_modification_triggers_auto_reload(temp_persistence_env):
    """Verifies that modifying graph JSON externally invalidates in-memory cache."""
    manager, data_file, _ = temp_persistence_env

    # 1. Initial load
    graph = manager.load_graph()
    test_node_id = "test-node-ext-001"
    assert test_node_id not in graph.nodes

    # 2. External writer modifies data_file directly on disk
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["nodes"][test_node_id] = {
        "id": test_node_id,
        "title": "External Injected Task",
        "description": "Created outside the running API process",
        "status": "ready",
        "stage": "ready",
        "position": {"x": 100.0, "y": 200.0},
        "dependencies": [],
        "created_at": "2026-09-06T12:00:00Z",
        "updated_at": "2026-09-06T12:00:00Z",
    }

    # Ensure mtime is strictly greater than initial load
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    future_mtime = time.time() + 2.0
    os.utime(data_file, (future_mtime, future_mtime))

    # 3. get_graph without force_reload automatically detects mtime change and reloads
    reloaded_graph = manager.get_graph()
    assert test_node_id in reloaded_graph.nodes
    assert reloaded_graph.nodes[test_node_id].title == "External Injected Task"

    # 4. get_node and find_node also reflect fresh data
    node = manager.get_node(test_node_id)
    assert node is not None
    assert node.title == "External Injected Task"

    found_node = manager.find_node(test_node_id)
    assert found_node is not None
    assert found_node.id == test_node_id


def test_internal_save_synchronizes_mtime(temp_persistence_env):
    """Verifies internal save_graph updates _last_loaded_mtime so no redundant disk load occurs."""
    manager, data_file, _ = temp_persistence_env

    graph = manager.load_graph()
    initial_mtime = manager._last_loaded_mtime

    # Add a node internally and save
    new_node = NodeItem(
        id="internal-node-001",
        title="Internal Node",
        stage=ExecutionStage.READY,
        status=NodeStatus.IN_PROGRESS,
    )
    graph.nodes[new_node.id] = new_node
    manager.save_graph(graph)

    # _last_loaded_mtime must be updated to current disk mtime
    assert manager._last_loaded_mtime >= initial_mtime

    # Next load_graph returns cached graph without error
    cached_graph = manager.load_graph()
    assert cached_graph is graph
    assert "internal-node-001" in cached_graph.nodes


def test_projects_external_modification_auto_reload(temp_persistence_env):
    """Verifies that projects.json external changes are auto-reloaded via mtime check."""
    manager, _, projects_file = temp_persistence_env

    # 1. Initial projects load
    projects = manager.get_projects()
    assert len(projects) > 0
    assert manager._last_projects_mtime > 0.0

    # 2. External writer appends a new project
    new_proj_id = "proj-ext-999"
    with open(projects_file, "r", encoding="utf-8") as f:
        projs_data = json.load(f)

    projs_data.append({
        "id": new_proj_id,
        "name": "External Test Project",
        "slug": "external-test-project",
        "description": "Project created by external agent",
        "icon": "Folder",
        "color": "#ff0000",
        "created_at": "2026-09-06T12:00:00Z",
    })

    with open(projects_file, "w", encoding="utf-8") as f:
        json.dump(projs_data, f, indent=2)

    future_mtime = time.time() + 2.0
    os.utime(projects_file, (future_mtime, future_mtime))

    # 3. get_projects auto-detects new mtime and returns updated list
    updated_projects = manager.get_projects()
    matching = [p for p in updated_projects if p.id == new_proj_id]
    assert len(matching) == 1
    assert matching[0].name == "External Test Project"


def test_file_path_property_backward_compat(temp_persistence_env):
    """Verifies file_path alias property works as expected."""
    manager, data_file, _ = temp_persistence_env
    assert manager.file_path == data_file
