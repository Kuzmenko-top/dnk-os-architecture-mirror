# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_visual_canvas_control.py"
# purpose: "Verification test suite for Vector 5: Visual Control Panel on Canvas (TaskDNA DAG to Obsidian Canvas, Live HUD, Stage Transitions, and Bidirectional Sync)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import subprocess
import sys
from pathlib import Path
import pytest

HUB_ROOT = Path(__file__).resolve().parent.parent.parent

from core.orchestrator.visual_canvas_control import (
    VisualCanvasControlEngine,
    STAGE_CANVAS_COLORS,
    STAGE_STATUS_ICONS,
)
from core.task_forest.forest import TaskForest
from core.task_forest.models import TaskNode, ExecutionStage, Priority


@pytest.fixture
def temp_canvas_path(tmp_path):
    canvas_file = tmp_path / "test_control_panel.canvas"
    return canvas_file


@pytest.fixture
def sample_task_dna():
    return {
        "goal": "Build Obsidian Canvas Visual Control Panel",
        "task_id": "test_dna_001",
        "dag_tree": [
            {
                "id": "task_1",
                "title": "Architecture Specification",
                "stage": "done",
                "assigned_agent": "antigravity_mentor",
                "risk_level": "low",
                "dependencies": [],
                "tool_budget": "<= 25 tools",
            },
            {
                "id": "task_2",
                "title": "Core Canvas Engine Implementation",
                "stage": "in_progress",
                "assigned_agent": "gerych_builder",
                "risk_level": "medium",
                "dependencies": ["task_1"],
                "tool_budget": "<= 25 tools",
            },
            {
                "id": "task_3",
                "title": "Adversarial Quality Gate Verification",
                "stage": "backlog",
                "assigned_agent": "gerych_auditor",
                "risk_level": "low",
                "dependencies": ["task_2"],
                "tool_budget": "<= 25 tools",
            },
        ],
    }


def test_render_progress_bar():
    engine = VisualCanvasControlEngine()
    assert engine.render_progress_bar(0, 10) == "[░░░░░░░░░░] 0%"
    assert engine.render_progress_bar(5, 10) == "[█████░░░░░] 50%"
    assert engine.render_progress_bar(10, 10) == "[██████████] 100%"
    assert engine.render_progress_bar(0, 0) == "[░░░░░░░░░░] 0%"


def test_compute_topological_layout(sample_task_dna):
    engine = VisualCanvasControlEngine()
    coords, depth_map = engine.compute_topological_layout(sample_task_dna["dag_tree"])

    assert depth_map["task_1"] == 0
    assert depth_map["task_2"] == 1
    assert depth_map["task_3"] == 2

    assert coords["task_1"][0] < coords["task_2"][0]
    assert coords["task_2"][0] < coords["task_3"][0]


def test_build_node_markdown():
    engine = VisualCanvasControlEngine()
    task = {
        "id": "sub_1",
        "title": "Liquid AST Synthesis",
        "stage": "in_progress",
        "assigned_agent": "dnk_shopify",
        "risk_level": "high",
        "dependencies": ["root_task"],
        "tool_budget": "<= 20 tools",
        "description": "Create modular Liquid templates.",
    }
    md = engine.build_node_markdown(task)
    assert "### Liquid AST Synthesis" in md
    assert "🛍️ DNK Shopify Engine" in md
    assert "⚡ [IN_PROGRESS]" in md
    assert "`High`" in md
    assert "`root_task`" in md
    assert "<= 20 tools" in md
    assert "- [ ]" in md


def test_generate_canvas_from_task_dna(temp_canvas_path, sample_task_dna):
    engine = VisualCanvasControlEngine(default_output_path=temp_canvas_path)
    canvas_doc = engine.generate_canvas_from_task_dna(sample_task_dna, canvas_path=temp_canvas_path)

    assert temp_canvas_path.exists()
    assert "nodes" in canvas_doc
    assert "edges" in canvas_doc

    # Check HUD Node exists
    hud_node = next((n for n in canvas_doc["nodes"] if n["id"] == "control_panel_hud"), None)
    assert hud_node is not None
    assert hud_node["type"] == "text"
    assert "🎛️ DNK OS Swarm Control Panel" in hud_node["text"]
    assert "**1** / **3** completed" in hud_node["text"]

    # Check Task Nodes
    t1 = next(n for n in canvas_doc["nodes"] if n["id"] == "task_1")
    t2 = next(n for n in canvas_doc["nodes"] if n["id"] == "task_2")
    t3 = next(n for n in canvas_doc["nodes"] if n["id"] == "task_3")

    assert t1["color"] == "4"  # done = green
    assert t2["color"] == "5"  # in_progress = cyan
    assert t3["color"] == "3"  # backlog = yellow

    # Check Edges
    assert len(canvas_doc["edges"]) == 2
    edge_1_to_2 = next(e for e in canvas_doc["edges"] if e["fromNode"] == "task_1" and e["toNode"] == "task_2")
    assert edge_1_to_2["fromSide"] == "right"
    assert edge_1_to_2["toSide"] == "left"
    assert edge_1_to_2["color"] == "4"  # fromNode task_1 is done


def test_update_node_stage(temp_canvas_path, sample_task_dna):
    engine = VisualCanvasControlEngine(default_output_path=temp_canvas_path)
    engine.generate_canvas_from_task_dna(sample_task_dna, canvas_path=temp_canvas_path)

    # Transition task_2 to done
    res = engine.update_node_stage("task_2", "done", canvas_path=temp_canvas_path, notes="Passed all tests")
    assert res["status"] == "success"
    assert res["completed_tasks"] == 2

    # Verify updated canvas content
    canvas_data = json.loads(temp_canvas_path.read_text(encoding="utf-8"))
    t2 = next(n for n in canvas_data["nodes"] if n["id"] == "task_2")
    assert t2["color"] == "4"
    assert "✅ [DONE]" in t2["text"]
    assert "- [x]" in t2["text"]
    assert "Passed all tests" in t2["text"]

    # Verify HUD reflects 2/3 completed
    hud = next(n for n in canvas_data["nodes"] if n["id"] == "control_panel_hud")
    assert "**2** / **3** completed" in hud["text"]


def test_sync_forest_bidirectional(temp_canvas_path, tmp_path):
    forest_storage = tmp_path / "task_forest_db"
    forest = TaskForest(storage_path=str(forest_storage))

    node_a = TaskNode(
        id="node_a",
        title="Design Architecture",
        stage=ExecutionStage.DONE,
        priority=Priority.HIGH,
        assigned_agent="antigravity_mentor",
    )
    node_b = TaskNode(
        id="node_b",
        title="Develop Backend API",
        stage=ExecutionStage.IN_PROGRESS,
        priority=Priority.MEDIUM,
        dependencies=["node_a"],
        assigned_agent="dnk_dev_fullstack",
    )
    forest.create_node(node_a)
    forest.create_node(node_b)

    engine = VisualCanvasControlEngine(default_output_path=temp_canvas_path)
    # Sync Forest -> Canvas
    engine.sync_forest_to_canvas(forest=forest, canvas_path=temp_canvas_path)

    assert temp_canvas_path.exists()
    canvas_doc = json.loads(temp_canvas_path.read_text(encoding="utf-8"))
    nodes = canvas_doc["nodes"]
    assert any(n["id"] == "node_a" for n in nodes)
    assert any(n["id"] == "node_b" for n in nodes)

    # Simulate user moving node_b in Obsidian Canvas to (800, 600)
    for n in canvas_doc["nodes"]:
        if n["id"] == "node_b":
            n["x"] = 800
            n["y"] = 600
            n["color"] = "4"  # User marked done
    temp_canvas_path.write_text(json.dumps(canvas_doc), encoding="utf-8")

    # Sync Canvas -> Forest
    updated_ids = engine.sync_canvas_to_forest(canvas_path=temp_canvas_path, forest=forest)
    assert "node_b" in updated_ids
    assert forest.nodes["node_b"].position["x"] == 800.0
    assert forest.nodes["node_b"].position["y"] == 600.0
    assert forest.nodes["node_b"].stage == ExecutionStage.DONE


def test_cli_runner_goal_and_status(temp_canvas_path):
    # Test --goal CLI
    cmd = [
        sys.executable,
        "scripts/system/visual_canvas_control_runner.py",
        "--goal",
        "Implement Realtime Obsidian Canvas Dashboard",
        "--canvas-path",
        str(temp_canvas_path),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode == 0
    assert "Decomposed Goal & Generated Visual Control Panel" in p.stdout
    assert temp_canvas_path.exists()

    # Test --status CLI
    cmd_status = [
        sys.executable,
        "scripts/system/visual_canvas_control_runner.py",
        "--status",
        "--canvas-path",
        str(temp_canvas_path),
    ]
    p_status = subprocess.run(cmd_status, capture_output=True, text=True)
    assert p_status.returncode == 0
    assert "Visual Control Panel Telemetry" in p_status.stdout
    assert "DNK OS Swarm Control Panel" in p_status.stdout

    # Test --update-node CLI
    cmd_update = [
        sys.executable,
        "scripts/system/visual_canvas_control_runner.py",
        "--update-node",
        "slice_1_arch",
        "--stage",
        "done",
        "--notes",
        "Slice verified green",
        "--canvas-path",
        str(temp_canvas_path),
    ]
    p_update = subprocess.run(cmd_update, capture_output=True, text=True)
    assert p_update.returncode == 0
    assert "transitioned to 'done'" in p_update.stdout


def test_record_live_tool_execution_lifecycle(temp_canvas_path, sample_task_dna):
    engine = VisualCanvasControlEngine(default_output_path=temp_canvas_path)
    engine.generate_canvas_from_task_dna(sample_task_dna, canvas_path=temp_canvas_path)

    # 1. Mutating tool: write_file
    res1 = engine.record_live_tool_execution(
        tool_name="write_file",
        tool_input={"path": "core/orchestrator/visual_canvas_control.py"},
        status="success",
        canvas_path=temp_canvas_path,
    )
    assert res1 is not None
    assert res1["tools_executed"] == 1

    doc1 = json.loads(temp_canvas_path.read_text(encoding="utf-8"))
    hud1 = next(n for n in doc1["nodes"] if n["id"] == "control_panel_hud")
    assert "**Tools Executed**: `1` calls" in hud1["text"]

    # 2. Terminal test run passing
    res2 = engine.record_live_tool_execution(
        tool_name="terminal",
        tool_input={"command": "./.venv/bin/pytest tests/verification/test_visual_canvas_control.py"},
        status="success",
        result_text="3 passed in 0.5s",
        canvas_path=temp_canvas_path,
    )
    assert res2 is not None
    assert res2["tools_executed"] == 2
    doc2 = json.loads(temp_canvas_path.read_text(encoding="utf-8"))
    hud2 = next(n for n in doc2["nodes"] if n["id"] == "control_panel_hud")
    assert "**Tools Executed**: `2` calls" in hud2["text"]


def test_hermes_post_tool_hook_live_canvas_sync(temp_canvas_path, sample_task_dna, monkeypatch):
    import os
    engine = VisualCanvasControlEngine(default_output_path=temp_canvas_path)
    engine.generate_canvas_from_task_dna(sample_task_dna, canvas_path=temp_canvas_path)

    payload = {
        "hook_event_name": "post_tool_call",
        "tool_name": "patch",
        "tool_input": {"path": "scripts/system/hermes_post_tool_hook.py"},
        "extra": {
            "status": "success",
            "result": "Applied diff successfully"
        }
    }

    env = dict(os.environ)
    env["DNK_ACTIVE_CANVAS_PATH"] = str(temp_canvas_path)

    proc = subprocess.run(
        [sys.executable, "scripts/system/hermes_post_tool_hook.py"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
    )
    assert proc.returncode == 0
    doc = json.loads(temp_canvas_path.read_text(encoding="utf-8"))
    hud = next(n for n in doc["nodes"] if n["id"] == "control_panel_hud")
    assert "**Tools Executed**: `1` calls" in hud["text"]


def test_poll_and_execute_canvas_triggers(temp_canvas_path, sample_task_dna, monkeypatch):
    """Vector 3: Test interactive canvas triggers for running tests and dispatching workers."""
    engine = VisualCanvasControlEngine(default_output_path=temp_canvas_path)
    engine.generate_canvas_from_task_dna(sample_task_dna, canvas_path=temp_canvas_path)

    # 1. Simulate user ticking "- [x] Run Tests" in a node card
    doc = json.loads(temp_canvas_path.read_text(encoding="utf-8"))
    for n in doc["nodes"]:
        if n["id"] == "task_2":
            n["text"] += "\n- [x] Run Tests"
            break
    temp_canvas_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    # Poll and execute triggers
    actions = engine.poll_and_execute_canvas_triggers(
        canvas_path=temp_canvas_path,
        auto_execute=True,
        test_command=[sys.executable, "-c", "import sys; sys.exit(0)"]
    )
    assert len(actions) == 1
    assert actions[0]["node_id"] == "task_2"
    assert actions[0]["action"] == "run_tests"

    # Check updated canvas file
    updated_doc = json.loads(temp_canvas_path.read_text(encoding="utf-8"))
    node_2 = next(n for n in updated_doc["nodes"] if n["id"] == "task_2")
    assert "- [ ] Run Tests" in node_2["text"]
    assert "✅ [Tests Passed]" in node_2["text"]
    assert node_2["color"] == "4"

    # 2. Simulate user ticking "- [x] Dispatch Worker" in a node card
    node_2["text"] += "\n- [x] Dispatch Worker"
    temp_canvas_path.write_text(json.dumps(updated_doc, indent=2), encoding="utf-8")

    mock_dispatched = []

    def mock_dispatch(agent, task_description, workspace_id, parameters=None):
        mock_dispatched.append({"agent": agent, "desc": task_description})
        return json.dumps({"status": "dispatched", "worker": agent})

    monkeypatch.setattr("core.hermes_agent.tools.dnk_swarm_tool.dnk_swarm_dispatch", mock_dispatch)

    actions2 = engine.poll_and_execute_canvas_triggers(
        canvas_path=temp_canvas_path,
        auto_execute=True
    )
    assert len(actions2) == 1
    assert actions2[0]["action"] == "dispatch_worker"
    assert len(mock_dispatched) == 1
    assert mock_dispatched[0]["agent"] == "gerych_builder"

    # 3. Test CLI Runner with --poll-triggers
    cli_proc = subprocess.run(
        [sys.executable, "scripts/system/visual_canvas_control_runner.py", "--poll-triggers", "--canvas-path", str(temp_canvas_path)],
        capture_output=True,
        text=True,
        cwd=str(HUB_ROOT)
    )
    assert cli_proc.returncode == 0
    assert "interactive triggers" in cli_proc.stdout.lower()


def test_canvas_to_react_flow_bridge_roundtrip(temp_canvas_path, sample_task_dna, tmp_path):
    """Vector 4: Verify bidirectional SSOT bridge between Obsidian Canvas and React Flow."""
    engine = VisualCanvasControlEngine(default_output_path=temp_canvas_path)
    engine.generate_canvas_from_task_dna(sample_task_dna, canvas_path=temp_canvas_path)

    canvas_doc = json.loads(temp_canvas_path.read_text(encoding="utf-8"))
    
    # 1. Convert to React Flow
    rf_doc = engine.canvas_to_react_flow(canvas_doc)
    assert "nodes" in rf_doc and "edges" in rf_doc
    assert len(rf_doc["nodes"]) == len(canvas_doc["nodes"])
    assert len(rf_doc["edges"]) == len(canvas_doc["edges"])

    sample_rf_node = next(n for n in rf_doc["nodes"] if n["id"] == "task_1")
    assert "position" in sample_rf_node
    assert "dimensions" in sample_rf_node
    assert sample_rf_node["data"]["worker"] == "antigravity_mentor"

    # 2. Convert React Flow back to Canvas
    reconstructed_canvas = engine.react_flow_to_canvas(rf_doc)
    assert len(reconstructed_canvas["nodes"]) == len(canvas_doc["nodes"])
    assert len(reconstructed_canvas["edges"]) == len(canvas_doc["edges"])

    rec_node_1 = next(n for n in reconstructed_canvas["nodes"] if n["id"] == "task_1")
    assert rec_node_1["x"] == sample_rf_node["position"]["x"]
    assert rec_node_1["y"] == sample_rf_node["position"]["y"]

    # 3. CLI Runner Export/Import verification
    rf_export_path = tmp_path / "exported_rf.json"
    p_export = subprocess.run(
        [
            sys.executable,
            "scripts/system/visual_canvas_control_runner.py",
            "--export-react-flow",
            str(rf_export_path),
            "--canvas-path",
            str(temp_canvas_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(HUB_ROOT),
    )
    assert p_export.returncode == 0
    assert rf_export_path.exists()
    assert "Exported Obsidian Canvas to React Flow JSON" in p_export.stdout

    imported_canvas_path = tmp_path / "imported.canvas"
    p_import = subprocess.run(
        [
            sys.executable,
            "scripts/system/visual_canvas_control_runner.py",
            "--import-react-flow",
            str(rf_export_path),
            "--canvas-path",
            str(imported_canvas_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(HUB_ROOT),
    )
    assert p_import.returncode == 0
    assert imported_canvas_path.exists()
    assert "Imported React Flow JSON into Obsidian Canvas" in p_import.stdout

