# --- DNK-MRH-HEADER ---
# mrh_id: "tests_platform_test_platform_scaling"
# purpose: "Comprehensive test suite for PostgreSQL Read Replicas, Tenant Sharding, Redis Cluster/PubSub, and TenantRouter middleware"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.db.database import DatabaseManager, PoolRole
from apps.api.db.sharding import TenantShardRouter
from apps.api.services.redis_client import RedisClient
from apps.api.services.redis_pubsub import RedisPubSubManager
from apps.api.services.workspace_lock_manager import WorkspaceLockManager
from apps.api.services.workspace_collaboration_hub import WorkspaceCollaborationHub
from apps.api.middleware.tenant_router import TenantRouterMiddleware


@pytest.mark.asyncio
async def test_database_manager_replicas_fallback():
    db = DatabaseManager()
    # Mock master pool
    mock_master_pool = MagicMock()
    mock_master_pool.acquire = AsyncMock()
    mock_master_pool._closed = False
    db.master_pool = mock_master_pool
    db._is_connected = True

    # With no replicas configured, get_pool(PoolRole.REPLICA) should fallback to master_pool
    replica_pool = db.get_pool(PoolRole.REPLICA)
    assert replica_pool == mock_master_pool

    # Adding mock replica pools
    mock_replica_1 = MagicMock()
    mock_replica_1._closed = False
    mock_replica_2 = MagicMock()
    mock_replica_2._closed = False
    db.replica_pools = [mock_replica_1, mock_replica_2]

    # Selected pool should be one of the replica pools
    selected = db.get_pool(PoolRole.REPLICA)
    assert selected in [mock_replica_1, mock_replica_2]
    assert db.get_replica_count() == 2


@pytest.mark.asyncio
async def test_tenant_shard_router_hashing():
    router = TenantShardRouter(num_shards=4)
    shard_alpha = router.get_shard_for_tenant("tenant-alpha-001")
    shard_beta = router.get_shard_for_tenant("tenant-beta-002")

    assert 0 <= shard_alpha < 4
    assert 0 <= shard_beta < 4

    # Determinism test
    assert router.get_shard_for_tenant("tenant-alpha-001") == shard_alpha

    # Stats test
    stats = router.get_shard_distribution_stats()
    assert stats["num_shards"] == 4


@pytest.mark.asyncio
async def test_redis_client_fallback_mode():
    client = RedisClient()
    await client.init()

    # In test environment without Redis server, client falls back to InMemoryRedisFallback
    assert client.is_connected is True
    assert client.fallback is not None

    ping_res = await client.ping()
    assert ping_res is True

    health = await client.health_check()
    assert health["status"] in ("healthy", "healthy_fallback")


@pytest.mark.asyncio
async def test_redis_pubsub_broadcast():
    pubsub = RedisPubSubManager()
    await pubsub.init()

    received_events = []

    async def sample_handler(msg: dict):
        received_events.append(msg)

    channel = "dnk:test:channel"
    await pubsub.subscribe(channel, sample_handler)

    test_msg = {"event": "USER_JOINED", "user_id": "usr-1001"}
    await pubsub.publish(channel, test_msg)

    await asyncio.sleep(0.05)
    assert len(received_events) == 1
    assert received_events[0]["event"] == "USER_JOINED"

    await pubsub.close()


@pytest.mark.asyncio
async def test_workspace_lock_manager_cluster_tagging():
    lock_mgr = WorkspaceLockManager()

    # Acquire section lock
    res = await lock_mgr.acquire_lock(
        workspace_id="ws-alpha",
        section_id="sec-canvas",
        user_id="user-alice",
        ttl_seconds=10
    )
    assert res["success"] is True

    # Conflicting lock attempt
    conflict = await lock_mgr.acquire_lock(
        workspace_id="ws-alpha",
        section_id="sec-canvas",
        user_id="user-bob",
        ttl_seconds=10
    )
    assert conflict["success"] is False
    assert conflict["conflict"]["user_id"] == "user-alice"

    # Release lock
    rel = await lock_mgr.release_lock(
        workspace_id="ws-alpha",
        section_id="sec-canvas",
        user_id="user-alice"
    )
    assert rel is True


@pytest.mark.asyncio
async def test_cross_node_workspace_hub_sync():
    hub_1 = WorkspaceCollaborationHub()
    hub_2 = WorkspaceCollaborationHub()

    # Share pubsub manager for simulating multi-node bus
    pubsub = RedisPubSubManager()
    await pubsub.init()

    hub_1.pubsub_manager = pubsub
    hub_2.pubsub_manager = pubsub

    workspace_id = "ws-sync-101"

    # Mock WebSocket for hub_2
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock()

    await hub_2.connect(workspace_id=workspace_id, user_id="user-charlie", websocket=mock_ws)

    # Broadcast from node 1
    broadcast_payload = {"type": "PRESENCE_UPDATE", "user": "Charlie"}
    await hub_1.broadcast(workspace_id=workspace_id, message=broadcast_payload)

    for _ in range(20):
        if mock_ws.send_json.called:
            break
        await asyncio.sleep(0.05)

    assert mock_ws.send_json.called

    await pubsub.close()


def test_tenant_router_middleware():
    app = FastAPI()
    app.add_middleware(TenantRouterMiddleware)

    @app.get("/api/v1/test")
    async def test_route():
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/api/v1/test", headers={"X-Tenant-Id": "tenant-enterprise-99"})

    assert response.status_code == 200
    assert response.headers.get("X-Tenant-Shard") is not None
