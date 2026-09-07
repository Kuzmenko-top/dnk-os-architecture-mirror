# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_scones_l3.py"
# purpose: "Verification tests for SCONES L3 SOTA Engine (Native PostgreSQL Long-Term Memory with Temporal Decay and Sleep Consolidation)"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-SCONES-L3-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import math
from datetime import datetime, timezone, timedelta
from core.scones_l3_memory import SCONESL3Memory


@pytest.mark.asyncio
async def test_store_and_retrieve_memory():
    scones_l3 = SCONESL3Memory()
    user_id = "user-alpha-101"
    workspace_id = "ws-alpha-001"

    mem_id = await scones_l3.store_memory(
        user_id=user_id,
        workspace_id=workspace_id,
        agent_id="gerych_builder",
        memory_type="semantic",
        content="User strictly prefers dark mode with emerald green accents in UI",
        metadata={"emotion": "neutral", "importance": "high"},
    )

    assert mem_id is not None
    assert isinstance(mem_id, str)

    # Hybrid retrieve
    memories = await scones_l3.retrieve_memories(
        user_id=user_id,
        workspace_id=workspace_id,
        query="dark mode emerald theme preference",
        top_k=5,
    )

    assert len(memories) > 0
    top_hit = memories[0]
    assert "dark mode" in top_hit["content"]
    assert top_hit["recency_score"] == 1.0
    assert top_hit["final_score"] > 0.0


@pytest.mark.asyncio
async def test_temporal_decay():
    scones_l3 = SCONESL3Memory(decay_lambda=0.1)
    user_id = "user-beta-202"
    workspace_id = "ws-alpha-001"

    # Create memory from 14 days ago (2 half-lives)
    old_time = datetime.now(timezone.utc) - timedelta(days=14)
    mem_id = await scones_l3.store_memory(
        user_id=user_id,
        workspace_id=workspace_id,
        content="Old architectural preference for port 3000",
        created_at=old_time,
    )

    # Apply decay
    updated = await scones_l3.apply_temporal_decay()
    assert updated >= 1

    decayed_mem = scones_l3._in_memory_l3_store[mem_id]
    # Expected score: exp(-0.1 * 14) = exp(-1.4) ≈ 0.246
    expected_score = math.exp(-0.1 * 14)
    assert pytest.approx(decayed_mem["recency_score"], rel=1e-2) == expected_score


@pytest.mark.asyncio
async def test_sleep_consolidation():
    scones_l3 = SCONESL3Memory()
    user_id = "user-gamma-303"
    workspace_id = "ws-alpha-001"

    # Seed old L2 memories (10 days old)
    old_time = datetime.now(timezone.utc) - timedelta(days=10)
    scones_l3._in_memory_l2_store = [
        {
            "id": "l2-1",
            "user_id": user_id,
            "workspace_id": workspace_id,
            "content": "User prefers dark mode on macOS UI components",
            "created_at": old_time,
            "archived": False,
        },
        {
            "id": "l2-2",
            "user_id": user_id,
            "workspace_id": workspace_id,
            "content": "User adjusted UI theme to high contrast dark mode",
            "created_at": old_time,
            "archived": False,
        },
    ]

    # Run sleep consolidation
    distilled = await scones_l3.consolidate_memories(
        user_id=user_id,
        workspace_id=workspace_id,
        older_than_days=7,
    )

    assert len(distilled) > 0
    assert scones_l3._in_memory_l2_store[0]["archived"] is True
    assert scones_l3._in_memory_l2_store[1]["archived"] is True

    # Check L3 long-term memory presence
    l3_memories = await scones_l3.retrieve_memories(
        user_id=user_id,
        workspace_id=workspace_id,
        query="ui theme preference dark mode",
    )

    assert len(l3_memories) > 0
    assert l3_memories[0]["metadata"].get("consolidated_from") == "L2"


@pytest.mark.asyncio
async def test_workspace_isolation():
    scones_l3 = SCONESL3Memory()

    # User in Workspace A
    await scones_l3.store_memory(
        user_id="user-1",
        workspace_id="ws-A",
        content="Secret project codename is ORION",
    )

    # Query from Workspace B
    ws_b_results = await scones_l3.retrieve_memories(
        user_id="user-1",
        workspace_id="ws-B",
        query="ORION codename",
    )

    assert len(ws_b_results) == 0
