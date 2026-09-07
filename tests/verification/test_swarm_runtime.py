# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-DNK-A2A-002"
# purpose: "Unit and Integration Tests for Swarm Runtime 14-Agent Orchestrator"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Auditor"
# --- END DNK-MRH-HEADER ---

import pytest

from apps.api.services.a2a_protocol_engine import (
    CommunicationPattern,
    ConsensusMechanism,
    ProposalStatus,
)
from apps.api.services.swarm_runtime import CANONICAL_SWARM_AGENTS, SwarmRuntime


def test_swarm_runtime_agent_registration():
    runtime = SwarmRuntime()
    assert len(runtime.agents) == 14
    assert "gerych_auditor" in runtime.agents
    assert "gerych_builder" in runtime.agents
    assert "antigravity_supervisor" in runtime.agents
    assert "dnk_dev_fullstack" in runtime.agents
    assert "dnk_shopify" in runtime.agents
    assert "dnk_security_guard" in runtime.agents

    agents_list = runtime.list_agents()
    assert len(agents_list) == 14
    auditor_meta = next(a for a in agents_list if a["name"] == "gerych_auditor")
    assert auditor_meta["consensus_weight"] == 5.0
    assert "red_teaming" in auditor_meta["capabilities"]


@pytest.mark.asyncio
async def test_swarm_p2p_message_flow():
    runtime = SwarmRuntime()
    msg = await runtime.send_message(
        sender="gerych_auditor",
        recipients=["gerych_builder"],
        method="agent.review_findings",
        params={"severity": "LOW", "diff_clean": True},
        pattern=CommunicationPattern.P2P,
    )
    assert msg.sender == "gerych_auditor"

    received = await runtime.receive_next("gerych_builder", timeout_s=0.5)
    assert received is not None
    assert received.sender == "gerych_auditor"
    assert received.params["diff_clean"] is True


@pytest.mark.asyncio
async def test_swarm_broadcast_alert():
    runtime = SwarmRuntime()
    alert_payload = {"type": "FIREWALL_TRIGGER", "source_ip": "192.168.1.100"}
    msg = await runtime.broadcast_alert(
        sender="dnk_security_guard",
        alert=alert_payload,
        severity="CRITICAL",
    )
    assert msg.pattern == CommunicationPattern.BROADCAST

    # Check that builder and auditor received the broadcast
    builder_msg = await runtime.receive_next("gerych_builder", timeout_s=0.5)
    assert builder_msg is not None
    assert builder_msg.params["severity"] == "CRITICAL"

    auditor_msg = await runtime.receive_next("gerych_auditor", timeout_s=0.5)
    assert auditor_msg is not None
    assert auditor_msg.params["alert"]["type"] == "FIREWALL_TRIGGER"


@pytest.mark.asyncio
async def test_swarm_supervisor_worker_delegation():
    runtime = SwarmRuntime()
    workers = ["dnk_dev_fullstack", "gerych_builder", "dnk_qa_agent"]
    task_payload = {"task_id": "TASK-A2A-99", "action": "GENERATE_ENDPOINTS"}

    msg = await runtime.delegate_task(
        supervisor="antigravity_supervisor",
        workers=workers,
        task_payload=task_payload,
    )
    assert msg.pattern == CommunicationPattern.SUPERVISOR_WORKER

    for w in workers:
        w_msg = await runtime.receive_next(w, timeout_s=0.5)
        assert w_msg is not None
        assert w_msg.params["task_id"] == "TASK-A2A-99"


@pytest.mark.asyncio
async def test_swarm_pubsub_topic_events():
    runtime = SwarmRuntime()
    runtime.message_router.subscribe_topic("deployments.production", "dnk_ops_agent")
    runtime.message_router.subscribe_topic("deployments.production", "gerych_auditor")

    msg = await runtime.publish_event(
        sender="antigravity_supervisor",
        topic="deployments.production",
        payload={"version": "v5.0.0-rc1", "cluster": "k8s-prod"},
    )
    assert msg.topic == "deployments.production"

    ops_msg = await runtime.receive_next("dnk_ops_agent", timeout_s=0.5)
    assert ops_msg is not None
    assert ops_msg.params["version"] == "v5.0.0-rc1"


def test_swarm_consensus_flow():
    runtime = SwarmRuntime()
    prop = runtime.request_consensus(
        proposer="antigravity_supervisor",
        topic="security.firewall_rule_change",
        description="Allow outbound webhook to external API",
        mechanism=ConsensusMechanism.WEIGHTED,
        threshold=0.5,
        participants=["gerych_auditor", "gerych_builder", "dnk_dev_fullstack"],
    )
    assert prop.status == ProposalStatus.PENDING

    # Builder approves (weight 2.0)
    runtime.vote_consensus(prop.proposal_id, "gerych_builder", "approve")
    # Auditor rejects (weight 5.0 -> majority veto)
    updated_prop = runtime.vote_consensus(
        prop.proposal_id,
        "gerych_auditor",
        "reject",
        rationale="Unauthenticated webhook URL",
    )
    assert updated_prop.status == ProposalStatus.REJECTED


def test_swarm_distributed_locking_flow():
    runtime = SwarmRuntime()
    res = "database_schema_migration_lock"

    # 1. Dev acquires lock
    acquired = runtime.acquire_resource_lock(resource=res, agent="dnk_dev_fullstack", ttl_seconds=10.0)
    assert acquired is True

    # 2. Builder fails to acquire same resource
    blocked = runtime.acquire_resource_lock(resource=res, agent="gerych_builder", ttl_seconds=10.0)
    assert blocked is False

    # 3. Dev renews heartbeat
    renewed = runtime.renew_resource_lock(resource=res, agent="dnk_dev_fullstack")
    assert renewed is True

    # 4. Check active locks
    active_locks = runtime.get_active_locks()
    assert len(active_locks) >= 1
    assert any(l["resource"] == res and l["owner"] == "dnk_dev_fullstack" for l in active_locks)

    # 5. Dev releases lock
    released = runtime.release_resource_lock(resource=res, agent="dnk_dev_fullstack")
    assert released is True

    # 6. Builder can now acquire
    acquired_builder = runtime.acquire_resource_lock(resource=res, agent="gerych_builder", ttl_seconds=10.0)
    assert acquired_builder is True
