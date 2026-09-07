# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-001"
# purpose: "Core Multi-Agent A2A Protocol Engine (P2P, Supervisor-Worker, Broadcast, PubSub, Redis PubSub, Consensus, Telemetry)"
# canonical_source: true
# alters_files: ["apps/api/services/a2a_protocol_engine.py"]
# triggers_tasks: ["DNK-A2A-001-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger("dnk.a2a.engine")


class CommunicationPattern(str, Enum):
    P2P = "peer-to-peer"
    SUPERVISOR_WORKER = "supervisor-worker"
    BROADCAST = "broadcast"
    PUBSUB = "pubsub"


class ConsensusMechanism(str, Enum):
    MAJORITY_VOTE = "majority-vote"
    UNANIMOUS = "unanimous"
    WEIGHTED = "weighted"


class ProposalStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class A2AMessage(BaseModel):
    jsonrpc: str = "2.0"
    method: str = "agent.message"
    params: Dict[str, Any] = Field(default_factory=dict)
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    trace_id: str = Field(default_factory=lambda: f"trc_{uuid.uuid4().hex[:8]}")
    span_id: str = Field(default_factory=lambda: f"spn_{uuid.uuid4().hex[:8]}")
    parent_span_id: Optional[str] = None
    sender: str
    recipients: List[str] = Field(default_factory=list)
    pattern: CommunicationPattern = CommunicationPattern.P2P
    topic: Optional[str] = None
    timeout_ms: int = 5000
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def serialize_rpc(self) -> str:
        """Serializes message to standard JSON-RPC 2.0 / A2A-ML-001 wire string."""
        return self.model_dump_json()

    @classmethod
    def deserialize_rpc(cls, raw_json: str) -> "A2AMessage":
        """Deserializes JSON-RPC 2.0 payload into validated A2AMessage."""
        return cls.model_validate_json(raw_json)


class A2ADeadLetter(BaseModel):
    message_id: str
    trace_id: str
    raw_payload: Dict[str, Any]
    error_reason: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class A2ATelemetryRecord(BaseModel):
    trace_id: str
    span_id: str
    sender: str
    recipient: str
    pattern: CommunicationPattern
    topic: Optional[str] = None
    latency_ms: float = 0.0
    status: str = "delivered"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class A2AConsensusVote(BaseModel):
    voter_agent: str
    vote: str  # "approve", "reject", "abstain"
    weight: float = 1.0
    rationale: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class A2AConsensusProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: f"prop_{uuid.uuid4().hex[:8]}")
    topic: str
    description: str
    mechanism: ConsensusMechanism = ConsensusMechanism.MAJORITY_VOTE
    threshold: float = 0.5  # 0.5 for >50%, 0.66 for 2/3, 1.0 for unanimous
    participants: List[str] = Field(default_factory=list)
    votes: Dict[str, A2AConsensusVote] = Field(default_factory=dict)
    status: ProposalStatus = ProposalStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MessageRouter:
    """Enterprise In-Memory A2A Message Router supporting P2P, Supervisor-Worker, Broadcast, and PubSub."""

    def __init__(self, known_agents: Optional[List[str]] = None):
        self._mailboxes: Dict[str, asyncio.Queue] = {}
        self._topic_subscribers: Dict[str, Set[str]] = {}
        self._dlq: List[A2ADeadLetter] = []
        self._telemetry: List[A2ATelemetryRecord] = []
        self._active_agents: Set[str] = set()

        default_agents = [
            "gerych_builder",
            "gerych_researcher",
            "gerych_auditor",
            "dnk_dev_fullstack",
            "dnk_shopify",
            "dnk_video_ai_creator",
            "dnk_security_guard",
            "dnk_scones_memory",
            "antigravity_supervisor",
        ]
        for ag in known_agents or default_agents:
            self.register_agent(ag)

    def register_agent(self, agent_name: str) -> None:
        if agent_name not in self._mailboxes:
            self._mailboxes[agent_name] = asyncio.Queue()
            self._active_agents.add(agent_name)

    def subscribe_topic(self, topic: str, agent_name: str) -> None:
        self.register_agent(agent_name)
        if topic not in self._topic_subscribers:
            self._topic_subscribers[topic] = set()
        self._topic_subscribers[topic].add(agent_name)

    def unsubscribe_topic(self, topic: str, agent_name: str) -> None:
        if topic in self._topic_subscribers and agent_name in self._topic_subscribers[topic]:
            self._topic_subscribers[topic].remove(agent_name)

    async def route(self, message: A2AMessage) -> List[str]:
        """Routes message based on its pattern and returns list of delivered agents."""
        start_time = time.perf_counter()
        delivered_to: List[str] = []

        try:
            if message.pattern == CommunicationPattern.P2P:
                for recipient in message.recipients:
                    if recipient in self._mailboxes:
                        await self._mailboxes[recipient].put(message)
                        delivered_to.append(recipient)
                    else:
                        self._push_to_dlq(message, f"Recipient agent '{recipient}' is not registered.")

            elif message.pattern == CommunicationPattern.SUPERVISOR_WORKER:
                for worker in message.recipients:
                    if worker in self._mailboxes:
                        await self._mailboxes[worker].put(message)
                        delivered_to.append(worker)
                    else:
                        self._push_to_dlq(message, f"Worker agent '{worker}' not found for supervisor delegation.")

            elif message.pattern == CommunicationPattern.BROADCAST:
                for ag in self._active_agents:
                    if ag != message.sender:
                        await self._mailboxes[ag].put(message)
                        delivered_to.append(ag)

            elif message.pattern == CommunicationPattern.PUBSUB:
                topic = message.topic or "default"
                subs = self._topic_subscribers.get(topic, set())
                for sub in subs:
                    if sub in self._mailboxes:
                        await self._mailboxes[sub].put(message)
                        delivered_to.append(sub)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            for r in delivered_to:
                self._telemetry.append(
                    A2ATelemetryRecord(
                        trace_id=message.trace_id,
                        span_id=message.span_id,
                        sender=message.sender,
                        recipient=r,
                        pattern=message.pattern,
                        topic=message.topic,
                        latency_ms=round(elapsed_ms, 3),
                        status="delivered",
                    )
                )

        except Exception as exc:
            self._push_to_dlq(message, str(exc))

        return delivered_to

    async def receive(self, agent_name: str, timeout_s: float = 1.0) -> Optional[A2AMessage]:
        if agent_name not in self._mailboxes:
            return None
        try:
            return await asyncio.wait_for(self._mailboxes[agent_name].get(), timeout=timeout_s)
        except asyncio.TimeoutError:
            return None

    def _push_to_dlq(self, message: A2AMessage, reason: str) -> None:
        self._dlq.append(
            A2ADeadLetter(
                message_id=message.id,
                trace_id=message.trace_id,
                raw_payload=message.model_dump(),
                error_reason=reason,
            )
        )

    def get_dlq(self) -> List[A2ADeadLetter]:
        return list(self._dlq)

    def get_telemetry(self, trace_id: Optional[str] = None) -> List[A2ATelemetryRecord]:
        if trace_id:
            return [t for t in self._telemetry if t.trace_id == trace_id]
        return list(self._telemetry)

    def list_active_topics(self) -> List[str]:
        return list(self._topic_subscribers.keys())


class RedisPubSubRouter:
    """Redis-backed PubSub Router for distributed A2A communication with in-memory fallback."""

    def __init__(self, redis_url: str = "redis://localhost:6379", use_mock_fallback: bool = True):
        self.redis_url = redis_url
        self.use_mock_fallback = use_mock_fallback
        self._redis_client = None
        self._mock_channels: Dict[str, asyncio.Queue] = {}
        self._connected = False

    async def connect(self) -> bool:
        try:
            import redis.asyncio as aioredis  # type: ignore[import-untyped,import-not-found]
            self._redis_client = aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True, socket_connect_timeout=0.5
            )
            await self._redis_client.ping()
            self._connected = True
            logger.info("Connected to Redis at %s", self.redis_url)
            return True
        except Exception as exc:
            if self.use_mock_fallback:
                logger.warning("Redis connection failed (%s). Falling back to Async In-Memory PubSub.", exc)
                self._connected = False
                return True
            raise

    async def publish(self, channel: str, message: A2AMessage) -> int:
        payload = message.serialize_rpc()
        if self._connected and self._redis_client:
            try:
                return await self._redis_client.publish(channel, payload)
            except Exception:
                pass
        
        # Fallback to mock channel
        if channel not in self._mock_channels:
            self._mock_channels[channel] = asyncio.Queue()
        await self._mock_channels[channel].put(payload)
        return 1

    async def subscribe(self, channel: str) -> AsyncIterator[A2AMessage]:
        if self._connected and self._redis_client:
            pubsub = self._redis_client.pubsub()
            await pubsub.subscribe(channel)
            try:
                async for item in pubsub.listen():
                    if item and item.get("type") == "message":
                        yield A2AMessage.deserialize_rpc(item["data"])
            finally:
                await pubsub.unsubscribe(channel)
        else:
            if channel not in self._mock_channels:
                self._mock_channels[channel] = asyncio.Queue()
            while True:
                data = await self._mock_channels[channel].get()
                yield A2AMessage.deserialize_rpc(data)

    async def close(self) -> None:
        if self._connected and self._redis_client:
            await self._redis_client.close()


class ConsensusEngine:
    """Consensus voting engine for multi-agent swarm decisions."""

    def __init__(self, default_weights: Optional[Dict[str, float]] = None):
        self._proposals: Dict[str, A2AConsensusProposal] = {}
        self.weights: Dict[str, float] = default_weights or {
            "gerych_auditor": 3.0,
            "gerych_builder": 2.5,
            "dnk_dev_fullstack": 2.5,
            "antigravity_supervisor": 3.0,
            "dnk_security_guard": 3.0,
        }

    def create_proposal(
        self,
        topic: str,
        description: str,
        participants: List[str],
        mechanism: ConsensusMechanism = ConsensusMechanism.MAJORITY_VOTE,
        threshold: float = 0.5,
    ) -> A2AConsensusProposal:
        proposal = A2AConsensusProposal(
            topic=topic,
            description=description,
            participants=participants,
            mechanism=mechanism,
            threshold=threshold,
        )
        self._proposals[proposal.proposal_id] = proposal
        return proposal

    def cast_vote(
        self,
        proposal_id: str,
        voter_agent: str,
        vote: str,  # "approve", "reject", "abstain"
        rationale: Optional[str] = None,
    ) -> A2AConsensusProposal:
        if proposal_id not in self._proposals:
            raise KeyError(f"Proposal {proposal_id} does not exist.")
        
        proposal = self._proposals[proposal_id]
        weight = self.weights.get(voter_agent, 1.0)
        
        proposal.votes[voter_agent] = A2AConsensusVote(
            voter_agent=voter_agent,
            vote=vote.lower(),
            weight=weight,
            rationale=rationale,
        )
        return self.evaluate_proposal(proposal_id)

    def evaluate_proposal(self, proposal_id: str) -> A2AConsensusProposal:
        proposal = self._proposals[proposal_id]
        if not proposal.participants:
            proposal.status = ProposalStatus.ACCEPTED
            return proposal

        total_participants = len(proposal.participants)
        submitted_votes = len(proposal.votes)

        if proposal.mechanism == ConsensusMechanism.UNANIMOUS:
            if any(v.vote == "reject" for v in proposal.votes.values()):
                proposal.status = ProposalStatus.REJECTED
            elif submitted_votes == total_participants and all(v.vote == "approve" for v in proposal.votes.values()):
                proposal.status = ProposalStatus.ACCEPTED
            else:
                proposal.status = ProposalStatus.PENDING

        elif proposal.mechanism == ConsensusMechanism.MAJORITY_VOTE:
            approvals = sum(1 for v in proposal.votes.values() if v.vote == "approve")
            rejections = sum(1 for v in proposal.votes.values() if v.vote == "reject")
            
            if approvals / total_participants > proposal.threshold:
                proposal.status = ProposalStatus.ACCEPTED
            elif rejections / total_participants >= (1.0 - proposal.threshold):
                proposal.status = ProposalStatus.REJECTED
            else:
                proposal.status = ProposalStatus.PENDING

        elif proposal.mechanism == ConsensusMechanism.WEIGHTED:
            total_possible_weight = sum(self.weights.get(p, 1.0) for p in proposal.participants)
            approved_weight = sum(v.weight for v in proposal.votes.values() if v.vote == "approve")
            rejected_weight = sum(v.weight for v in proposal.votes.values() if v.vote == "reject")

            if total_possible_weight > 0:
                if approved_weight / total_possible_weight > proposal.threshold:
                    proposal.status = ProposalStatus.ACCEPTED
                elif rejected_weight / total_possible_weight >= (1.0 - proposal.threshold):
                    proposal.status = ProposalStatus.REJECTED
                else:
                    proposal.status = ProposalStatus.PENDING

        return proposal


class DistributedLockManager:
    """Distributed Concurrency Lock Manager (RedLock emulation + Heartbeat Renewal)."""

    def __init__(self):
        self._locks: Dict[str, Dict[str, Any]] = {}

    def acquire_lock(self, resource_id: str, owner_agent: str, ttl_seconds: float = 10.0) -> bool:
        now = time.time()
        if resource_id in self._locks:
            lock = self._locks[resource_id]
            if lock["expires_at"] > now and lock["owner"] != owner_agent:
                return False  # Locked by another agent
        
        self._locks[resource_id] = {
            "owner": owner_agent,
            "acquired_at": now,
            "expires_at": now + ttl_seconds,
            "ttl_seconds": ttl_seconds,
        }
        return True

    def renew_heartbeat(self, resource_id: str, owner_agent: str) -> bool:
        now = time.time()
        if resource_id not in self._locks:
            return False
        lock = self._locks[resource_id]
        if lock["owner"] != owner_agent:
            return False
        
        lock["expires_at"] = now + lock["ttl_seconds"]
        return True

    def release_lock(self, resource_id: str, owner_agent: str) -> bool:
        if resource_id not in self._locks:
            return False
        if self._locks[resource_id]["owner"] != owner_agent:
            return False
        del self._locks[resource_id]
        return True

    def is_locked(self, resource_id: str) -> bool:
        now = time.time()
        if resource_id in self._locks:
            if self._locks[resource_id]["expires_at"] > now:
                return True
            del self._locks[resource_id]
        return False

    def list_active_locks(self) -> List[Dict[str, Any]]:
        now = time.time()
        active: List[Dict[str, Any]] = []
        expired_keys: List[str] = []
        for res_id, lock_data in self._locks.items():
            remaining = lock_data["expires_at"] - now
            if remaining > 0:
                active.append(
                    {
                        "resource": res_id,
                        "owner": lock_data["owner"],
                        "remaining_ttl_seconds": round(remaining, 2),
                        "acquired_at": lock_data["acquired_at"],
                    }
                )
            else:
                expired_keys.append(res_id)
        for k in expired_keys:
            del self._locks[k]
        return active
