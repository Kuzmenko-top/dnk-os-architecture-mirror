# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-SERVICE-AUCTION"
# purpose: "A2A Task Auction Engine with Multi-Attribute Composite Bid Scoring"
# canonical_source: true
# alters_files: ["apps/api/services/a2a_task_auction_engine.py"]
# triggers_tasks: ["DNK-A2A-003-MVP"]
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from apps.api.db.models.a2a_task_auction import A2ATaskAuction
from apps.api.db.models.a2a_resource_bid import A2AResourceBid
from apps.api.db.models.a2a_negotiation_contract import A2ANegotiationContract
from apps.api.services.a2a_mesh_negotiator import A2AMeshNegotiator


class BidSubmissionResult(tuple):
    """Custom tuple supporting both boolean checks and (success, bid, message) tuple unpacking."""
    def __new__(cls, success: bool, bid: Optional[A2AResourceBid], message: str):
        return super(BidSubmissionResult, cls).__new__(cls, (success, bid, message))

    def __bool__(self) -> bool:
        return bool(self[0])


class A2ATaskAuctionEngine:
    """Decentralized task auctioneer calculating multi-attribute utility scores for resource allocation."""

    # Configurable scoring weights: price (30%), latency (25%), load availability (25%), reputation (20%)
    W_PRICE = 0.30
    W_LATENCY = 0.25
    W_LOAD = 0.25
    W_REPUTATION = 0.20

    def __init__(self, negotiator: Optional[A2AMeshNegotiator] = None):
        self._auctions: Dict[str, A2ATaskAuction] = {}
        self._bids: Dict[str, List[A2AResourceBid]] = {}
        self._negotiator = negotiator or A2AMeshNegotiator()

    def create_auction(
        self,
        task_or_id: Optional[Union[A2ATaskAuction, str, uuid.UUID]] = None,
        task_id: Optional[str] = None,
        task_name: Optional[str] = None,
        initiator_agent_id: Optional[str] = None,
        required_capabilities: Optional[List[str]] = None,
        max_budget_units: float = 100.0,
        auction_duration_seconds: float = 5.0,
        task_payload: Optional[Dict[str, Any]] = None,
        workspace_id: str = "ws-default",
    ) -> A2ATaskAuction:
        """Create and register a new task auction."""
        target_task = task_or_id if task_or_id is not None else task_id
        if target_task is None:
            target_task = f"task_{uuid.uuid4().hex[:8]}"

        if isinstance(target_task, A2ATaskAuction):
            auction = target_task
            auction_id = str(auction.id) if auction.id else f"auc_{uuid.uuid4().hex[:12]}"
            auction.id = auction_id
            self._auctions[auction_id] = auction
            if auction_id not in self._bids:
                self._bids[auction_id] = []
            return auction

        auction_id = f"auc_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=auction_duration_seconds)

        auction = A2ATaskAuction(
            id=auction_id,
            workspace_id=workspace_id,
            task_id=str(target_task),
            task_name=task_name or f"Task {target_task}",
            initiator_agent_id=str(initiator_agent_id or "supervisor_agent"),
            required_capabilities=required_capabilities or [],
            max_budget_units=max_budget_units,
            bids_count=0,
            status="open",
            task_payload=task_payload or {},
            expires_at=expires_at,
            created_at=now,
        )
        self._auctions[auction_id] = auction
        self._bids[auction_id] = []
        return auction

    def calculate_composite_score(
        self,
        bid_or_price: Optional[Union[A2AResourceBid, float]] = None,
        *,
        bid_price: Optional[float] = None,
        max_budget: Optional[float] = None,
        estimated_duration_ms: Optional[float] = None,
        current_load_percentage: Optional[float] = None,
        agent_reputation: float = 1.0,
        **kwargs: Any,
    ) -> float:
        """Calculates normalized composite utility score in range [0.0, 1.0]."""
        target = bid_or_price if bid_or_price is not None else (bid_price if bid_price is not None else kwargs.get("price"))
        if target is None:
            target = 1.0

        if isinstance(target, A2AResourceBid):
            bid = target
            price = bid.bid_price_units if bid.bid_price_units is not None else 1.0
            duration = bid.estimated_duration_ms if bid.estimated_duration_ms is not None else 100.0
            load = bid.current_load_percentage if bid.current_load_percentage is not None else 0.0
            budget = max_budget or 100.0
            reputation = (bid.bid_metadata or {}).get("reputation", agent_reputation)
        else:
            price = float(target)
            budget = float(max_budget) if max_budget is not None else 100.0
            duration = float(estimated_duration_ms) if estimated_duration_ms is not None else 100.0
            load = float(current_load_percentage) if current_load_percentage is not None else 0.0
            reputation = float(agent_reputation)

        # Price score: 1.0 if free, 0.0 if equals or exceeds budget
        price_norm = max(0.0, min(1.0, 1.0 - (price / max(budget, 1.0))))

        # Latency score: benchmarked against 2000ms baseline
        latency_norm = max(0.0, min(1.0, 1.0 - (duration / 2000.0)))

        # Load score: 1.0 if idle (0% load), 0.0 if 100% loaded
        load_norm = max(0.0, min(1.0, 1.0 - (load / 100.0)))

        # Reputation score: normalized against max 2.0
        reputation_norm = max(0.0, min(1.0, reputation / 2.0))

        composite = (
            self.W_PRICE * price_norm +
            self.W_LATENCY * latency_norm +
            self.W_LOAD * load_norm +
            self.W_REPUTATION * reputation_norm
        )
        return round(composite, 4)

    def submit_bid(
        self,
        auction_id: Union[str, uuid.UUID],
        bid_or_agent_id: Optional[Union[A2AResourceBid, str, uuid.UUID]] = None,
        *,
        bidder_agent_id: Optional[Union[str, uuid.UUID]] = None,
        bid_price_units: Optional[float] = None,
        estimated_duration_ms: Optional[float] = None,
        current_load_percentage: Optional[float] = None,
        agent_reputation: float = 1.0,
        bid_metadata: Optional[Dict[str, Any]] = None,
        workspace_id: str = "ws-default",
        **kwargs: Any,
    ) -> BidSubmissionResult:
        """Submit a bid to an open task auction."""
        auc_id = str(auction_id)
        auction = self._auctions.get(auc_id)
        if not auction:
            return BidSubmissionResult(False, None, f"Auction {auc_id} not found")

        if auction.status != "open":
            return BidSubmissionResult(False, None, f"Auction {auc_id} is {auction.status}, not accepting bids")

        bid_source = bid_or_agent_id if bid_or_agent_id is not None else bidder_agent_id
        if bid_source is None:
            return BidSubmissionResult(False, None, "Bidder agent ID or bid object required")

        if isinstance(bid_source, A2AResourceBid):
            bid = bid_source
            if (bid.bid_price_units or 0.0) > (auction.max_budget_units or 100.0):
                return BidSubmissionResult(False, None, f"Bid price {bid.bid_price_units} exceeds max budget {auction.max_budget_units}")

            if bid.composite_score is None or bid.composite_score == 0.0:
                bid.composite_score = self.calculate_composite_score(
                    bid_or_price=bid.bid_price_units or 1.0,
                    max_budget=auction.max_budget_units or 100.0,
                    estimated_duration_ms=bid.estimated_duration_ms or 100.0,
                    current_load_percentage=bid.current_load_percentage or 0.0,
                    agent_reputation=agent_reputation,
                )
            if auc_id not in self._bids:
                self._bids[auc_id] = []
            self._bids[auc_id].append(bid)
            auction.bids_count = len(self._bids[auc_id])
            return BidSubmissionResult(True, bid, "Bid registered successfully")

        price = bid_price_units if bid_price_units is not None else 1.0
        if price > (auction.max_budget_units or 100.0):
            return BidSubmissionResult(False, None, f"Bid price {price} exceeds max budget {auction.max_budget_units}")

        duration = estimated_duration_ms if estimated_duration_ms is not None else 100.0
        load = current_load_percentage if current_load_percentage is not None else 0.0

        score = self.calculate_composite_score(
            bid_or_price=price,
            max_budget=auction.max_budget_units or 100.0,
            estimated_duration_ms=duration,
            current_load_percentage=load,
            agent_reputation=agent_reputation,
        )

        bid_id = f"bid_{uuid.uuid4().hex[:12]}"
        bid = A2AResourceBid(
            id=bid_id,
            workspace_id=workspace_id,
            auction_id=auc_id,
            bidder_agent_id=str(bid_source),
            bid_price_units=price,
            estimated_duration_ms=duration,
            current_load_percentage=load,
            composite_score=score,
            is_winning_bid=False,
            bid_metadata=bid_metadata or {},
        )
        if auc_id not in self._bids:
            self._bids[auc_id] = []
        self._bids[auc_id].append(bid)
        auction.bids_count = len(self._bids[auc_id])
        return BidSubmissionResult(True, bid, "Bid registered successfully")

    def rank_bids(self, auction_id: Union[str, uuid.UUID]) -> List[A2AResourceBid]:
        """Rank bids for a given auction by composite utility score descending, then lowest price."""
        bids = self._bids.get(str(auction_id), [])
        return sorted(
            bids,
            key=lambda b: (b.composite_score if b.composite_score is not None else 0.0, -(b.bid_price_units if b.bid_price_units is not None else 9999.0)),
            reverse=True,
        )

    def resolve_auction(
        self, auction_id: Union[str, uuid.UUID]
    ) -> Tuple[Optional[A2ATaskAuction], Optional[A2AResourceBid], str]:
        auc_id = str(auction_id)
        auction = self._auctions.get(auc_id)
        if not auction:
            return None, None, f"Auction {auc_id} not found"

        if auction.status not in ("open", "closed"):
            return auction, None, f"Auction is already {auction.status}"

        ranked = self.rank_bids(auc_id)
        if not ranked:
            auction.status = "expired"
            return auction, None, "No bids received; auction expired"

        winning_bid = ranked[0]
        winning_bid.is_winning_bid = True

        auction.status = "awarded"
        auction.winning_agent_id = winning_bid.bidder_agent_id
        auction.final_settled_price = winning_bid.bid_price_units
        auction.awarded_at = datetime.now(timezone.utc)

        return auction, winning_bid, f"Auction awarded to {winning_bid.bidder_agent_id}"

    def finalize_auction(
        self,
        auction_id: Union[str, uuid.UUID],
        negotiator: Optional[A2AMeshNegotiator] = None,
    ) -> Optional[A2ANegotiationContract]:
        """Finalize auction and construct an executed A2ANegotiationContract with the winning bidder."""
        auc_id = str(auction_id)
        auction, winning_bid, msg = self.resolve_auction(auc_id)
        if not auction or not winning_bid:
            return None

        neg = negotiator or self._negotiator
        contract = neg.negotiate_and_create_contract(
            delegator_id=auction.initiator_agent_id,
            executor_id=winning_bid.bidder_agent_id,
            task_id=auction.task_id,
            agreed_budget_units=winning_bid.bid_price_units or 0.0,
            max_latency_ms=winning_bid.estimated_duration_ms or 1000.0,
            retry_limit=3,
            contract_terms={
                "auction_id": auc_id,
                "composite_score": winning_bid.composite_score,
                "created_via": "auction_engine",
            },
            workspace_id=auction.workspace_id or "ws-default",
        )
        return contract

    def get_auction(self, auction_id: Union[str, uuid.UUID]) -> Optional[A2ATaskAuction]:
        return self._auctions.get(str(auction_id))

    def get_bids(self, auction_id: Union[str, uuid.UUID]) -> List[A2AResourceBid]:
        return self._bids.get(str(auction_id), [])

    def list_auctions(self, workspace_id: Optional[str] = None) -> List[A2ATaskAuction]:
        if workspace_id:
            return [a for a in self._auctions.values() if a.workspace_id == workspace_id]
        return list(self._auctions.values())
