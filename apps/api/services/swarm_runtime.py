# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-002"
# purpose: "Swarm Runtime Orchestrator integrating 14 Swarm Agents with Multi-Agent A2A Protocol Engine"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

from dataclasses import dataclass, field
from typing import Any, Optional

from .a2a_protocol_engine import (
    A2AConsensusProposal,
    A2ADeadLetter,
    A2AMessage,
    A2ATelemetryRecord,
    CommunicationPattern,
    ConsensusEngine,
    ConsensusMechanism,
    DistributedLockManager,
    MessageRouter,
)


@dataclass
class SwarmAgentMetadata:
    name: str
    role: str
    capabilities: list[str] = field(default_factory=list)
    consensus_weight: float = 1.0
    status: str = "active"


# Canonical 14 Swarm Agents of DNK OS
CANONICAL_SWARM_AGENTS: dict[str, SwarmAgentMetadata] = {
    "gerych_builder": SwarmAgentMetadata(
        name="gerych_builder",
        role="UI/Code Builder",
        capabilities=["code_generation", "ui_components", "refactoring"],
        consensus_weight=2.0,
    ),
    "gerych_researcher": SwarmAgentMetadata(
        name="gerych_researcher",
        role="Deep R&D / GitHub Research",
        capabilities=["repository_mining", "ast_extraction", "licensing"],
        consensus_weight=1.5,
    ),
    "gerych_auditor": SwarmAgentMetadata(
        name="gerych_auditor",
        role="Security / Quality Auditor",
        capabilities=["red_teaming", "ast_security_scan", "test_verification"],
        consensus_weight=5.0,  # High veto weight for security
    ),
    "dnk_dev_fullstack": SwarmAgentMetadata(
        name="dnk_dev_fullstack",
        role="Backend & Fullstack Engine",
        capabilities=["fastapi", "database", "distributed_systems"],
        consensus_weight=2.0,
    ),
    "dnk_shopify": SwarmAgentMetadata(
        name="dnk_shopify",
        role="E-commerce & Payments",
        capabilities=["liquid", "shopify_api", "checkout_3ds"],
        consensus_weight=1.5,
    ),
    "dnk_video_ai_creator": SwarmAgentMetadata(
        name="dnk_video_ai_creator",
        role="Media & Programmatic Video",
        capabilities=["ffmpeg", "video_generation", "remotion"],
        consensus_weight=1.0,
    ),
    "dnk_security_guard": SwarmAgentMetadata(
        name="dnk_security_guard",
        role="Firewall & Boundary Defense",
        capabilities=["firewall", "rate_limiting", "token_sanitization"],
        consensus_weight=5.0,  # High veto weight
    ),
    "dnk_scones_memory": SwarmAgentMetadata(
        name="dnk_scones_memory",
        role="Persistent Knowledge & Memory",
        capabilities=["vector_retrieval", "scones_db", "pattern_retrieval"],
        consensus_weight=1.5,
    ),
    "antigravity_supervisor": SwarmAgentMetadata(
        name="antigravity_supervisor",
        role="Head of Orchestration & Architecture",
        capabilities=["task_decomposition", "swarm_orchestration", "governance"],
        consensus_weight=3.0,
    ),
    "dnk_marketing_agent": SwarmAgentMetadata(
        name="dnk_marketing_agent",
        role="Growth & Marketing Analytics",
        capabilities=["campaigns", "copywriting", "seo"],
        consensus_weight=1.0,
    ),
    "dnk_customer_support": SwarmAgentMetadata(
        name="dnk_customer_support",
        role="Support & Ticket Routing",
        capabilities=["triage", "faq_answering", "sla_tracking"],
        consensus_weight=1.0,
    ),
    "dnk_analytics_agent": SwarmAgentMetadata(
        name="dnk_analytics_agent",
        role="Data Analytics & BI",
        capabilities=["telemetry_aggregation", "reporting", "bi_dashboards"],
        consensus_weight=1.0,
    ),
    "dnk_ops_agent": SwarmAgentMetadata(
        name="dnk_ops_agent",
        role="Infrastructure & Deployment",
        capabilities=["docker", "ci_cd", "observability"],
        consensus_weight=2.0,
    ),
    "dnk_qa_agent": SwarmAgentMetadata(
        name="dnk_qa_agent",
        role="Automated QA & E2E Validation",
        capabilities=["e2e_testing", "playwright", "load_testing"],
        consensus_weight=2.0,
    ),
}


class SwarmRuntime:
    """Production-grade Swarm Runtime managing 14 Swarm Agents over A2A Protocol Engine."""

    def __init__(self, agent_overrides: Optional[dict[str, SwarmAgentMetadata]] = None) -> None:
        self.agents: dict[str, SwarmAgentMetadata] = agent_overrides or CANONICAL_SWARM_AGENTS.copy()
        agent_names = list(self.agents.keys())

        # Initialize core A2A components
        self.message_router = MessageRouter(known_agents=agent_names)
        weights = {name: meta.consensus_weight for name, meta in self.agents.items()}
        self.consensus_engine = ConsensusEngine(default_weights=weights)
        self.lock_manager = DistributedLockManager()

        # Auto-subscribe default swarm channels
        for agent_name in agent_names:
            self.message_router.subscribe_topic("system.alerts", agent_name)

    async def send_message(
        self,
        sender: str,
        recipients: list[str],
        method: str,
        params: Optional[dict[str, Any]] = None,
        pattern: CommunicationPattern = CommunicationPattern.P2P,
        topic: Optional[str] = None,
        timeout_ms: int = 5000,
    ) -> A2AMessage:
        """Constructs, validates, and routes an A2AMessage."""
        message = A2AMessage(
            method=method,
            params=params or {},
            sender=sender,
            recipients=recipients,
            pattern=pattern,
            topic=topic,
            timeout_ms=timeout_ms,
        )
        await self.message_router.route(message)
        return message

    async def broadcast_alert(
        self,
        sender: str,
        alert: dict[str, Any],
        severity: str = "HIGH",
    ) -> A2AMessage:
        """Broadcasts an alert to all registered agents in the Swarm."""
        params = {"alert": alert, "severity": severity}
        return await self.send_message(
            sender=sender,
            recipients=[],
            method="system.broadcast_alert",
            params=params,
            pattern=CommunicationPattern.BROADCAST,
        )

    async def delegate_task(
        self,
        supervisor: str,
        workers: list[str],
        task_payload: dict[str, Any],
    ) -> A2AMessage:
        """Supervisor-to-Worker task delegation."""
        return await self.send_message(
            sender=supervisor,
            recipients=workers,
            method="supervisor.delegate_task",
            params=task_payload,
            pattern=CommunicationPattern.SUPERVISOR_WORKER,
        )

    async def publish_event(
        self,
        sender: str,
        topic: str,
        payload: dict[str, Any],
    ) -> A2AMessage:
        """Publish a topic-based event for subscribed agents."""
        return await self.send_message(
            sender=sender,
            recipients=[],
            method=f"event.{topic}",
            params=payload,
            pattern=CommunicationPattern.PUBSUB,
            topic=topic,
        )

    async def receive_next(self, agent_name: str, timeout_s: float = 1.0) -> Optional[A2AMessage]:
        """Pulls the next message from an agent's inbox."""
        return await self.message_router.receive(agent_name, timeout_s=timeout_s)

    def request_consensus(
        self,
        proposer: str,
        topic: str,
        description: str,
        mechanism: ConsensusMechanism = ConsensusMechanism.MAJORITY_VOTE,
        threshold: float = 0.5,
        participants: Optional[list[str]] = None,
    ) -> A2AConsensusProposal:
        """Initiates a swarm consensus proposal."""
        part = participants or list(self.agents.keys())
        return self.consensus_engine.create_proposal(
            topic=topic,
            description=description,
            participants=part,
            mechanism=mechanism,
            threshold=threshold,
        )

    def vote_consensus(
        self,
        proposal_id: str,
        voter: str,
        vote: str,
        rationale: str = "",
    ) -> A2AConsensusProposal:
        """Records a vote for a consensus proposal."""
        return self.consensus_engine.cast_vote(
            proposal_id=proposal_id,
            voter_agent=voter,
            vote=vote,
            rationale=rationale,
        )

    def acquire_resource_lock(
        self,
        resource: str,
        agent: str,
        ttl_seconds: float = 30.0,
    ) -> bool:
        """Acquires a distributed lock on a resource."""
        return self.lock_manager.acquire_lock(
            resource_id=resource,
            owner_agent=agent,
            ttl_seconds=ttl_seconds,
        )

    def renew_resource_lock(self, resource: str, agent: str) -> bool:
        """Renews lock heartbeat for an agent."""
        return self.lock_manager.renew_heartbeat(resource_id=resource, owner_agent=agent)

    def release_resource_lock(self, resource: str, agent: str) -> bool:
        """Releases a distributed lock."""
        return self.lock_manager.release_lock(resource_id=resource, owner_agent=agent)

    def get_active_locks(self) -> list[dict[str, Any]]:
        """Returns metadata for all active distributed locks."""
        return self.lock_manager.list_active_locks()

    def get_telemetry(self, trace_id: Optional[str] = None) -> list[A2ATelemetryRecord]:
        """Returns message delivery telemetry records."""
        return self.message_router.get_telemetry(trace_id=trace_id)

    def get_dlq(self) -> list[A2ADeadLetter]:
        """Returns poisoned / dead-letter queue records."""
        return self.message_router.get_dlq()

    def list_agents(self) -> list[dict[str, Any]]:
        """Returns a list of all registered 14 Swarm agents and their metadata."""
        return [
            {
                "name": meta.name,
                "role": meta.role,
                "capabilities": meta.capabilities,
                "consensus_weight": meta.consensus_weight,
                "status": meta.status,
            }
            for meta in self.agents.values()
        ]
