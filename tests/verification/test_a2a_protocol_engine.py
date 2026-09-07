# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-DNK-A2A-001"
# purpose: "Comprehensive Unit & Integration Test Suite for Multi-Agent A2A Protocol Engine (P2P, Supervisor-Worker, Broadcast, PubSub, Consensus, Locks)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Auditor"
# --- END DNK-MRH-HEADER ---

import asyncio
import pytest

from apps.api.services.a2a_protocol_engine import (
    A2AMessage,
    CommunicationPattern,
    ConsensusEngine,
    ConsensusMechanism,
    DistributedLockManager,
    MessageRouter,
    ProposalStatus,
    RedisPubSubRouter,
)


def test_a2a_message_serialization():
    msg = A2AMessage(
        method="agent.code_review",
        params={"pr_id": 42, "findings": 0},
        sender="gerych_auditor",
        recipients=["gerych_builder"],
        pattern=CommunicationPattern.P2P,
    )
    wire = msg.serialize_rpc()
    assert "jsonrpc" in wire
    assert "2.0" in wire
    assert "gerych_auditor" in wire

    reconstructed = A2AMessage.deserialize_rpc(wire)
    assert reconstructed.id == msg.id
    assert reconstructed.sender == "gerych_auditor"
    assert reconstructed.recipients == ["gerych_builder"]
    assert reconstructed.params["pr_id"] == 42


@pytest.mark.asyncio
async def test_message_router_p2p():
    router = MessageRouter()
    msg = A2AMessage(
        method="agent.review_request",
        params={"module": "a2a_protocol_engine.py"},
        sender="gerych_builder",
        recipients=["gerych_auditor"],
        pattern=CommunicationPattern.P2P,
    )
    delivered = await router.route(msg)
    assert delivered == ["gerych_auditor"]

    received = await router.receive("gerych_auditor", timeout_s=0.5)
    assert received is not None
    assert received.sender == "gerych_builder"
    assert received.params["module"] == "a2a_protocol_engine.py"

    # Verify telemetry record
    telemetry = router.get_telemetry()
    assert len(telemetry) == 1
    assert telemetry[0].sender == "gerych_builder"
    assert telemetry[0].recipient == "gerych_auditor"
    assert telemetry[0].pattern == CommunicationPattern.P2P


@pytest.mark.asyncio
async def test_message_router_supervisor_worker():
    router = MessageRouter()
    workers = ["dnk_dev_fullstack", "gerych_builder", "dnk_shopify"]
    msg = A2AMessage(
        method="supervisor.delegate_task",
        params={"task": "DNK-TASK-849", "goal": "Build Payment Router"},
        sender="antigravity_supervisor",
        recipients=workers,
        pattern=CommunicationPattern.SUPERVISOR_WORKER,
    )
    delivered = await router.route(msg)
    assert set(delivered) == set(workers)

    for w in workers:
        worker_msg = await router.receive(w, timeout_s=0.5)
        assert worker_msg is not None
        assert worker_msg.sender == "antigravity_supervisor"
        assert worker_msg.params["task"] == "DNK-TASK-849"


@pytest.mark.asyncio
async def test_message_router_broadcast():
    router = MessageRouter(known_agents=["agent_1", "agent_2", "agent_3", "sender_agent"])
    msg = A2AMessage(
        method="system.security_alert",
        params={"severity": "CRITICAL", "action": "HALT_WRITES"},
        sender="sender_agent",
        pattern=CommunicationPattern.BROADCAST,
    )
    delivered = await router.route(msg)
    assert "sender_agent" not in delivered
    assert set(delivered) == {"agent_1", "agent_2", "agent_3"}

    for ag in ["agent_1", "agent_2", "agent_3"]:
        recv = await router.receive(ag, timeout_s=0.5)
        assert recv is not None
        assert recv.params["severity"] == "CRITICAL"


@pytest.mark.asyncio
async def test_message_router_pubsub():
    router = MessageRouter()
    router.subscribe_topic("deployments.production", "gerych_auditor")
    router.subscribe_topic("deployments.production", "dnk_security_guard")

    msg = A2AMessage(
        method="event.deploy_initiated",
        params={"version": "v5.0.0", "target": "cluster_us_east"},
        sender="antigravity_supervisor",
        topic="deployments.production",
        pattern=CommunicationPattern.PUBSUB,
    )
    delivered = await router.route(msg)
    assert set(delivered) == {"gerych_auditor", "dnk_security_guard"}

    auditor_recv = await router.receive("gerych_auditor", timeout_s=0.5)
    assert auditor_recv is not None
    assert auditor_recv.topic == "deployments.production"


@pytest.mark.asyncio
async def test_message_router_dlq_on_unknown_recipient():
    router = MessageRouter()
    msg = A2AMessage(
        method="agent.ping",
        sender="gerych_builder",
        recipients=["non_existent_agent_99"],
        pattern=CommunicationPattern.P2P,
    )
    delivered = await router.route(msg)
    assert delivered == []

    dlq = router.get_dlq()
    assert len(dlq) == 1
    assert dlq[0].message_id == msg.id
    assert "non_existent_agent_99" in dlq[0].error_reason


@pytest.mark.asyncio
async def test_redis_pubsub_router_mock_fallback():
    redis_router = RedisPubSubRouter(redis_url="redis://localhost:9999", use_mock_fallback=True)
    connected = await redis_router.connect()
    assert connected is True

    test_msg = A2AMessage(
        method="agent.telemetry_ping",
        params={"ping": "pong"},
        sender="gerych_builder",
        recipients=["gerych_auditor"],
    )

    # Subscribe & publish in background
    async def subscriber():
        async for m in redis_router.subscribe("telemetry_channel"):
            return m

    sub_task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.05)
    await redis_router.publish("telemetry_channel", test_msg)

    received_msg = await asyncio.wait_for(sub_task, timeout=1.0)
    assert received_msg is not None
    assert received_msg.sender == "gerych_builder"
    assert received_msg.params["ping"] == "pong"
    await redis_router.close()


def test_consensus_engine_majority_and_unanimous():
    engine = ConsensusEngine()
    participants = ["gerych_auditor", "gerych_builder", "dnk_dev_fullstack"]

    # 1. Majority vote
    prop = engine.create_proposal(
        topic="architecture.switch_to_next15",
        description="Migrate frontend to Next.js 15 App Router",
        participants=participants,
        mechanism=ConsensusMechanism.MAJORITY_VOTE,
        threshold=0.5,
    )
    engine.cast_vote(prop.proposal_id, "gerych_auditor", "approve")
    prop_state = engine.cast_vote(prop.proposal_id, "gerych_builder", "approve")
    assert prop_state.status == ProposalStatus.ACCEPTED

    # 2. Unanimous vote rejection
    prop_sec = engine.create_proposal(
        topic="security.allow_anonymous_upload",
        description="Permit anonymous avatar upload",
        participants=participants,
        mechanism=ConsensusMechanism.UNANIMOUS,
    )
    engine.cast_vote(prop_sec.proposal_id, "gerych_builder", "approve")
    prop_sec_state = engine.cast_vote(prop_sec.proposal_id, "gerych_auditor", "reject", rationale="Security risk")
    assert prop_sec_state.status == ProposalStatus.REJECTED


def test_consensus_engine_weighted():
    engine = ConsensusEngine(default_weights={"gerych_auditor": 5.0, "guest_agent": 1.0})
    prop = engine.create_proposal(
        topic="security.override_firewall",
        description="Bypass rate limiter",
        participants=["gerych_auditor", "guest_agent"],
        mechanism=ConsensusMechanism.WEIGHTED,
        threshold=0.5,
    )
    # Guest approves (weight 1/6) -> still pending/not enough
    engine.cast_vote(prop.proposal_id, "guest_agent", "approve")
    # Auditor rejects (weight 5/6) -> rejected
    prop_eval = engine.cast_vote(prop.proposal_id, "gerych_auditor", "reject")
    assert prop_eval.status == ProposalStatus.REJECTED


def test_distributed_lock_manager():
    lock_mgr = DistributedLockManager()
    res = "shared_config_file_v1"

    # 1. Acquire
    assert lock_mgr.acquire_lock(res, owner_agent="gerych_builder", ttl_seconds=5.0) is True
    assert lock_mgr.is_locked(res) is True

    # 2. Conflict rejection
    assert lock_mgr.acquire_lock(res, owner_agent="dnk_dev_fullstack", ttl_seconds=5.0) is False

    # 3. Heartbeat renewal
    assert lock_mgr.renew_heartbeat(res, owner_agent="gerych_builder") is True
    assert lock_mgr.renew_heartbeat(res, owner_agent="dnk_dev_fullstack") is False

    # 4. Release
    assert lock_mgr.release_lock(res, owner_agent="gerych_builder") is True
    assert lock_mgr.is_locked(res) is False
    assert lock_mgr.acquire_lock(res, owner_agent="dnk_dev_fullstack", ttl_seconds=5.0) is True
