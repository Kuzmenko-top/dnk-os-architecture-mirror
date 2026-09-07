# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_task_forest.py"
# purpose: "Comprehensive unit and integration tests for Task Forest nodes, dependencies, stages, and Obsidian sync."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import json
from pathlib import Path
from datetime import datetime

from core.task_forest import (
    NodeType,
    ExecutionStage,
    Priority,
    TaskNode,
    IdeaNode,
    GoalNode,
    BugNode,
    DocumentationNode,
    DependencyGraph,
    StageManager,
    TaskForest,
)
from core.obsidian.task_forest_sync import ObsidianTaskForestSync, TaskForestSync


class TestTaskForestModels:
    def test_create_task_node(self):
        node = TaskNode(
            id="task-1",
            title="Implement Core Engine",
            description="Build task forest engine",
            type=NodeType.TASK,
            stage=ExecutionStage.BACKLOG,
            priority=Priority.HIGH,
            tags=["core", "task_forest"],
        )
        assert node.id == "task-1"
        assert node.type == NodeType.TASK
        assert node.stage == ExecutionStage.BACKLOG
        assert node.priority == Priority.HIGH
        assert "core" in node.tags
        d = node.to_dict()
        assert d["id"] == "task-1"
        assert d["type"] == "task"

    def test_create_idea_node(self):
        idea = IdeaNode(
            id="idea-1",
            title="AI Co-pilot for Canvas",
            votes=5,
            status="proposed",
        )
        assert idea.id == "idea-1"
        assert idea.type == NodeType.IDEA
        assert idea.metadata["votes"] == 5
        assert idea.metadata["status"] == "proposed"

    def test_create_goal_node(self):
        goal = GoalNode(
            id="goal-1",
            title="Release DNK OS 2.0",
            milestone="Q4 2026",
            progress=0.45,
        )
        assert goal.id == "goal-1"
        assert goal.type == NodeType.GOAL
        assert goal.metadata["milestone"] == "Q4 2026"
        assert goal.metadata["progress"] == 0.45

    def test_create_bug_node(self):
        bug = BugNode(
            id="bug-1",
            title="Canvas zoom jump on pinch",
            severity="critical",
            reported_by="QA Swarm",
        )
        assert bug.id == "bug-1"
        assert bug.type == NodeType.BUG
        assert bug.metadata["severity"] == "critical"
        assert bug.metadata["reported_by"] == "QA Swarm"

    def test_create_documentation_node(self):
        doc = DocumentationNode(
            id="doc-1",
            title="Task Forest Architecture Guide",
            doc_type="architecture",
            version="1.0.0",
        )
        assert doc.id == "doc-1"
        assert doc.type == NodeType.DOCUMENTATION
        assert doc.metadata["doc_type"] == "architecture"
        assert doc.metadata["version"] == "1.0.0"


class TestDependencyGraph:
    def test_add_and_remove_dependency(self):
        graph = DependencyGraph()
        graph.add_dependency("task-B", "task-A")  # B depends on A
        assert "task-A" in graph.get_dependencies("task-B")
        assert "task-B" in graph.get_dependents("task-A")
        assert not graph.has_cycle()

        graph.remove_dependency("task-B", "task-A")
        assert "task-A" not in graph.get_dependencies("task-B")
        assert "task-B" not in graph.get_dependents("task-A")

    def test_cycle_detection(self):
        graph = DependencyGraph()
        graph.add_dependency("B", "A")  # B depends on A
        graph.add_dependency("C", "B")  # C depends on B
        assert not graph.has_cycle()

        # Add cycle: A depends on C
        graph.add_dependency("A", "C")
        assert graph.has_cycle()

    def test_execution_order_topological_sort(self):
        graph = DependencyGraph()
        # Task D depends on C; C depends on B; B depends on A
        graph.add_dependency("B", "A")
        graph.add_dependency("C", "B")
        graph.add_dependency("D", "C")

        order = graph.get_execution_order(["D", "B", "A", "C"])
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")
        assert order.index("C") < order.index("D")

    def test_execution_order_cycle_raises_error(self):
        graph = DependencyGraph()
        graph.add_dependency("A", "B")
        graph.add_dependency("B", "A")
        with pytest.raises(ValueError, match="(?i)cycle detected"):
            graph.get_execution_order(["A", "B"])


class TestStageTransitions:
    def test_valid_transitions(self):
        manager = StageManager()
        node = TaskNode(id="t-1", title="Test Node", stage=ExecutionStage.BACKLOG)

        assert manager.can_transition(node.stage, ExecutionStage.PLANNED)
        assert manager.transition(node, ExecutionStage.PLANNED)
        assert node.stage == ExecutionStage.PLANNED

        assert manager.can_transition(node.stage, ExecutionStage.IN_PROGRESS)
        assert manager.transition(node, ExecutionStage.IN_PROGRESS)
        assert node.stage == ExecutionStage.IN_PROGRESS

        assert manager.can_transition(node.stage, ExecutionStage.REVIEW)
        assert manager.transition(node, ExecutionStage.REVIEW)
        assert node.stage == ExecutionStage.REVIEW

        assert manager.can_transition(node.stage, ExecutionStage.DONE)
        assert manager.transition(node, ExecutionStage.DONE)
        assert node.stage == ExecutionStage.DONE
        assert node.completed_at is not None

    def test_invalid_transitions(self):
        manager = StageManager()
        node = TaskNode(id="t-1", title="Test Node", stage=ExecutionStage.BACKLOG)

        # Cannot jump from BACKLOG directly to DONE
        assert not manager.can_transition(node.stage, ExecutionStage.DONE)
        assert not manager.transition(node, ExecutionStage.DONE)
        assert node.stage == ExecutionStage.BACKLOG

        # DONE cannot transition back to BACKLOG
        node.stage = ExecutionStage.DONE
        assert not manager.can_transition(node.stage, ExecutionStage.BACKLOG)


class TestTaskForestWorkflow:
    def test_forest_lifecycle_and_blocking_dependencies(self, tmp_path):
        storage_file = tmp_path / "forest.json"
        forest = TaskForest(storage_path=str(storage_file))

        # Add node 1 (prerequisite) and node 2 (dependent)
        node_a = forest.add_node("Prerequisite Task", NodeType.TASK)
        node_b = forest.add_node("Dependent Task", NodeType.TASK)

        # Add dependency: B depends on A
        success = forest.add_dependency(node_b.id, node_a.id)
        assert success is True
        assert node_a.id in node_b.dependencies

        # Moving node B to PLANNED is allowed
        forest.transition_stage(node_b.id, ExecutionStage.PLANNED)
        assert node_b.stage == ExecutionStage.PLANNED

        # Moving node B to IN_PROGRESS should fail while node A is still in BACKLOG
        with pytest.raises(ValueError, match="blocked by"):
            forest.transition_stage(node_b.id, ExecutionStage.IN_PROGRESS)

        # Advance node A through to DONE
        forest.transition_stage(node_a.id, ExecutionStage.PLANNED)
        forest.transition_stage(node_a.id, ExecutionStage.IN_PROGRESS)
        forest.transition_stage(node_a.id, ExecutionStage.REVIEW)
        forest.transition_stage(node_a.id, ExecutionStage.DONE)
        assert node_a.stage == ExecutionStage.DONE

        # Now node B can advance to IN_PROGRESS
        forest.transition_stage(node_b.id, ExecutionStage.IN_PROGRESS)
        assert node_b.stage == ExecutionStage.IN_PROGRESS

        # Canvas format export
        canvas = forest.to_canvas_format()
        assert len(canvas["nodes"]) == 2
        assert len(canvas["edges"]) == 1
        assert canvas["edges"][0]["source"] == node_a.id
        assert canvas["edges"][0]["target"] == node_b.id

    def test_cycle_prevention_in_forest(self, tmp_path):
        forest = TaskForest(storage_path=str(tmp_path / "forest_cycle.json"))
        node_a = forest.add_node("Node A", NodeType.TASK)
        node_b = forest.add_node("Node B", NodeType.TASK)
        node_c = forest.add_node("Node C", NodeType.TASK)

        forest.add_dependency(node_b.id, node_a.id)  # B depends on A
        forest.add_dependency(node_c.id, node_b.id)  # C depends on B

        # Trying to make A depend on C should raise ValueError
        with pytest.raises(ValueError, match="cycle"):
            forest.add_dependency(node_a.id, node_c.id)


class TestObsidianTaskForestSync:
    def test_export_import_and_canvas_sync(self, tmp_path):
        vault_dir = tmp_path / "obsidian_vault"
        forest_file = tmp_path / "forest_sync.json"

        forest = TaskForest(storage_path=str(forest_file))
        node_1 = forest.add_node("Architecture Spec", NodeType.DOCUMENTATION, description="System design doc")
        node_2 = forest.add_node("Core Implementation", NodeType.TASK, description="Write python models")
        forest.add_dependency(node_2.id, node_1.id)

        sync_mgr = ObsidianTaskForestSync(forest=forest, vault_dir=str(vault_dir))
        
        # Test export_all and export_to_obsidian
        exported_count = sync_mgr.export_to_obsidian()
        assert exported_count == 2
        assert len(list(vault_dir.glob("*.md"))) == 2

        # Verify markdown content has YAML frontmatter and MRH header
        md_file = list(vault_dir.glob("*.md"))[0]
        content = md_file.read_text(encoding="utf-8")
        assert "DNK-MRH-HEADER" in content
        assert "---" in content
        assert "type:" in content

        # Test export_to_canvas
        canvas_file = vault_dir / "task_forest.canvas"
        sync_mgr.export_to_canvas(str(canvas_file))
        assert canvas_file.exists()
        canvas_json = json.loads(canvas_file.read_text(encoding="utf-8"))
        assert "nodes" in canvas_json
        assert "edges" in canvas_json
        assert len(canvas_json["nodes"]) == 2
        assert len(canvas_json["edges"]) == 1

        # Test import into a fresh TaskForest
        fresh_forest_file = tmp_path / "fresh_forest.json"
        fresh_forest = TaskForest(storage_path=str(fresh_forest_file))
        fresh_sync = TaskForestSync(forest=fresh_forest, vault_dir=str(vault_dir))
        
        imported_count = fresh_sync.import_from_obsidian()
        assert imported_count == 2
        assert fresh_forest.get_node(node_1.id) is not None
        assert fresh_forest.get_node(node_2.id) is not None
        assert node_1.id in fresh_forest.get_node(node_2.id).dependencies


class TestSwarmAgentIntegration:
    def test_swarm_agent_assignment_and_dispatch(self, tmp_path):
        forest = TaskForest(storage_path=str(tmp_path / "forest_agents.json"))
        node = forest.add_node("Implement UI Component", NodeType.TASK)

        # Assign Swarm Agent
        updated_node = forest.assign_agent(node.id, "gerych_builder")
        assert updated_node is not None
        assert updated_node.assigned_agent == "gerych_builder"
        assert updated_node.agent_status == "idle"

        # Dispatch Agent
        dispatch_res = forest.dispatch_agent(node.id, mode="direct")
        assert dispatch_res["status"] == "running"
        assert dispatch_res["agent"] == "gerych_builder"
        node = forest.get_node(node.id)
        assert node is not None
        assert node.stage == ExecutionStage.IN_PROGRESS
        assert node.agent_status == "running"

        # Complete Agent run
        forest.update_agent_status(node.id, "completed", run_id="run-12345")
        assert node.agent_status == "completed"
        assert node.agent_run_id == "run-12345"

        # Verify persistence and reload
        reloaded_forest = TaskForest(storage_path=str(tmp_path / "forest_agents.json"))
        reloaded_node = reloaded_forest.get_node(node.id)
        assert reloaded_node is not None
        assert reloaded_node.assigned_agent == "gerych_builder"
        assert reloaded_node.agent_status == "completed"
        assert reloaded_node.agent_run_id == "run-12345"

    def test_import_from_task_dna(self, tmp_path):
        forest = TaskForest(storage_path=str(tmp_path / "forest_dna.json"))

        sample_dna = {
            "task_id": "dna-999",
            "goal": "Build Automated Testing Engine",
            "dag_tree": [
                {
                    "id": "step-1",
                    "title": "Architecture Specification & Contracts",
                    "assigned_agent": "antigravity_mentor",
                    "dependencies": [],
                    "risk_level": "low",
                },
                {
                    "id": "step-2",
                    "title": "Core Implementation of Test Runners",
                    "assigned_agent": "dnk_dev_fullstack",
                    "dependencies": ["step-1"],
                    "risk_level": "medium",
                },
                {
                    "id": "step-3",
                    "title": "UI Dashboard for Test Status",
                    "assigned_agent": "gerych_builder",
                    "dependencies": ["step-2"],
                    "risk_level": "medium",
                },
                {
                    "id": "step-4",
                    "title": "Adversarial Quality Gate Audit",
                    "assigned_agent": "gerych_auditor",
                    "dependencies": ["step-3"],
                    "risk_level": "high",
                },
            ],
        }

        created_nodes = forest.import_from_task_dna(sample_dna, base_x=100.0, base_y=100.0)
        assert len(created_nodes) == 4

        # Check node mappings
        node1 = forest.get_node("step-1")
        assert node1 is not None
        assert node1.assigned_agent == "antigravity_mentor"
        assert node1.dependencies == []

        node2 = forest.get_node("step-2")
        assert node2 is not None
        assert node2.assigned_agent == "dnk_dev_fullstack"
        assert "step-1" in node2.dependencies

        node3 = forest.get_node("step-3")
        assert node3 is not None

        node4 = forest.get_node("step-4")
        assert node4 is not None
        assert node4.assigned_agent == "gerych_auditor"
        assert node4.priority == Priority.HIGH
        assert "step-3" in node4.dependencies

        # Check topological execution order
        all_ids = [n.id for n in created_nodes]
        exec_order = forest.dependency_graph.get_execution_order(all_ids)
        assert exec_order == ["step-1", "step-2", "step-3", "step-4"]

        # Check positioning layout (horizontal topological layers)
        assert node1.position["x"] < node2.position["x"]
        assert node2.position["x"] < node4.position["x"]

