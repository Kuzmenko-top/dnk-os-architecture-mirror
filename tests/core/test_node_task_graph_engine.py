# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_node_task_graph_engine.py"
# purpose: "Comprehensive Unit Tests for Node Task Graph Engine and DAG Dependencies"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from services.dnk_node_tasks.models import (
    NodeType,
    ExecutionStage,
    NodeStatus,
    EdgeRelation,
    DependencyEdge,
    NodePosition,
    NodeItem,
    NodeTaskGraph,
    IdeaConversionRequest,
)
from services.dnk_node_tasks.graph_engine import NodeTaskGraphEngine
from services.dnk_node_tasks.seed_data import create_initial_dnk_node_task_graph
from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager


def test_seed_graph_creation_and_stats():
    graph = create_initial_dnk_node_task_graph()
    assert len(graph.nodes) >= 10
    assert len(graph.edges) >= 10

    stats = NodeTaskGraphEngine.compute_statistics(graph)
    assert stats.total_nodes >= 10
    assert stats.ideas_count >= 3
    assert stats.epics_count >= 2
    assert stats.tasks_count >= 4
    assert stats.gates_count >= 2
    assert stats.overall_progress > 0.0


def test_cycle_detection_in_dag():
    edges = [
        DependencyEdge(id="e1", source="A", target="B", relation=EdgeRelation.DEPENDS_ON),
        DependencyEdge(id="e2", source="B", target="C", relation=EdgeRelation.DEPENDS_ON),
    ]

    # Adding C -> A should trigger a cycle
    has_cycle, path = NodeTaskGraphEngine.detect_cycle_with_new_edge(
        existing_edges=edges,
        new_source="C",
        new_target="A",
        relation=EdgeRelation.DEPENDS_ON
    )
    assert has_cycle is True
    assert "A" in path and "C" in path

    # Adding D -> A is legal
    has_cycle_2, _ = NodeTaskGraphEngine.detect_cycle_with_new_edge(
        existing_edges=edges,
        new_source="D",
        new_target="A",
        relation=EdgeRelation.DEPENDS_ON
    )
    assert has_cycle_2 is False


def test_blocked_status_and_gating():
    node_a = NodeItem(
        id="task-a",
        title="Prerequisite Task",
        description="Must be done first",
        node_type=NodeType.TASK,
        stage=ExecutionStage.IN_PROGRESS,
        status=NodeStatus.IN_PROGRESS,
        progress=50.0,
        position=NodePosition(x=0, y=0)
    )
    node_b = NodeItem(
        id="task-b",
        title="Dependent Task",
        description="Waiting for A",
        node_type=NodeType.TASK,
        stage=ExecutionStage.READY,
        status=NodeStatus.READY,
        progress=0.0,
        position=NodePosition(x=100, y=0)
    )
    edge = DependencyEdge(
        id="e-ab",
        source="task-a",
        target="task-b",
        relation=EdgeRelation.DEPENDS_ON
    )

    graph = NodeTaskGraph(
        nodes={"task-a": node_a, "task-b": node_b},
        edges=[edge]
    )

    NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
    assert node_b.is_blocked is True
    assert "task-a" in node_b.blocked_by
    assert node_b.status == NodeStatus.BLOCKED

    # Attempting to move node_b to in_progress should fail
    allowed, reason = NodeTaskGraphEngine.can_transition_stage(
        node=node_b,
        target_stage=ExecutionStage.IN_PROGRESS,
        graph=graph
    )
    assert allowed is False
    assert "blocked by incomplete prerequisite" in reason

    # Complete task-a
    node_a.status = NodeStatus.COMPLETED
    node_a.progress = 100.0
    NodeTaskGraphEngine.recalculate_graph_dependencies(graph)

    assert node_b.is_blocked is False
    assert len(node_b.blocked_by) == 0
    assert node_b.status == NodeStatus.READY

    allowed_after, _ = NodeTaskGraphEngine.can_transition_stage(
        node=node_b,
        target_stage=ExecutionStage.IN_PROGRESS,
        graph=graph
    )
    assert allowed_after is True


def test_idea_conversion():
    graph = create_initial_dnk_node_task_graph()
    idea_id = "idea-remotion"
    assert idea_id in graph.nodes

    req = IdeaConversionRequest(
        idea_id=idea_id,
        new_task_title="Engineered Remotion Engine Implementation",
        node_type=NodeType.TASK,
        assigned_agent="dnk_video_ai_creator",
        target_module="services/dnk_video_engine",
        target_files=["services/dnk_video_engine/pipeline.py"]
    )

    new_task, spawn_edge = NodeTaskGraphEngine.convert_idea_to_task(graph, req)
    assert new_task.id in graph.nodes
    assert new_task.title == "Engineered Remotion Engine Implementation"
    assert new_task.assigned_agent == "dnk_video_ai_creator"
    assert spawn_edge in graph.edges
    assert spawn_edge.relation == EdgeRelation.SPAWNS_FROM

    # The idea itself is marked completed/converted
    assert graph.nodes[idea_id].status == NodeStatus.COMPLETED
    assert "converted" in graph.nodes[idea_id].tags


def test_topological_sort():
    graph = create_initial_dnk_node_task_graph()
    order = NodeTaskGraphEngine.get_topological_execution_order(graph)
    assert len(order) == len(graph.nodes)
    # Check that task-node-system appears before task-occ-merge because occ depends on node-system
    pos_node = order.index("task-node-system")
    pos_occ = order.index("task-occ-merge")
    assert pos_node < pos_occ


def test_persistence_and_obsidian_sync(tmp_path):
    data_file = tmp_path / "test_graph.json"
    obsidian_dir = tmp_path / "obsidian_tasks"

    manager = NodeTaskPersistenceManager(
        data_file_path=str(data_file),
        obsidian_dir=str(obsidian_dir)
    )

    graph = manager.load_graph()
    assert len(graph.nodes) >= 10
    assert data_file.exists()

    res = manager.sync_to_obsidian()
    assert res["status"] == "success"
    assert res["synced_count"] >= 11
    assert (obsidian_dir / "000_DNK_TASK_AND_IDEAS_INDEX.md").exists()
    assert (obsidian_dir / "task-node-system.md").exists()


def test_compute_critical_path():
    # Construct a small DAG:
    # task-1 (dur 3h) -> task-2 (dur 8h, critical priority) -> task-4 (dur 3h)
    # task-1 -> task-3 (dur 1h, low priority) -> task-4
    # The critical path must be task-1 -> task-2 -> task-4
    node_1 = NodeItem(id="t1", title="Start Task", priority="medium", status=NodeStatus.READY)
    node_2 = NodeItem(id="t2", title="Heavy Task", priority="critical", status=NodeStatus.READY)
    node_3 = NodeItem(id="t3", title="Light Task", priority="low", status=NodeStatus.READY)
    node_4 = NodeItem(id="t4", title="End Task", priority="medium", status=NodeStatus.READY)

    e12 = DependencyEdge(id="e12", source="t1", target="t2", relation=EdgeRelation.DEPENDS_ON)
    e13 = DependencyEdge(id="e13", source="t1", target="t3", relation=EdgeRelation.DEPENDS_ON)
    e24 = DependencyEdge(id="e24", source="t2", target="t4", relation=EdgeRelation.DEPENDS_ON)
    e34 = DependencyEdge(id="e34", source="t3", target="t4", relation=EdgeRelation.DEPENDS_ON)

    graph = NodeTaskGraph(
        nodes={"t1": node_1, "t2": node_2, "t3": node_3, "t4": node_4},
        edges=[e12, e13, e24, e34]
    )

    cpm = NodeTaskGraphEngine.compute_critical_path(graph)

    assert "t1" in cpm["critical_path_node_ids"]
    assert "t2" in cpm["critical_path_node_ids"]
    assert "t4" in cpm["critical_path_node_ids"]
    # t3 has slack, so it should not be on the critical path
    assert "t3" not in cpm["critical_path_node_ids"]
    assert "e12" in cpm["critical_edge_ids"]
    assert "e24" in cpm["critical_edge_ids"]
    assert "e13" not in cpm["critical_edge_ids"]
    assert "e34" not in cpm["critical_edge_ids"]
    # Duration: t1(3) + t2(8) + t4(3) = 14h
    assert cpm["total_duration_hours"] == 14.0
    # t2 should be identified as a bottleneck
    assert any(b["node_id"] == "t2" for b in cpm["bottlenecks"])

