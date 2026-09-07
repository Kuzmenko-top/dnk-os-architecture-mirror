# --- DNK-MRH-HEADER ---
# mrh_id: "tests/test_beads_adapter.py"
# purpose: "Unit tests for the Beads and Dolt Adapter (topological sort, atomic claiming, memory)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import tempfile
import pytest
from adapters.beads_adapter import BeadsAdapter


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for test execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_beads_adapter_initialization(temp_workspace):
    """Test that beads directory and database initialize correctly."""
    adapter = BeadsAdapter(workspace_root=temp_workspace)
    assert os.path.exists(adapter.beads_dir)
    assert os.path.exists(adapter.db_path)


def test_beads_creation_and_retrieval(temp_workspace):
    """Test creating a bead and retrieving it."""
    adapter = BeadsAdapter(workspace_root=temp_workspace)
    
    # Create main Epic bead
    epic = adapter.create_bead(
        id_prefix="bd-a3f8",
        title="Launch Shopify PDP",
        description="E-commerce Product Detail Page launch sequence",
        metadata={"priority": "high", "tier": "Epic"}
    )
    assert epic["id"].startswith("bd-a3f8-")
    assert epic["title"] == "Launch Shopify PDP"
    assert epic["status"] == "open"
    assert epic["metadata"]["tier"] == "Epic"

    # Create hierarchical child (Task)
    task = adapter.create_bead(
        id_prefix="bd-a3f8",
        title="Design Liquid Layout",
        parent_id=epic["id"],
        metadata={"tier": "Task"}
    )
    assert task["id"] == f"{epic['id']}.1"
    assert task["parent_id"] == epic["id"]


def test_beads_topological_sort_and_unblocking(temp_workspace):
    """Test that get_ready_beads returns only unblocked beads based on dependencies."""
    adapter = BeadsAdapter(workspace_root=temp_workspace)
    
    # Bead A: Design Liquid Layout
    bead_a = adapter.create_bead(id_prefix="bd-a1", title="Design Liquid Layout")
    # Bead B: Transpile Web Canvas -> depends on A
    bead_b = adapter.create_bead(
        id_prefix="bd-b1",
        title="Transpile Web Canvas",
        dependencies=[bead_a["id"]]
    )
    
    # Initially, only Bead A should be ready
    ready = adapter.get_ready_beads()
    ready_ids = [b["id"] for b in ready]
    assert bead_a["id"] in ready_ids
    assert bead_b["id"] not in ready_ids
    
    # Close Bead A (Design Liquid Layout)
    success = adapter.close_bead(bead_a["id"])
    assert success is True
    
    # Now, Bead B should be unblocked and ready
    ready = adapter.get_ready_beads()
    ready_ids = [b["id"] for b in ready]
    assert bead_b["id"] in ready_ids


def test_beads_atomic_claiming(temp_workspace):
    """Test that claiming is atomic and prevents multiple claims on the same bead."""
    adapter = BeadsAdapter(workspace_root=temp_workspace)
    bead = adapter.create_bead(id_prefix="bd-claim", title="Test Claiming")
    
    # Agent 1 claims first
    claim_1 = adapter.claim_bead(bead["id"], assignee="gerych_builder")
    assert claim_1 is True
    
    # Agent 2 attempts to claim the same bead
    claim_2 = adapter.claim_bead(bead["id"], assignee="dnk_shopify")
    assert claim_2 is False
    
    # Verify the bead state is owned by Agent 1
    updated_bead = adapter.get_bead(bead["id"])
    assert updated_bead is not None
    assert updated_bead["status"] == "in_progress"
    assert updated_bead["assignee"] == "gerych_builder"
    assert updated_bead["claimed_at"] is not None


def test_beads_memories(temp_workspace):
    """Test storing and retrieving insights/memories associated with beads."""
    adapter = BeadsAdapter(workspace_root=temp_workspace)
    bead = adapter.create_bead(id_prefix="bd-memo", title="Test Memory Linkage")
    
    # Store an insight
    memory_id = adapter.remember_insight(
        insight="Avoid using direct rsync in Shopify checkout, use standard CLI sync.",
        author="gerych_builder",
        bead_id=bead["id"]
    )
    assert memory_id > 0
    
    # Retrieve memories
    memos = adapter.get_memories(bead_id=bead["id"])
    assert len(memos) == 1
    assert memos[0]["insight"] == "Avoid using direct rsync in Shopify checkout, use standard CLI sync."
    assert memos[0]["author"] == "gerych_builder"
