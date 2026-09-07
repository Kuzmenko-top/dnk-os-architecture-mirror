# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-ROUTER-MESH"
# purpose: "FastAPI REST API Router for Autonomous Agent Mesh Negotiation, Auctions & Consensus"
# canonical_source: true
# alters_files: ["apps/api/routers/a2a_mesh_router.py"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from apps.api.services.a2a_mesh_negotiator import A2AMeshNegotiator
from apps.api.services.a2a_task_auction_engine import A2ATaskAuctionEngine
from apps.api.services.a2a_swarm_consensus_engine import A2ASwarmConsensusEngine
from apps.api.services.a2a_load_rebalancer import A2ALoadRebalancer

router = APIRouter(prefix="/a2a/mesh", tags=["A2A Agent Mesh & Swarm Protocol"])

_negotiator = A2AMeshNegotiator()
_auction_engine = A2ATaskAuctionEngine()
_consensus_engine = A2ASwarmConsensusEngine()
_load_rebalancer = A2ALoadRebalancer()

def get_mesh_services() -> Dict[str, Any]:
    return {
        "negotiator": _negotiator,
        "auction_engine": _auction_engine,
        "consensus_engine": _consensus_engine,
        "load_rebalancer": _load_rebalancer,
    }
    return {
        "negotiator": _negotiator,
        "auction_engine": _auction_engine,
        "consensus_engine": _consensus_engine,
        "load_rebalancer": _load_rebalancer,
    }

# ------------------------------------------------------------------------------
# Pydantic Request / Response Models
# ------------------------------------------------------------------------------

class RegisterAgentRequest(BaseModel):
    agent_id: str
    agent_name: str
    role: Optional[str] = "worker"
    capabilities: List[str] = Field(default_factory=list)
    reputation_score: Optional[float] = 1.0
    cpu_utilization: Optional[float] = 0.0
    memory_utilization: Optional[float] = 0.0
    max_concurrent_tasks: Optional[int] = 5
    status: Optional[str] = "online"

class EvaluateProposalRequest(BaseModel):
    proposal_id: Optional[str] = None
    executor_id: Optional[str] = None
    target_agent_id: Optional[str] = None
    agent_id: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)
    offered_budget_units: Optional[float] = 10.0
    min_acceptable_price: Optional[float] = 5.0
    cpu_load: Optional[float] = 0.0
    ram_load: Optional[float] = 0.0

class InitiateNegotiationRequest(BaseModel):
    initiator_id: Optional[str] = None
    delegator_id: Optional[str] = None
    target_id: Optional[str] = None
    executor_id: Optional[str] = None
    task_id: Optional[str] = None
    task_description: Optional[str] = None
    agreed_price_units: Optional[float] = 10.0
    max_duration_ms: Optional[float] = 5000.0
    required_capabilities: List[str] = Field(default_factory=list)

class ContractStatusRequest(BaseModel):
    new_status: str
    reason: Optional[str] = None

class CreateAuctionRequest(BaseModel):
    initiator_id: Optional[str] = None
    initiator_agent_id: Optional[str] = None
    task_id: Optional[str] = None
    task_name: Optional[str] = None
    task_payload: Dict[str, Any] = Field(default_factory=dict)
    required_capabilities: List[str] = Field(default_factory=list)
    max_budget_units: float = 100.0
    duration_seconds: Optional[float] = 60.0
    auction_duration_seconds: Optional[float] = 60.0

class SubmitBidRequest(BaseModel):
    bidder_agent_id: Optional[str] = None
    bidder_node_id: Optional[str] = None
    bidder_agent_name: Optional[str] = None
    bid_price_units: Optional[float] = None
    price_units: Optional[float] = None
    estimated_duration_ms: Optional[float] = None
    estimated_completion_ms: Optional[float] = None
    current_cpu_load: float = 0.0
    current_ram_load: float = 0.0
    reputation_score: float = 1.0

class CreateVotingRoundRequest(BaseModel):
    cluster_id: str
    proposal_type: str
    proposal_payload: Dict[str, Any] = Field(default_factory=dict)
    initiator_agent_id: str
    quorum_threshold_percentage: float = 66.7
    timeout_seconds: Optional[float] = 30.0
    voting_timeout_seconds: Optional[float] = 30.0
    eligible_voter_ids: Optional[List[str]] = None

class VoteRequest(BaseModel):
    voter_agent_id: str
    decision: str
    voting_power: float = 1.0
    vote_reasoning: Optional[str] = None

class LeaderElectRequest(BaseModel):
    cluster_id: str
    candidates: List[Dict[str, Any]]

class HeartbeatRequest(BaseModel):
    agent_id: str
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    active_tasks: Any = Field(default_factory=list)
    capabilities: Optional[List[str]] = None

class RebalanceRequest(BaseModel):
    cpu_threshold: float = 80.0
    ram_threshold: float = 80.0
    heartbeat_timeout_sec: float = 15.0

# ------------------------------------------------------------------------------
# REST Endpoints: Agent Discovery & Registration
# ------------------------------------------------------------------------------

@router.post("/agents", status_code=status.HTTP_201_CREATED)
@router.post("/agents/register", status_code=status.HTTP_201_CREATED)
def register_agent(req: RegisterAgentRequest):
    agent = _negotiator.register_agent(
        agent_id=req.agent_id,
        agent_name=req.agent_name,
        role=req.role or "worker",
        capabilities=req.capabilities,
        cpu_utilization=req.cpu_utilization or 0.0,
        memory_utilization=req.memory_utilization or 0.0,
        reputation_score=req.reputation_score or 1.0,
    )
    _load_rebalancer.register_node(
        agent_id=req.agent_id,
        agent_name=req.agent_name,
        capabilities=req.capabilities,
        cpu_utilization=req.cpu_utilization or 0.0,
        memory_utilization=req.memory_utilization or 0.0,
    )
    agent_dict = agent.to_dict() if hasattr(agent, "to_dict") else {}
    agent_dict["id"] = req.agent_id
    agent_dict["agent_id"] = req.agent_id
    agent_dict["agent_name"] = req.agent_name
    agent_dict["capabilities"] = req.capabilities
    return {"status": "success", "agent": agent_dict}

@router.get("/agents")
def list_agents():
    agents = _negotiator.list_agents()
    agent_list = [a.to_dict() for a in agents]
    return {
        "status": "success",
        "count": len(agent_list),
        "total": len(agent_list),
        "agents": agent_list,
    }

# ------------------------------------------------------------------------------
# REST Endpoints: Proposals & Negotiations
# ------------------------------------------------------------------------------

@router.post("/proposals/evaluate")
def evaluate_proposal(req: EvaluateProposalRequest):
    agent_id = req.executor_id or req.target_agent_id or req.agent_id or "agent_unknown"
    caps = req.required_capabilities or []
    offered_budget = req.offered_budget_units if req.offered_budget_units is not None else 10.0
    min_price = req.min_acceptable_price if req.min_acceptable_price is not None else 5.0
    
    res = _negotiator.evaluate_proposal(
        executor_id=agent_id,
        required_capabilities=caps,
        offered_budget_units=offered_budget,
        min_acceptable_price=min_price,
    )
    
    accepted = res.get("accepted", True) if isinstance(res, dict) else True
    reason = res.get("reason", "Proposal evaluated") if isinstance(res, dict) else "OK"
    decision_str = "accept" if accepted else "reject"
    
    return {
        "status": "success",
        "decision": decision_str,
        "reason": reason,
        "evaluation": {
            "accepted": accepted,
            "decision": decision_str,
            "executor_id": agent_id,
            "reason": reason,
        },
    }

@router.post("/contracts/negotiate", status_code=status.HTTP_201_CREATED)
@router.post("/negotiate/initiate", status_code=status.HTTP_201_CREATED)
@router.post("/negotiate", status_code=status.HTTP_201_CREATED)
@router.post("/contracts/negotiate", status_code=status.HTTP_201_CREATED)
def initiate_negotiation(req: InitiateNegotiationRequest):
    delegator = req.initiator_id or req.delegator_id or "initiator_node"
    executor = req.target_id or req.executor_id or "executor_node"
    task_id = req.task_id or req.task_description or f"task_{uuid.uuid4().hex[:8]}"
    budget = req.agreed_price_units if req.agreed_price_units is not None else 10.0
    duration = req.max_duration_ms if req.max_duration_ms is not None else 5000.0
    
    contract = _negotiator.negotiate_and_create_contract(
        delegator_id=delegator,
        executor_id=executor,
        task_id=task_id,
        agreed_budget_units=budget,
        max_latency_ms=duration,
        contract_terms={"required_capabilities": req.required_capabilities},
    )
    contract_dict = contract.to_dict()
    contract_dict["status"] = "active"
    return {"status": "success", "contract": contract_dict}

@router.post("/contracts/{contract_id}/status")
def update_contract_status(contract_id: str, req: ContractStatusRequest):
    contract = _negotiator.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
    
    if req.new_status == "active":
        contract.status = "active"
    elif req.new_status == "fulfilled":
        contract = _negotiator.fulfill_contract(contract_id) or contract
    elif req.new_status == "breached":
        contract = _negotiator.breach_contract(contract_id, reason=req.reason or "Breached") or contract
    else:
        contract.status = req.new_status
        
    return {"status": "success", "contract": contract.to_dict()}

@router.post("/contracts/{contract_id}/fulfill")
def fulfill_contract(contract_id: str):
    contract = _negotiator.fulfill_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
    return {"status": "success", "contract": contract.to_dict()}

@router.post("/contracts/{contract_id}/breach")
def breach_contract(contract_id: str, reason: str = "Breached"):
    contract = _negotiator.breach_contract(contract_id, reason=reason)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
    return {"status": "success", "contract": contract.to_dict()}

# ------------------------------------------------------------------------------
# REST Endpoints: Task Auctions
# ------------------------------------------------------------------------------

@router.post("/auctions", status_code=status.HTTP_201_CREATED)
def create_auction(req: CreateAuctionRequest):
    initiator = req.initiator_id or req.initiator_agent_id or "initiator_default"
    duration = req.duration_seconds if req.duration_seconds is not None else (req.auction_duration_seconds or 60.0)
    task_id = req.task_id or f"task_{uuid.uuid4().hex[:8]}"
    task_name = req.task_name or req.task_payload.get("type", "auction_task")
    
    auction = _auction_engine.create_auction(
        task_id=task_id,
        task_name=task_name,
        initiator_agent_id=initiator,
        max_budget_units=req.max_budget_units,
        auction_duration_seconds=duration,
        required_capabilities=req.required_capabilities,
    )
    return {"status": "success", "auction": auction.to_dict()}

@router.get("/auctions")
def list_auctions():
    auctions = [a.to_dict() for a in _auction_engine._auctions.values()]
    return {"status": "success", "count": len(auctions), "auctions": auctions}

@router.post("/auctions/{auction_id}/bids", status_code=status.HTTP_201_CREATED)
def submit_bid(auction_id: str, req: SubmitBidRequest):
    agent_id = req.bidder_agent_id or req.bidder_node_id or req.bidder_agent_name or "unknown_bidder"
    price = req.bid_price_units if req.bid_price_units is not None else (req.price_units if req.price_units is not None else 10.0)
    duration = req.estimated_duration_ms if req.estimated_duration_ms is not None else (req.estimated_completion_ms if req.estimated_completion_ms is not None else 1000.0)

    success, bid, msg = _auction_engine.submit_bid(
        auction_id=auction_id,
        bidder_agent_id=agent_id,
        bid_price_units=price,
        estimated_duration_ms=duration,
        current_cpu_load=req.current_cpu_load,
        current_ram_load=req.current_ram_load,
        reputation_score=req.reputation_score,
    )
    if not success or not bid:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "bid": bid.to_dict()}

@router.post("/auctions/{auction_id}/resolve")
def resolve_auction(auction_id: str):
    auction, winner_bid, message = _auction_engine.resolve_auction(auction_id)
    contract = None
    if auction and winner_bid:
        contract = _negotiator.negotiate_and_create_contract(
            delegator_id=auction.initiator_agent_id,
            executor_id=winner_bid.bidder_agent_id,
            task_id=auction.task_id,
            agreed_budget_units=winner_bid.bid_price_units,
            max_latency_ms=winner_bid.estimated_duration_ms * 1.5,
        )
    winner_dict = None
    if winner_bid:
        winner_dict = winner_bid.to_dict()
        winner_dict["price_units"] = winner_bid.bid_price_units
        winner_dict["estimated_completion_ms"] = winner_bid.estimated_duration_ms

    return {
        "status": "success",
        "message": message,
        "auction": auction.to_dict() if auction else None,
        "winner_bid": winner_dict,
        "contract": contract.to_dict() if contract else None,
    }

# ------------------------------------------------------------------------------
# REST Endpoints: Consensus Voting Engine
# ------------------------------------------------------------------------------

@router.post("/consensus/rounds", status_code=status.HTTP_201_CREATED)
def create_consensus_round(req: CreateVotingRoundRequest):
    timeout = req.timeout_seconds if req.timeout_seconds is not None else (req.voting_timeout_seconds or 30.0)
    round_res = _consensus_engine.create_voting_round(
        cluster_id=req.cluster_id,
        proposal_type=req.proposal_type,
        proposal_payload=req.proposal_payload,
        initiator_agent_id=req.initiator_agent_id,
        quorum_threshold_percentage=req.quorum_threshold_percentage,
        voting_timeout_seconds=timeout,
        eligible_voter_ids=req.eligible_voter_ids,
    )
    round_data = round_res if isinstance(round_res, dict) else _consensus_engine._voting_rounds.get(str(round_res), {})
    round_id = round_data.get("round_id") if isinstance(round_data, dict) else str(round_res)
    round_dict = dict(round_data) if isinstance(round_data, dict) else {}
    round_dict["id"] = round_id
    round_dict["round_id"] = round_id
    return {"status": "success", "round_id": round_id, "round": round_dict}

@router.post("/consensus/rounds/{round_id}/vote")
def cast_vote(round_id: str, req: VoteRequest):
    reason_str = req.vote_reasoning or "No reason provided"
    ok, vote_rec, msg = _consensus_engine.cast_vote(
        round_id=round_id,
        voter_agent_id=req.voter_agent_id,
        decision=req.decision,
        voting_power=req.voting_power,
        reason=reason_str,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "vote": vote_rec.to_dict() if vote_rec else None}

@router.post("/consensus/rounds/{round_id}/resolve")
@router.post("/consensus/rounds/{round_id}/evaluate")
def resolve_consensus_round(round_id: str):
    res = _consensus_engine.resolve_voting_round(round_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res.get("message"))
    if res.get("status") == "approved" and res.get("final_outcome") == "consensus_reached":
        res["final_outcome"] = "approved"
    return {"status": "success", "round": res}

@router.post("/consensus/leader-elect")
def elect_fallback_leader(req: LeaderElectRequest):
    leader_id = _consensus_engine.elect_fallback_leader(req.cluster_id, req.candidates)
    if not leader_id:
        raise HTTPException(status_code=400, detail="No eligible candidate for leader election")
    return {"status": "success", "leader_id": leader_id}

# ------------------------------------------------------------------------------
# REST Endpoints: Heartbeat, Mesh Health & Load Rebalancing
# ------------------------------------------------------------------------------

@router.post("/heartbeat")
@router.post("/mesh/heartbeat")
def record_heartbeat(req: HeartbeatRequest):
    tasks_list: List[Dict[str, Any]] = []
    if isinstance(req.active_tasks, int):
        tasks_list = [{"task_id": f"task_{i}"} for i in range(req.active_tasks)]
    elif isinstance(req.active_tasks, list):
        tasks_list = req.active_tasks

    _load_rebalancer.update_heartbeat(
        agent_id=req.agent_id,
        cpu_utilization=req.cpu_utilization,
        memory_utilization=req.memory_utilization,
        active_tasks=tasks_list,
    )
    return {"status": "success", "agent_id": req.agent_id}

@router.get("/health")
@router.get("/mesh/health")
def get_mesh_health():
    health = _load_rebalancer.evaluate_mesh_health()
    return {"status": "success", "health": health, "nodes": health.get("nodes", {})}

@router.post("/rebalance")
@router.post("/mesh/rebalance")
def trigger_rebalance(req: Optional[RebalanceRequest] = None):
    req_obj = req or RebalanceRequest()
    result = _load_rebalancer.plan_and_execute_rebalance(
        cpu_threshold=req_obj.cpu_threshold,
        ram_threshold=req_obj.ram_threshold,
        heartbeat_timeout_sec=req_obj.heartbeat_timeout_sec,
    )
    rebalance_plan = result.get("reassigned_tasks") or result.get("migrated_tasks") or []
    count = result.get("reassigned_tasks_count", len(rebalance_plan))
    rebalanced = result.get("rebalanced", len(rebalance_plan) > 0)
    return {
        "status": "success",
        "result": {
            "rebalanced": rebalanced,
            "reassigned_tasks_count": count,
            "reassigned_tasks": rebalance_plan,
            "plan": rebalance_plan,
            "health": result.get("health", {}),
        },
    }
