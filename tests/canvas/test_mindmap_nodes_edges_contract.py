# --- DNK-MRH-HEADER ---
# mrh_id: "tests/canvas/test_mindmap_nodes_edges_contract.py"
# purpose: "Contract tests for Mind Map nodes, edges, NodeRegistry, CanvasEngine, and Toolbar registration."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_CANVAS_DIR = REPO_ROOT / "apps" / "web" / "components" / "canvas"


# 1. Verification of File Existence
MINDMAP_NODE_FILES = [
    "nodes/BaseMindMapNode.tsx",
    "nodes/MindMapIdeaNode.tsx",
    "nodes/MindMapGoalNode.tsx",
    "nodes/MindMapTaskNode.tsx",
    "nodes/MindMapAgentNode.tsx",
    "nodes/MindMapEvidenceNode.tsx",
]

MINDMAP_EDGE_FILES = [
    "edges/DependencyEdge.tsx",
    "edges/RelationEdge.tsx",
    "edges/MilestoneEdge.tsx",
]


@pytest.mark.parametrize("rel_path", MINDMAP_NODE_FILES)
def test_mindmap_node_files_exist(rel_path: str):
    """Verify that all 5 Mind Map node files and base node exist on disk."""
    file_path = WEB_CANVAS_DIR / rel_path
    assert file_path.is_file(), f"Expected node file missing: {rel_path}"
    assert file_path.stat().st_size > 0, f"Node file is empty: {rel_path}"


@pytest.mark.parametrize("rel_path", MINDMAP_EDGE_FILES)
def test_mindmap_edge_files_exist(rel_path: str):
    """Verify that all 3 custom edge files exist on disk."""
    file_path = WEB_CANVAS_DIR / rel_path
    assert file_path.is_file(), f"Expected edge file missing: {rel_path}"
    assert file_path.stat().st_size > 0, f"Edge file is empty: {rel_path}"


# 2. Verification of Component Exports & TypeScript Contracts
def test_mindmap_nodes_exports_and_headers():
    """Verify default export, MRH headers, and data contract interfaces in node components."""
    expected_exports = {
        "nodes/BaseMindMapNode.tsx": ["export default function BaseMindMapNode"],
        "nodes/MindMapIdeaNode.tsx": [
            "export default function MindMapIdeaNode",
            "export interface MindMapIdeaData",
        ],
        "nodes/MindMapGoalNode.tsx": [
            "export default function MindMapGoalNode",
            "export interface MindMapGoalData",
        ],
        "nodes/MindMapTaskNode.tsx": [
            "export default function MindMapTaskNode",
            "export interface MindMapTaskData",
        ],
        "nodes/MindMapAgentNode.tsx": [
            "export default function MindMapAgentNode",
            "export interface MindMapAgentData",
        ],
        "nodes/MindMapEvidenceNode.tsx": [
            "export default function MindMapEvidenceNode",
            "export interface MindMapEvidenceData",
        ],
    }

    for rel_path, symbols in expected_exports.items():
        file_path = WEB_CANVAS_DIR / rel_path
        content = file_path.read_text(encoding="utf-8")
        assert "DNK-MRH-HEADER" in content, f"Missing MRH header in {rel_path}"
        for symbol in symbols:
            assert symbol in content, f"Missing export '{symbol}' in {rel_path}"


def test_mindmap_edges_exports_and_headers():
    """Verify default export and MRH headers in edge components."""
    expected_exports = {
        "edges/DependencyEdge.tsx": [
            "export default function DependencyEdge",
            "export interface DependencyEdgeData",
        ],
        "edges/RelationEdge.tsx": [
            "export default function RelationEdge",
        ],
        "edges/MilestoneEdge.tsx": [
            "export default function MilestoneEdge",
        ],
    }

    for rel_path, symbols in expected_exports.items():
        file_path = WEB_CANVAS_DIR / rel_path
        content = file_path.read_text(encoding="utf-8")
        assert "DNK-MRH-HEADER" in content, f"Missing MRH header in {rel_path}"
        for symbol in symbols:
            assert symbol in content, f"Missing export '{symbol}' in {rel_path}"


# 3. Verification of Registration in NodeRegistry.ts
def test_mindmap_registration_in_node_registry():
    """Verify that all MindMap nodes are registered in NodeRegistry.ts."""
    registry_file = WEB_CANVAS_DIR / "NodeRegistry.ts"
    assert registry_file.is_file(), "NodeRegistry.ts missing"
    content = registry_file.read_text(encoding="utf-8")

    expected_nodes = [
        "BaseMindMapNode",
        "MindMapIdeaNode",
        "MindMapGoalNode",
        "MindMapTaskNode",
        "MindMapAgentNode",
        "MindMapEvidenceNode",
    ]

    for node_name in expected_nodes:
        assert node_name in content, f"{node_name} is not registered or imported in NodeRegistry.ts"


# 4. Verification of Registration in CanvasEngine.tsx
def test_mindmap_registration_in_canvas_engine():
    """Verify that MindMap nodes and custom edges are registered in CanvasEngine.tsx."""
    canvas_file = WEB_CANVAS_DIR / "CanvasEngine.tsx"
    assert canvas_file.is_file(), "CanvasEngine.tsx missing"
    content = canvas_file.read_text(encoding="utf-8")

    # Nodes registered
    expected_node_types = [
        "MindMapIdeaNode",
        "MindMapGoalNode",
        "MindMapTaskNode",
        "MindMapAgentNode",
        "MindMapEvidenceNode",
    ]
    for node in expected_node_types:
        assert node in content, f"CanvasEngine.tsx must register {node}"

    # Edges registered
    expected_edge_types = [
        "DependencyEdge",
        "RelationEdge",
        "MilestoneEdge",
    ]
    for edge in expected_edge_types:
        assert edge in content, f"CanvasEngine.tsx must register {edge}"


# 5. Verification of Quick Spawn Toolbar in StitchSpatialToolbar.tsx
def test_mindmap_quick_spawn_in_toolbar():
    """Verify that StitchSpatialToolbar.tsx includes quick-spawn buttons for all 5 Mind Map nodes."""
    toolbar_file = WEB_CANVAS_DIR / "StitchSpatialToolbar.tsx"
    assert toolbar_file.is_file(), "StitchSpatialToolbar.tsx missing"
    content = toolbar_file.read_text(encoding="utf-8")

    # Verify Mind Map quick spawn items
    expected_items = [
        ("mindmap-idea", "MindMapIdeaNode", "💡"),
        ("mindmap-goal", "MindMapGoalNode", "🎯"),
        ("mindmap-task", "MindMapTaskNode", "✅"),
        ("mindmap-agent", "MindMapAgentNode", "🤖"),
        ("mindmap-evidence", "MindMapEvidenceNode", "📎"),
    ]

    for item_id, node_type, icon_glyph in expected_items:
        assert item_id in content, f"Toolbar missing item id: {item_id}"
        assert node_type in content, f"Toolbar missing nodeType: {node_type}"
        assert icon_glyph in content, f"Toolbar missing glyph: {icon_glyph}"

    # Verify addNode hook integration
    assert "useCanvasStore" in content, "Toolbar must import useCanvasStore"
    assert "addNode" in content, "Toolbar must call addNode for instant node spawning"
