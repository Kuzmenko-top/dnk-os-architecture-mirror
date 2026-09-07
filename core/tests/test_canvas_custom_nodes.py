# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_canvas_custom_nodes.py"
# purpose: "Unit tests for CanvasNode type additions, layout positioning and ReactFlow export structure."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-08"
# --- END DNK-MRH-HEADER ---

import pytest
from core.canvas_engine import CanvasEngine, CanvasNode

def test_custom_node_types_validation():
    """Verify that custom node types like PatternNode, DocNode, AgentNode, TaskNode are fully supported."""
    engine = CanvasEngine()
    
    # Test valid types
    n1 = engine.add_node("N1", "Pattern 1", "PatternNode", "Done")
    n2 = engine.add_node("N2", "Task 1", "TaskNode", "Executing")
    n3 = engine.add_node("N3", "Agent 1", "AgentNode", "Blocked")
    n4 = engine.add_node("N4", "Doc 1", "DocNode", "Queued")
    
    assert n1.type == "PatternNode"
    assert n2.type == "TaskNode"
    assert n3.type == "AgentNode"
    assert n4.type == "DocNode"

    # Test invalid type
    with pytest.raises(ValueError, match="Type must be one of"):
        engine.add_node("N5", "Bad", "InvalidType")

def test_calculate_auto_layout():
    """Verify that auto layout places nodes in structured columns without overlap."""
    engine = CanvasEngine()
    engine.add_node("N1", "Pattern 1", "PatternNode")
    engine.add_node("N2", "Doc 1", "DocNode")
    engine.add_node("N3", "Agent 1", "AgentNode")
    engine.add_node("N4", "Task 1", "TaskNode")

    engine.calculate_auto_layout()

    # Column x-offsets validation
    assert engine.nodes["N1"].x == 50.0
    assert engine.nodes["N2"].x == 50.0
    assert engine.nodes["N3"].x == 350.0
    assert engine.nodes["N4"].x == 650.0

    # Vertical spacing checks
    assert engine.nodes["N1"].y == 50.0
    assert engine.nodes["N2"].y == 230.0

def test_to_reactflow_graph():
    """Verify ReactFlow JSON export payload structure."""
    engine = CanvasEngine()
    engine.add_node("N1", "Pattern 1", "PatternNode", "Done")
    engine.add_node("N2", "Task 1", "TaskNode", "Executing")
    engine.add_edge("N1", "N2")

    graph = engine.to_reactflow_graph()

    # Nodes assertion
    assert "nodes" in graph
    assert len(graph["nodes"]) == 2
    n_export = graph["nodes"][0]
    assert n_export["id"] == "N1"
    assert n_export["type"] == "custom"
    assert "position" in n_export
    assert "x" in n_export["position"]
    assert "data" in n_export
    assert n_export["data"]["label"] == "Pattern 1"
    assert "style" in n_export
    assert "backdropFilter" in n_export["style"]

    # Edges assertion
    assert "edges" in graph
    assert len(graph["edges"]) == 1
    edge_export = graph["edges"][0]
    assert edge_export["source"] == "N1"
    assert edge_export["target"] == "N2"
    assert edge_export["animated"] is True
