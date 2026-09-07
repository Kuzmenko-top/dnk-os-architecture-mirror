---
name: multi-agent-a2a-protocol
description: Use when building multi-agent A2A protocols and routing.
version: 1.0.0
author: DNK-e.com Maksym & Gerych Prime
license: MIT
metadata:
  hermes:
    tags: [multi-agent, a2a, protocols, consensus, distributed-locks, redis]
    related_skills: [hermes-agent, workspace-realtime-collaboration]
---

# Multi-Agent Agent-to-Agent (A2A) Protocol Architecture

This skill defines the canonical architecture and patterns for building and maintaining robust Agent-to-Agent (A2A) communication fabrics in multi-agent swarms.

## When to Use
- Implementing or extending inter-agent communication channels (P2P, Supervisor-Worker, Broadcast, PubSub).
- Designing consensus mechanisms for multi-agent approvals (e.g., Security/Auditor gates, deployment consensus).
- Managing shared state concurrency across autonomous workers with distributed locks and TTL heartbeats.
- Standardizing JSON-RPC 2.0 / A2A message serialization and tracing.

## 1. Core Communication Patterns

When designing multi-agent swarms, route all inter-agent traffic through standardized patterns:

1. **P2P (Peer-to-Peer)**:
   - Direct bilateral communication between two specialized agents (e.g. `gerych_auditor` ↔ `gerych_builder` for code reviews).
   - Expected response: direct synchronous or asynchronous acknowledgement.

2. **Supervisor-Worker**:
   - Hierarchical delegation from an orchestrator to one or many worker agents.
   - Message fans out with a correlated `trace_id` and tracks completion across worker mailboxes.

3. **Broadcast**:
   - Swarm-wide notification (e.g., Security Alerts, Global Circuit Breaker trips).
   - Delivered to all registered agents except the sender.

4. **PubSub (Topic-Based)**:
   - Decoupled topic channels (e.g. `deployments.production`, `metrics.telemetry`).
   - Agents dynamically subscribe and unsubscribe without point-to-point coupling.

---

## 2. Standard Message Envelope (JSON-RPC 2.0 / A2A-ML-001)

Always enforce strict Pydantic v2 schemas for wire messages:
- `jsonrpc`: `"2.0"`
- `method`: Namespaced action (`agent.review`, `supervisor.delegate`, `system.security_alert`).
- `id`, `trace_id`, `span_id`: Unique correlation identifiers for telemetry and debugging.
- `sender` & `recipients`: Explicit agent identifiers.
- `pattern`: One of `peer-to-peer`, `supervisor-worker`, `broadcast`, `pubsub`.
- `timestamp`: Timezone-aware UTC (`datetime.now(timezone.utc)`).

---

## 3. Consensus Engine Invariants

When swarms make distributed decisions, use deterministic consensus mechanisms:

- **Majority Vote**: Requires `> threshold` (e.g. `> 0.5` or `> 0.66`) approvals.
- **Unanimous**: 100% agreement required; any single rejection with rationale triggers immediate veto (ideal for Security/Auditor gates).
- **Weighted Consensus**: Votes scaled by agent domain expertise weights (e.g. Security Auditor weight `5.0` vs Worker weight `1.0`).

---

## 4. Distributed Concurrency & Locking

To prevent race conditions on shared state, resources, or files:
- Implement RedLock-style distributed locking with TTL.
- Enforce periodic heartbeat renewal (`renew_heartbeat`) during long-running tasks.
- Always implement Dead-Letter Queues (DLQ) for malformed, unroutable, or timed-out envelopes.

---

## 5. Swarm Runtime & Monitoring REST API

When exposing A2A Swarm runtime state for telemetry and Generative UI dashboards:
1. **Canonical Registry**: Maintain a registry of all swarm agents, their domain capabilities, consensus weights, and mailbox queues.
2. **REST Endpoints**:
   - `GET /a2a/agents` & `GET /a2a/topics` for live topology.
   - `POST /a2a/messages/send` & `POST /a2a/broadcast` for dispatching.
   - `POST /a2a/consensus/propose` & `POST /a2a/consensus/vote` for managing proposal lifecycle.
   - `GET /a2a/locks`, `POST /a2a/locks/acquire`, `POST /a2a/locks/release` for resource mutex.
   - `GET /a2a/telemetry` & `GET /a2a/dlq` for tracing and poisoned message inspection.

## 6. Common Pitfalls & Lessons Learned
- **Enum String Serialization**: Ensure FastAPI request schemas match exact wire values for enums (e.g., `"majority-vote"` with a hyphen vs `"majority_vote"`, and ProposalStatus `"accepted"` vs `"approved"`).
- **Timezone-Aware UTC**: Use `datetime.now(datetime.timezone.utc)` instead of deprecated `datetime.utcnow()` to prevent Pydantic serialization deprecation warnings in Python 3.12+.
- **Redis Async Fallback**: Always wrap Redis Pub/Sub calls with an In-Memory fallback queue so tests and offline local environments function without an active Redis daemon.
- **SQLAlchemy ORM Model Direct Instantiation**: Column `default=...` arguments in SQLAlchemy only populate on DB insert; when instantiating models directly in unit tests or before DB flush, unsupplied attributes default to `None`. Always implement a `.to_dict()` helper on ORM models that supplies fallback defaults (`self.status or "online"`) to guarantee clean JSON serialization across FastAPI routers and unit tests.
- **Service Method Parameter Signature Flexibility**: Core service methods (`create_auction`, `submit_bid`, `calculate_composite_score`) should support both object instances and primitive keyword arguments (`task_id` vs `task_or_id`, `bid_price` vs `bid_or_price`) with `**kwargs` catch-alls to ensure seamless interoperability between REST schemas, CLI calls, and internal unit test harnesses.

## 7. Decentralized Task Auctions & SLA Contracts (A2A Mesh)
*(See starter schema in `templates/a2a_auction_bid_template.json`)*
- **Task Auction Pattern**: Initiator agents broadcast `A2ATaskAuction` with `required_capabilities`, `max_budget_units`, and expiration timestamp.
- **Resource Bidding**: Candidate worker nodes submit `A2AResourceBid` evaluating current CPU/RAM load, estimated execution duration, and price.
- **Composite Scoring**: Winning bids are selected via multi-attribute utility formula balancing price, latency, availability, and reputation:
  $$\text{Composite} = w_{\text{price}} \cdot (1 - \frac{\text{Price}}{\text{MaxBudget}}) + w_{\text{latency}} \cdot (1 - \frac{\text{Duration}}{\text{MaxLatency}}) + w_{\text{load}} \cdot (1 - \frac{\text{Load}}{100}) + w_{\text{rep}} \cdot \frac{\text{Reputation}}{\text{MaxReputation}}$$
  *(Standard weights: Price 30%, Latency 25%, Load 25%, Reputation 20%).*
- **Bilateral Negotiation Sessions**: Before or during contract finalization, agents can initiate bilateral `NegotiationSession` with `TaskSpec`, offering counter-proposals (`counter_offer`), accepting, or rejecting.
- **SLA Contracts & Lifecycle**: Finalized auctions or direct negotiations register binding `A2ANegotiationContract` records. Successful delivery (`fulfill_contract`) increases agent reputation score, whereas SLA breach (`breach_contract`) penalizes reputation.
- **Method Signature & Return Ergonomics**: To support both object-based invocations (`submit_bid(auction_id, bid)`) and scalar keyword args (`submit_bid(auction_id, bidder_agent_id=..., bid_price_units=...)`), and allow dual boolean checks (`if submit_bid(...)`) as well as tuple unpacking (`success, bid, msg = submit_bid(...)`), use custom tuple subclasses implementing `__bool__`.

## 8. Swarm Consensus & Leader Fallback (Raft/PBFT-Inspired)
- **Weighted Quorum**: Votes scaled by voter reputation (`reputation_weight`). Calculate approval as $\text{ApprovePower} / (\text{ApprovePower} + \text{RejectPower})$.
- **Quorum Thresholds**: Supermajority ($\ge 66.7\%$) for architecture/deployment decisions; simple majority ($\ge 50.0\%$) for operational routing.
- **Leader Election Fallback**: When consensus rounds stall, select a fallback leader via composite ranking: $\max(\text{reputation} \cdot 0.6 + (100 - \text{CPU\_Load}) \cdot 0.4)$.
- **Signature & Idempotency**: Verify unique vote signatures (`signature_hash`) and reject duplicate or non-eligible voter submissions.

## 9. Dynamic Swarm Load Rebalancing & Heartbeat Eviction
- **Overload Threshold**: Gating node task allocation when CPU or RAM exceeds 80.0%.
- **Heartbeat Timeout**: Treat nodes with no heartbeat for $>15\text{s}$ as degraded/offline.
- **Autonomous Task Migration**: Generate rebalance plans that evict unassigned/in-flight tasks from degraded nodes and redistribute them to the lowest-load nodes possessing required capabilities.

## 10. REST API & WebSocket Telemetry Router Patterns (Phase 4)
- **Router Prefixes in FastAPI**: When registering sub-routers in `main.py` that do not set `prefix` in `APIRouter(...)`, explicitly supply `prefix="/a2a/mesh"` or `/api/v1/a2a` in `app.include_router(router, prefix="/a2a/prefix")` to ensure endpoints map to `/a2a/mesh/...` rather than the root namespace.
- **Floating-Point Quorum Verification**: When comparing approval percentages (e.g. $2.0 / 3.0 = 66.6667\%$) with threshold percentages (e.g. $66.7\%$), use rounded comparison `round(approval_pct, 1) >= round(threshold, 1)` to eliminate false-negative voting rejections from float representation limits.
- **Engine Return Type Handling**: Ensure router handlers safely handle both dict and scalar returns from core engines: `round_id = round_res.get("round_id") if isinstance(round_res, dict) else str(round_res)`.
- **WebSocket Event Streaming**: Maintain an active WebSocket ConnectionManager in `a2a_mesh_ws.py` to stream JSON events (`consensus_voted`, `auction_state_changed`, `load_rebalanced`, `heartbeat_received`) to telemetry subscribers and Generative UI dashboards.
- **Pydantic Model Payload Aliasing for REST Endpoints**: Allow request Pydantic models (e.g., `SubmitBidRequest`, `CreateVotingRoundRequest`, `RebalanceRequest`) to accept alternative parameter names (`bidder_agent_id` vs `bidder_node_id`, `bid_price_units` vs `price_units`, `estimated_duration_ms` vs `estimated_completion_ms`) by setting fields to `Optional[...] = None` and resolving fallback values in the router handler (`agent_id = req.bidder_agent_id or req.bidder_node_id`). This guarantees backward compatibility across heterogeneous UI components, test runners, and older API schemas.
- **Rebalance Result Key Normalization**: Ensure rebalance endpoints resolve task count and plan arrays cleanly across both `reassigned_tasks` and `migrated_tasks` key names (`rebalance_plan = result.get("reassigned_tasks") or result.get("migrated_tasks") or []`) to prevent false `0` reassignment counts in client responses.

## 11. Cross-Platform Agent Federation & Streaming Mesh (DNK-A2A-004)
*(See detailed implementation patterns in `references/cross_platform_mesh_patterns.md`)*
- **Federated Agent Registry (`A2AFederatedAgent`)**: Support external agent frameworks (AutoGPT, CrewAI, LangGraph, OpenCode, Claude Code, Hermes) with multi-tier trust (`tier-0` Kernel, `tier-1` Verified, `tier-2` Standard, `tier-3` Sandboxed), SHA-256 token hashing, and public key verification.
- **Formal Capability Contracts (`A2ACapabilitySchema`)**: Register machine-verifiable input/output JSONSchemas, target SLA latencies, invocation cost units, and rate limits per capability key.
- **Trace-Context Wire Envelopes (`A2AMessageEnvelope`)**: Standardize wire transport with distributed OpenTelemetry-compatible tracing (`trace_id`, `span_id`, `parent_span_id`), communication patterns, payload signatures, and delivery tracking.
- **Real-Time CoT & Event Streaming (`A2AStreamSession`)**: Support Server-Sent Events (SSE) and gRPC streaming for Chain-of-Thought (CoT), token generation, tool execution progress, and artifact delivery with bounded backpressure windows.
- **Dynamic Routing & Resilient Circuit Breakers (`A2ARoutingTable`)**: Maintain capability routing with primary and fallback agent node lists. Tripped routes (`OPEN`) after threshold consecutive failures seamlessly fail over to secondary nodes while periodically testing health via `HALF_OPEN` probes.
- **Synthetic Health Probes (`A2AHealthProbe`)**: Continuously collect telemetry (latency ms, CPU %, memory MB, HTTP status) through synthetic RPC and heartbeat probes to dynamically update node health weights.


