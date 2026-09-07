# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_scones_l3_week2.py"
# purpose: "Verification tests for SCONES L3 Week 2 (Sleep Consolidation Worker & FastAPI Memory Router)"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-SCONES-L3-001", "DNK-SCONES-L3-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.workers.sleep_consolidation_worker import SleepConsolidationWorker
from core.scones_l3_memory import SCONESL3Memory


@pytest.mark.asyncio
async def test_sleep_consolidation_worker():
    scones_l3 = SCONESL3Memory()
    worker = SleepConsolidationWorker(scones_l3=scones_l3)

    user_id = "user-week2-101"
    workspace_id = "ws-week2-001"
    old_time = datetime.now(timezone.utc) - timedelta(days=12)

    # Populate L2 mock memories
    scones_l3._in_memory_l2_store.append({
        "id": "l2-old-1",
        "user_id": user_id,
        "workspace_id": workspace_id,
        "content": "User prefers concise responses without preambles",
        "created_at": old_time,
        "archived": False,
    })

    # Run one consolidation cycle
    result = await worker.run_consolidation_cycle()
    assert result["status"] == "completed"
    assert result["consolidated_users"] >= 1
    assert result["distilled_facts"] >= 1

    # Verify L3 storage received the consolidated memory
    l3_records = await scones_l3.retrieve_memories(
        user_id=user_id,
        workspace_id=workspace_id,
        query="concise responses",
    )
    assert len(l3_records) > 0
    assert "concise responses" in l3_records[0]["content"]


def test_fastapi_memory_l3_endpoints():
    client = TestClient(app)

    # 1. Store memory via REST API
    store_payload = {
        "user_id": "user-rest-001",
        "workspace_id": "ws-rest-001",
        "agent_id": "system",
        "memory_type": "semantic",
        "content": "User prefers architectural cleanliness and standard ports (e.g. port 3000)",
        "metadata": {"importance": "high"},
        "retention_policy": "forever",
    }
    res_store = client.post("/api/v1/memory/l3/store", json=store_payload)
    assert res_store.status_code == 200
    store_data = res_store.json()
    assert store_data["status"] == "success"
    assert "memory_id" in store_data

    # 2. List & hybrid search memories
    res_list = client.get(
        "/api/v1/memory/l3/memories",
        params={
            "user_id": "user-rest-001",
            "workspace_id": "ws-rest-001",
            "query": "port 3000 architectural cleanliness",
        },
    )
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["count"] >= 1
    assert "port 3000" in list_data["memories"][0]["content"]

    # 3. Get Stats
    res_stats = client.get(
        "/api/v1/memory/l3/stats",
        params={"user_id": "user-rest-001", "workspace_id": "ws-rest-001"},
    )
    assert res_stats.status_code == 200
    stats_data = res_stats.json()
    assert stats_data["total"] >= 1
    assert stats_data["avg_recency"] > 0.0

    # 4. Trigger Consolidation
    res_cons = client.post(
        "/api/v1/memory/l3/consolidate",
        json={"user_id": "user-rest-001", "workspace_id": "ws-rest-001", "older_than_days": 7},
    )
    assert res_cons.status_code == 200
    assert res_cons.json()["status"] == "success"
