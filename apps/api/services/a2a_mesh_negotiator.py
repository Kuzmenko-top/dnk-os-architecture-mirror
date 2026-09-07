# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-SERVICE-NEGOTIATOR"
# purpose: "A2A Peer-to-Peer Mesh Negotiation Engine & SLA Contract Management"
# canonical_source: true
# alters_files: ["apps/api/services/a2a_mesh_negotiator.py"]
# triggers_tasks: ["DNK-A2A-003-MVP"]
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from apps.api.db.models.a2a_mesh_agent import A2AMeshAgent
from apps.api.db.models.a2a_negotiation_contract import A2ANegotiationContract


@dataclass
class TaskSpec:
    """Specification of a task proposed for A2A negotiation."""
    task_id: str
    task_name: str = ""
    required_capabilities: List[str] = field(default_factory=list)
    budget_units: float = 100.0
    max_latency_ms: float = 1000.0
    retry_limit: int = 3
    workspace_id: str = "ws-default"
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NegotiationSession:
    """Represents an active bilateral negotiation session between two mesh agents."""
    session_id: str
    delegator_id: str
    executor_id: str
    task_spec: TaskSpec
    status: str = "initiated"  # initiated, proposed, counter_offered, accepted, rejected, contracted
    agreed_price: Optional[float] = None
    agreed_latency_ms: Optional[float] = None
    rejection_reason: Optional[str] = None
    counter_proposals: List[Dict[str, Any]] = field(default_factory=list)
    finalized_contract_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def counter_offer(self, price: float, latency_ms: float, terms: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Propose counter terms for the negotiation session."""
        proposal = {
            "proposal_id": f"prop_{uuid.uuid4().hex[:8]}",
            "price": price,
            "latency_ms": latency_ms,
            "terms": terms or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.counter_proposals.append(proposal)
        self.status = "counter_offered"
        return proposal

    def accept(self, price: Optional[float] = None, latency_ms: Optional[float] = None) -> bool:
        """Accept current or agreed negotiation terms."""
        self.agreed_price = price if price is not None else (self.counter_proposals[-1]["price"] if self.counter_proposals else self.task_spec.budget_units)
        self.agreed_latency_ms = latency_ms if latency_ms is not None else (self.counter_proposals[-1]["latency_ms"] if self.counter_proposals else self.task_spec.max_latency_ms)
        self.status = "accepted"
        return True

    def reject(self, reason: str = "Terms unacceptable") -> bool:
        """Reject negotiation terms."""
        self.status = "rejected"
        self.rejection_reason = reason
        return True


class A2AMeshNegotiator:
    """Orchestrates direct peer-to-peer capability negotiations and SLA contracts between agents."""

    def __init__(self):
        self._agents: Dict[str, A2AMeshAgent] = {}
        self._contracts: Dict[str, A2ANegotiationContract] = {}
        self._sessions: Dict[str, NegotiationSession] = {}

    def register_agent(
        self,
        agent_id: Union[str, uuid.UUID],
        agent_name: str,
        role: str = "worker",
        capabilities: Optional[List[str]] = None,
        cpu_utilization: float = 0.0,
        memory_utilization: float = 0.0,
        reputation_score: float = 1.0,
        workspace_id: str = "ws-default",
    ) -> A2AMeshAgent:
        str_id = str(agent_id)
        agent = A2AMeshAgent(
            id=str_id,
            workspace_id=workspace_id,
            agent_name=agent_name,
            role=role,
            capabilities=capabilities or [],
            status="online",
            cpu_utilization=cpu_utilization,
            memory_utilization=memory_utilization,
            active_tasks_count=0.0,
            reputation_score=reputation_score,
        )
        self._agents[str_id] = agent
        return agent

    def get_agent(self, agent_id: Union[str, uuid.UUID]) -> Optional[A2AMeshAgent]:
        return self._agents.get(str(agent_id))

    def list_agents(self, workspace_id: Optional[str] = None) -> List[A2AMeshAgent]:
        if workspace_id:
            return [a for a in self._agents.values() if a.workspace_id == workspace_id]
        return list(self._agents.values())

    def update_agent_load(
        self,
        agent_id: Union[str, uuid.UUID],
        cpu_utilization: float,
        memory_utilization: float,
    ) -> Optional[A2AMeshAgent]:
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        agent.cpu_utilization = cpu_utilization
        agent.memory_utilization = memory_utilization
        if cpu_utilization >= 80.0 or memory_utilization >= 80.0:
            agent.status = "busy"
        else:
            agent.status = "online"
        agent.updated_at = datetime.now(timezone.utc)
        return agent

    def initiate_negotiation(
        self,
        delegator_id: Union[str, uuid.UUID],
        executor_id: Union[str, uuid.UUID],
        task_spec: Union[TaskSpec, Dict[str, Any]],
    ) -> NegotiationSession:
        """Initiate a formal negotiation session between a delegator and an executor agent."""
        session_id = f"neg_{uuid.uuid4().hex[:12]}"
        if isinstance(task_spec, dict):
            spec = TaskSpec(
                task_id=task_spec.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                task_name=task_spec.get("task_name", "Negotiation Task"),
                required_capabilities=task_spec.get("required_capabilities", []),
                budget_units=task_spec.get("budget_units", 100.0),
                max_latency_ms=task_spec.get("max_latency_ms", 1000.0),
                retry_limit=task_spec.get("retry_limit", 3),
                workspace_id=task_spec.get("workspace_id", "ws-default"),
                payload=task_spec.get("payload", {}),
            )
        else:
            spec = task_spec

        session = NegotiationSession(
            session_id=session_id,
            delegator_id=str(delegator_id),
            executor_id=str(executor_id),
            task_spec=spec,
            status="initiated",
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[NegotiationSession]:
        return self._sessions.get(session_id)

    def evaluate_proposal(
        self,
        executor_id: Union[str, uuid.UUID],
        required_capabilities: List[str],
        offered_budget_units: float,
        min_acceptable_price: float = 5.0,
    ) -> Dict[str, Any]:
        executor = self.get_agent(executor_id)
        if not executor:
            return {"accepted": False, "reason": f"Agent {executor_id} not found"}

        if executor.status == "offline":
            return {"accepted": False, "reason": f"Agent {executor_id} is offline"}

        if (executor.cpu_utilization or 0.0) >= 85.0 or (executor.memory_utilization or 0.0) >= 85.0:
            return {
                "accepted": False,
                "reason": f"Agent {executor_id} overloaded (CPU: {executor.cpu_utilization}%, RAM: {executor.memory_utilization}%)",
            }

        missing_caps = [c for c in required_capabilities if c not in (executor.capabilities or [])]
        if missing_caps:
            return {"accepted": False, "reason": f"Missing required capabilities: {missing_caps}"}

        if offered_budget_units < min_acceptable_price:
            return {
                "accepted": False,
                "reason": f"Budget {offered_budget_units} is below minimum acceptable {min_acceptable_price}",
            }

        return {
            "accepted": True,
            "executor_id": str(executor_id),
            "estimated_cost": max(min_acceptable_price, offered_budget_units * 0.9),
            "reputation": executor.reputation_score,
        }

    def validate_sla(self, contract: A2ANegotiationContract) -> bool:
        """Validate an SLA contract against system invariants, capabilities, and capacity constraints."""
        if not contract:
            return False
        if not contract.delegator_agent_id or not contract.executor_agent_id or not contract.task_id:
            return False
        if (contract.agreed_budget_units or 0.0) < 0.0:
            return False
        if (contract.max_latency_ms or 0.0) <= 0.0:
            return False
        if (contract.retry_limit or 0) < 0:
            return False

        executor = self.get_agent(contract.executor_agent_id)
        if executor:
            if executor.status == "offline":
                return False
            if (executor.cpu_utilization or 0.0) >= 95.0 or (executor.memory_utilization or 0.0) >= 95.0:
                return False
        return True

    def register_contract(self, contract: A2ANegotiationContract) -> str:
        """Register and activate an SLA contract in the mesh ecosystem."""
        if not self.validate_sla(contract):
            raise ValueError("SLA contract failed validation constraints")

        contract_id = str(contract.id) if contract.id else f"sla_{uuid.uuid4().hex[:12]}"
        contract.id = contract_id
        if not contract.status:
            contract.status = "active"

        self._contracts[contract_id] = contract

        executor = self.get_agent(contract.executor_agent_id)
        if executor:
            executor.active_tasks_count = (executor.active_tasks_count or 0.0) + 1.0
        return contract_id

    def negotiate_and_create_contract(
        self,
        delegator_id: Union[str, uuid.UUID],
        executor_id: Union[str, uuid.UUID],
        task_id: str,
        agreed_budget_units: float,
        max_latency_ms: float = 1000.0,
        retry_limit: int = 3,
        contract_terms: Optional[Dict[str, Any]] = None,
        workspace_id: str = "ws-default",
    ) -> A2ANegotiationContract:
        contract_id = f"sla_{uuid.uuid4().hex[:12]}"
        contract = A2ANegotiationContract(
            id=contract_id,
            workspace_id=workspace_id,
            delegator_agent_id=str(delegator_id),
            executor_agent_id=str(executor_id),
            task_id=task_id,
            agreed_budget_units=agreed_budget_units,
            max_latency_ms=max_latency_ms,
            retry_limit=retry_limit,
            status="active",
            contract_terms=contract_terms or {},
        )
        self.register_contract(contract)
        return contract

    def fulfill_contract(self, contract_id: str) -> Optional[A2ANegotiationContract]:
        contract = self._contracts.get(contract_id)
        if not contract or contract.status != "active":
            return None

        contract.status = "fulfilled"
        contract.fulfilled_at = datetime.now(timezone.utc)

        executor = self.get_agent(contract.executor_agent_id)
        if executor:
            executor.active_tasks_count = max(0.0, (executor.active_tasks_count or 1.0) - 1.0)
            executor.reputation_score = min(2.0, (executor.reputation_score or 1.0) + 0.05)
        return contract

    def breach_contract(self, contract_id: str, reason: str = "timeout") -> Optional[A2ANegotiationContract]:
        contract = self._contracts.get(contract_id)
        if not contract or contract.status != "active":
            return None

        contract.status = "breached"
        terms = dict(contract.contract_terms or {})
        terms["breach_reason"] = reason
        contract.contract_terms = terms

        executor = self.get_agent(contract.executor_agent_id)
        if executor:
            executor.active_tasks_count = max(0.0, (executor.active_tasks_count or 1.0) - 1.0)
            executor.reputation_score = max(0.1, (executor.reputation_score or 1.0) - 0.2)
        return contract

    def get_contract(self, contract_id: str) -> Optional[A2ANegotiationContract]:
        return self._contracts.get(contract_id)

    def list_contracts(self, workspace_id: Optional[str] = None) -> List[A2ANegotiationContract]:
        if workspace_id:
            return [c for c in self._contracts.values() if c.workspace_id == workspace_id]
        return list(self._contracts.values())
