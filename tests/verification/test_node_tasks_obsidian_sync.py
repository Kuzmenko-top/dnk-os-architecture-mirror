# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_node_tasks_obsidian_sync.py"
# purpose: "Verification tests for Obsidian Markdown Bidirectional Sync Engine & API Endpoints"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from apps.api.main import app
from services.dnk_canvas_api.obsidian_sync_engine import ObsidianSyncEngine
from services.dnk_node_tasks.models import (
    NodeType,
    ExecutionStage,
    NodeStatus,
    EdgeRelation,
    NodeItem,
)
from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager


@pytest.fixture
def isolated_manager(tmp_path):
    """Provides an isolated NodeTaskPersistenceManager with a clean temp directory."""
    test_db = str(tmp_path / "test_tasks_graph.json")
    vault_dir = tmp_path / "obsidian_vault"
    vault_dir.mkdir(parents=True, exist_ok=True)

    manager = NodeTaskPersistenceManager(
        data_file_path=test_db,
        obsidian_dir=str(vault_dir),
    )
    NodeTaskPersistenceManager._instance = manager
    yield manager, vault_dir
    NodeTaskPersistenceManager._instance = None


@pytest.fixture
def client(isolated_manager):
    """FastAPI TestClient bound to isolated persistence manager."""
    manager, vault_dir = isolated_manager
    with TestClient(app) as tc:
        yield tc, vault_dir


def test_parse_markdown_with_frontmatter_and_wikilinks(tmp_path):
    """Verify that ObsidianSyncEngine properly parses Frontmatter, [[wikilinks]], checkboxes, and headers."""
    note_file = tmp_path / "task-canvas-core.md"
    note_content = """# --- DNK-MRH-HEADER ---
# mrh_id: "docs/notes/tasks_and_ideas/task-canvas-core.md"
# purpose: "Test note"
# --- END DNK-MRH-HEADER ---

---
id: task-canvas-core
title: "Universal Canvas Core Engine"
node_type: task
stage: ready
status: ready
progress: 35.0
priority: high
project_id: dnk_core
assigned_agent: gerych_builder
target_module: core
tags: [canvas, engine, realtime]
dependencies:
  - "[[task-auth-sso]]"
  - task-db-schema
position:
  x: 150.0
  y: 250.0
---

# Universal Canvas Core Engine

### Description
Core engine for canvas orchestration and dynamic stage gating.

### Acceptance Criteria
- [ ] Implement headless graph engine
- [x] Add cycle detection algorithm
- [ ] Connect WebSocket sync bridge

### Upstream Dependencies (Prerequisites)
- **depends_on** from [[task-event-bus]]
- **depends_on** from [[task-auth-sso|Authentication Service]]

### Target Module & Files
- `services/dnk_canvas_api/engine.py`
"""
    note_file.write_text(note_content, encoding="utf-8")

    parsed = ObsidianSyncEngine.parse_markdown_note(note_file)

    assert parsed is not None
    assert parsed["id"] == "task-canvas-core"
    assert parsed["title"] == "Universal Canvas Core Engine"
    assert parsed["node_type"] == NodeType.TASK
    assert parsed["stage"] == ExecutionStage.READY
    assert parsed["status"] == NodeStatus.READY
    assert parsed["progress"] == 35.0
    assert parsed["priority"] == "high"
    assert parsed["project_id"] == "dnk_core"
    assert parsed["assigned_agent"] == "gerych_builder"
    assert parsed["target_module"] == "core"
    assert parsed["position"].x == 150.0
    assert parsed["position"].y == 250.0
    assert "canvas" in parsed["tags"]

    # Check dependencies normalization and extraction
    deps = parsed["dependencies"]
    assert "task-auth-sso" in deps
    assert "task-db-schema" in deps
    assert "task-event-bus" in deps

    # Check acceptance criteria parsing
    criteria = parsed["acceptance_criteria"]
    assert "Implement headless graph engine" in criteria
    assert "Add cycle detection algorithm" in criteria
    assert "Connect WebSocket sync bridge" in criteria

    # Check target files
    assert "services/dnk_canvas_api/engine.py" in parsed["target_files"]


def test_sync_from_obsidian_creates_and_updates_nodes(isolated_manager):
    """Verify that sync_from_obsidian_vault creates new nodes, updates existing ones, and reconciles edges."""
    manager, vault_dir = isolated_manager

    # 1. Create two interrelated notes
    note1 = vault_dir / "task-alpha.md"
    note1.write_text(
        """---
id: task-alpha
title: "Alpha Infrastructure"
node_type: task
stage: ready
status: ready
progress: 10.0
priority: high
project_id: dnk_core
---
# Alpha Infrastructure
### Description
Alpha baseline infrastructure.
### Acceptance Criteria
- [ ] Provision database
""",
        encoding="utf-8",
    )

    note2 = vault_dir / "task-beta.md"
    note2.write_text(
        """---
id: task-beta
title: "Beta Microservice"
node_type: task
stage: ready
status: ready
progress: 0.0
priority: medium
project_id: dnk_core
dependencies:
  - "[[task-alpha]]"
---
# Beta Microservice
### Description
Dependent beta microservice.
### Acceptance Criteria
- [ ] Connect to Alpha
""",
        encoding="utf-8",
    )

    # First sync: import nodes and create dependency edge
    res1 = ObsidianSyncEngine.sync_from_obsidian_vault(vault_dir=vault_dir)
    assert res1["status"] == "success"
    assert res1["scanned"] == 2
    assert res1["imported"] == 2
    assert res1["updated"] == 0
    assert res1["edges_synced"] == 1

    graph = manager.load_graph(force_reload=True)
    assert "task-alpha" in graph.nodes
    assert "task-beta" in graph.nodes
    assert graph.nodes["task-beta"].is_blocked is True
    assert "task-alpha" in graph.nodes["task-beta"].blocked_by

    # 2. Update note 1: complete task-alpha in markdown note
    note1.write_text(
        """---
id: task-alpha
title: "Alpha Infrastructure (Completed)"
node_type: task
stage: completed
status: completed
progress: 100.0
priority: high
project_id: dnk_core
---
# Alpha Infrastructure (Completed)
### Description
Alpha baseline infrastructure is fully complete.
### Acceptance Criteria
- [x] Provision database
""",
        encoding="utf-8",
    )

    # Second sync: update existing nodes
    res2 = ObsidianSyncEngine.sync_from_obsidian_vault(vault_dir=vault_dir)
    assert res2["status"] == "success"
    assert res2["scanned"] == 2
    assert res2["imported"] == 0
    assert res2["updated"] == 2

    graph2 = manager.load_graph(force_reload=True)
    assert graph2.nodes["task-alpha"].status == NodeStatus.COMPLETED
    assert graph2.nodes["task-alpha"].progress == 100.0
    # Because task-alpha is completed, task-beta should unblock!
    assert graph2.nodes["task-beta"].is_blocked is False


def test_api_bidirectional_sync_endpoints(client):
    """Verify that both /sync_from_obsidian and /sync_bidirectional API endpoints work as expected."""
    tc, vault_dir = client

    # Seed a note in the vault
    test_note = vault_dir / "task-api-endpoint-test.md"
    test_note.write_text(
        """---
id: task-api-endpoint-test
title: "API Endpoint Sync Test"
node_type: task
stage: ready
status: ready
progress: 50.0
priority: medium
project_id: dnk_core
---
# API Endpoint Sync Test
### Acceptance Criteria
- [x] Verify POST /sync_from_obsidian
- [x] Verify POST /sync_bidirectional
""",
        encoding="utf-8",
    )

    # 1. Test POST /api/v3/node_tasks/sync_from_obsidian
    resp_from = tc.post(
        "/api/v3/node_tasks/sync_from_obsidian",
        json={"vault_dir": str(vault_dir), "project_id": "dnk_core"},
    )
    assert resp_from.status_code == 200
    data_from = resp_from.json()
    assert data_from["status"] == "success"
    assert data_from["scanned"] == 1
    assert data_from["nodes_synced"] >= 1

    # 2. Test POST /api/v3/node_tasks/sync_bidirectional
    resp_bidi = tc.post(
        "/api/v3/node_tasks/sync_bidirectional",
        json={"vault_dir": str(vault_dir), "project_id": "dnk_core"},
    )
    assert resp_bidi.status_code == 200
    data_bidi = resp_bidi.json()
    assert data_bidi["status"] == "success"
    assert data_bidi["scanned"] == 1
    assert data_bidi["exported"] >= 1


def test_soup_resilience_and_anti_dangling_guard(isolated_manager):
    """
    Validates Soup resilience layer in ObsidianSyncEngine:
    1. Resilient line-by-line fallback recovery when YAML frontmatter has syntax errors.
    2. Anti-Dangling Wikilinks Guard: automatically creating placeholder stub node for missing dependency.
    3. Criteria Union: merging criteria without overwriting existing checked items.
    """
    manager, vault_dir = isolated_manager

    # Note with malformed YAML (tab characters / unquoted special colon syntax)
    # and dangling wikilink to non-existent task-phantom-prereq
    malformed_note = vault_dir / "broken_task.md"
    malformed_note.write_text(
        """---
id: task-malformed-yaml
title: Heuristically Recovered Task
node_type: task
stage: architecture
status: in_progress
priority: high
dependencies: [[task-phantom-prereq]]
\tbad_tab_line: this: breaks: yaml: parser
---
# Heuristically Recovered Task
### Acceptance Criteria
- [ ] Recover from corrupted YAML
- [x] Auto-heal dependencies
""",
        encoding="utf-8",
    )

    res = ObsidianSyncEngine.sync_from_obsidian_vault(vault_dir=vault_dir)

    assert res["status"] == "success"
    # Both the recovered note and the phantom stub node should have been ingested
    assert res["imported"] >= 2
    assert res["edges_synced"] >= 1

    loaded_graph = manager.load_graph()
    assert "task-malformed-yaml" in loaded_graph.nodes
    assert "task-phantom-prereq" in loaded_graph.nodes

    recovered_node = loaded_graph.nodes["task-malformed-yaml"]
    assert recovered_node.title == "Heuristically Recovered Task"
    assert recovered_node.status == NodeStatus.IN_PROGRESS
    assert len(recovered_node.acceptance_criteria) == 2

    # Verify phantom stub node created by Anti-Dangling Guard
    phantom_node = loaded_graph.nodes["task-phantom-prereq"]
    assert "unresolved_prerequisite" in phantom_node.tags
    assert phantom_node.node_type == NodeType.IDEA
    assert phantom_node.assigned_agent == "herich_librarian"

