# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_canvas_flow.py"
# purpose: "Comprehensive unit and integration tests for the Infinite Flow Canvas stack."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import pytest
from core.canvas_engine import CanvasEngine, CanvasNode

def test_infinite_flow_canvas_initialization():
    """Verify that CanvasEngine initializes with empty nodes and edges."""
    engine = CanvasEngine()
    assert len(engine.nodes) == 0
    assert len(engine.edges) == 0
    assert engine.has_cycle() is False

def test_infinite_flow_canvas_dynamic_lod():
    """Test building nodes at multiple Level of Detail (LOD) scales."""
    engine = CanvasEngine()
    
    # LOD Level 1: Field & Sector
    engine.add_node("field_dnk_hub", "Field: DNK OS MVP", "DocNode", "Executing")
    engine.add_node("sector_core", "Sector: Core Engine", "DocNode", "Queued")
    
    # LOD Level 2: Tree
    engine.add_node("tree_swarm", "Tree: Agentic Swarm", "PatternNode", "Queued")
    
    # LOD Level 3: Bush
    engine.add_node("bush_parser", "Bush: AST Parser", "TaskNode", "Queued")
    
    # LOD Level 4: Flower
    engine.add_node("flower_sync", "Flower: WS Sync", "TaskNode", "Done")

    # Connect them into a hierarchy/pipeline
    engine.add_edge("field_dnk_hub", "sector_core")
    engine.add_edge("sector_core", "tree_swarm")
    engine.add_edge("tree_swarm", "bush_parser")
    engine.add_edge("bush_parser", "flower_sync")

    assert len(engine.nodes) == 5
    assert len(engine.edges) == 4
    assert engine.has_cycle() is False

def test_infinite_flow_canvas_state_propagation():
    """Verify node state updates and CSS glassmorphism styles."""
    engine = CanvasEngine()
    engine.add_node("n1", "Core Gateway", "AgentNode", "Queued")
    
    # State validation
    assert engine.nodes["n1"].state == "Queued"
    assert "🔘 Queued" in engine.nodes["n1"].get_state_indicator()
    
    # Update state
    engine.update_node_state("n1", "Executing")
    assert engine.nodes["n1"].state == "Executing"
    assert "🔵 Executing" in engine.nodes["n1"].get_state_indicator()

    # Glassmorphism styling check
    style = engine.nodes["n1"].get_glassmorphism_style()
    assert "background" in style
    assert "backdropFilter" in style
    assert "rgba(0, 123, 255, 0.2)" in style["background"]

def test_infinite_flow_canvas_cycle_detection():
    """Test cycle/loop detection logic in CanvasEngine."""
    engine = CanvasEngine()
    engine.add_node("A", "Node A", "TaskNode")
    engine.add_node("B", "Node B", "TaskNode")
    engine.add_node("C", "Node C", "TaskNode")

    engine.add_edge("A", "B")
    engine.add_edge("B", "C")
    assert engine.has_cycle() is False

    # Create cycle
    engine.add_edge("C", "A")
    assert engine.has_cycle() is True

def test_infinite_flow_canvas_serialization():
    """Verify ReactFlow JSON layout and export format."""
    engine = CanvasEngine()
    engine.add_node("field_dnk_hub", "Field: DNK OS MVP", "DocNode", "Done")
    engine.add_node("sector_core", "Sector: Core Engine", "DocNode", "Executing")
    engine.add_edge("field_dnk_hub", "sector_core")

    # Serialize
    rf_data = engine.to_reactflow_graph()
    
    assert "nodes" in rf_data
    assert "edges" in rf_data
    assert rf_data["has_cycle"] is False
    assert len(rf_data["nodes"]) == 2
    assert len(rf_data["edges"]) == 1

    node_export = rf_data["nodes"][0]
    assert node_export["id"] in ["field_dnk_hub", "sector_core"]
    assert node_export["type"] == "custom"
    assert "position" in node_export
    assert "x" in node_export["position"]
    assert "y" in node_export["position"]
    assert "style" in node_export
    assert "backdropFilter" in node_export["style"]

def test_infinite_flow_canvas_time_travel_history():
    """Verify time-travel undo/redo version history snapshots."""
    engine = CanvasEngine()
    
    # State 1
    engine.add_node("n1", "Node 1", "PatternNode")
    engine.add_node("n2", "Node 2", "PatternNode")
    engine.add_edge("n1", "n2")
    idx1 = engine.take_snapshot("Initial setup")
    
    assert idx1 == 0
    assert engine.history_cursor == 0
    assert len(engine.nodes) == 2
    assert len(engine.edges) == 1

    # State 2
    engine.add_node("n3", "Node 3", "TaskNode")
    engine.add_edge("n2", "n3")
    idx2 = engine.take_snapshot("Added third task node")

    assert idx2 == 1
    assert engine.history_cursor == 1
    assert len(engine.nodes) == 3
    assert len(engine.edges) == 2

    # Step Back (Undo)
    success_undo = engine.undo()
    assert success_undo is True
    assert engine.history_cursor == 0
    assert len(engine.nodes) == 2
    assert len(engine.edges) == 1
    assert "n3" not in engine.nodes

    # Try boundary undo (should return False)
    assert engine.undo() is False
    assert engine.history_cursor == 0

    # Step Forward (Redo)
    success_redo = engine.redo()
    assert success_redo is True
    assert engine.history_cursor == 1
    assert len(engine.nodes) == 3
    assert len(engine.edges) == 2
    assert "n3" in engine.nodes

    # Try boundary redo (should return False)
    assert engine.redo() is False
    assert engine.history_cursor == 1
