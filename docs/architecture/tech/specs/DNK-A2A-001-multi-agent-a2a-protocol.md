# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-001"
# purpose: "TaskDNA & Architectural Specification for Multi-Agent A2A Protocol (P2P, Supervisor-Worker, Broadcast, RedLock, Consensus Engine)"
# canonical_source: true
# alters_files: ["apps/api/services/a2a_protocol_engine.py", "tests/verification/test_a2a_protocol_engine.py"]
# triggers_tasks: ["DNK-A2A-001-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

# 🤖 DNK-A2A-001: Multi-Agent Agent-to-Agent (A2A) Protocol Specification

## 1. Overview & Objective
The **DNK Multi-Agent A2A Protocol** (`apps/api/services/a2a_protocol_engine.py`) defines an enterprise-grade, high-velocity communication and coordination standard across the 14 specialized Swarm Agents (`gerych_builder`, `gerych_researcher`, `gerych_auditor`, `dnk_dev_fullstack`, `dnk_shopify`, `dnk_video_ai_creator`, `dnk_security_guard`, `dnk_scones_memory`, etc.).

It solves inter-agent messaging, distributed consensus, concurrent state mutation locking, and execution telemetry with zero race conditions and verifiable auditability.

---

## 2. Core Architectural Pillars

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           A2A Protocol Engine                           │
│                                                                         │
│  ┌────────────────────┐   ┌────────────────────┐   ┌─────────────────┐  │
│  │ A2A Message Router │   │  Consensus Engine  │   │ State Lock Mgr  │  │
│  │ (P2P, Sup/Worker,  │   │(Majority, Unanimous│   │ (Redis RedLock  │  │
│  │  Broadcast/PubSub) │   │ Weighted Quorums)  │   │  & OCC Engine)  │  │
│  └─────────┬──────────┘   └─────────┬──────────┘   └────────┬────────┘  │
│            │                        │                       │           │
│            └────────────────────────┼───────────────────────┘           │
│                                     ▼                                   │
│                     ┌──────────────────────────────┐                    │
│                     │ A2A Telemetry & Trace Engine │                    │
│                     │  (TraceId, Span, Latency,    │                    │
│                     │   pgvector / UI Integration) │                    │
│                     └──────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Pillar 1: Multi-Pattern Message Router
Supports 3 fundamental coordination topologies:
1. **Peer-to-Peer (P2P)**: Direct point-to-point asynchronous request/reply between two agents with SLA timeouts.
2. **Supervisor-Worker**: Hierarchical dispatching where a coordinator agent delegates subtasks across worker agents and aggregates partial results.
3. **Broadcast / PubSub**: Topic-based event fanout across interested swarm subscribers (e.g. `audit.critical_alert`, `memory.sync_required`).

### Pillar 2: Swarm Consensus Engine
Guarantees distributed agreement for critical architectural and security decisions:
- **`majority_vote`**: Requires $> 50\%$ (or $2/3$) affirmative votes from participating nodes.
- **`unanimous`**: Requires $100\%$ approval (mandatory for security policies and production deployments via `gerych_auditor`).
- **`weighted`**: Dynamic voting weights based on domain specialization (e.g., `gerych_auditor` has weight 3.0 for security, `gerych_builder` weight 3.0 for frontend/UI).

### Pillar 3: Distributed State & Concurrency Lock (RedLock + OCC)
- **Redis RedLock Integration**: Prevents race conditions during shared workspace or file writes across parallel agents.
- **Heartbeat Auto-Renewal**: Automatic TTL extension while an agent is executing long-running builds.
- **Dead-Letter Queue (DLQ)**: Traps malformed or timed-out envelopes with automatic poisoned message isolation.

### Pillar 4: High-Resolution Telemetry & Generative UI Bridge
- Every envelope carries `trace_id`, `span_id`, `parent_span_id`, `sender_agent`, `recipient_agent`, and `timestamp_ns`.
- Real-time serialization to telemetry endpoints consumed by Generative UI Dashboard components.

---

## 3. Data Contracts & Wire Specifications (JSON-RPC 2.0 / A2A-ML-001)

### A2A Envelope Model
```json
{
  "jsonrpc": "2.0",
  "id": "msg_9f8c12e4",
  "trace_id": "trc_84a7bc19",
  "pattern": "supervisor_worker",
  "sender": "gerych_builder",
  "recipient": "dnk_dev_fullstack",
  "topic": "task.codegen.backend",
  "payload": {
    "task_id": "DNK-TASK-849",
    "action": "generate_fastapi_router",
    "params": {"schema": "payment_intents"}
  },
  "timeout_ms": 5000,
  "created_at": "2026-08-28T14:30:00Z"
}
```

### Consensus Proposal & Vote Models
- `A2AConsensusProposal`: `proposal_id`, `topic`, `mechanism`, `threshold`, `participants`, `votes`, `status` (`pending`, `accepted`, `rejected`, `expired`).
- `A2AConsensusVote`: `voter_agent`, `vote` (`approve`, `reject`, `abstain`), `weight`, `rationale`, `signature`.

---

## 4. Invariants & Guardrails (DNK-STD-0075)
1. **Schema Strictness**: All message routing and payloads must validate via Pydantic v2 schemas; invalid payloads are immediately rejected to DLQ.
2. **Zero-Waste Latency**: In-memory and Redis message routing under 5ms per hop (P95).
3. **Auditability & ASR**: Integrated security check by `gerych_auditor` on sensitive broadcast topics (ASR < 5.0%).
4. **Relative Path Hygiene**: Telemetry and logs use clean relative path identifiers.
5. **Quality Gate**: 100% pass on `bash scripts/verify_all.sh`.
