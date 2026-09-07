# Unified Swarm Control Plane & Engine Consolidation Protocol

## Overview
Consolidates 6 disparate coordination modules (`swarm_coordinator.py`, `swarm_engine.py`, `swarm_orchestrator.py`, `workflow_orchestrator.py`, `agent_coordinator.py`, and Hermes subprocess delegates) into a single authoritative DAG State Machine & Control Plane (`core/orchestrator/control_plane.py`).

## Core Invariants

### 1. State Machine & Node Lifecycle
Nodes transition deterministically through defined states:
`PENDING -> SCHEDULED -> RUNNING -> COMPLETED | FAILED | PAUSED_APPROVAL | RETRYING`

- `PENDING`: Enqueued in DAG, awaiting dependency completion.
- `SCHEDULED`: All parent dependencies are `COMPLETED`, ready for execution.
- `RUNNING`: Execution dispatched to worker.
- `PAUSED_APPROVAL`: Paused at a Human-in-the-Loop approval gate (`requires_approval=True`).
- `COMPLETED`: Successfully finished; output cached in node result.
- `FAILED`: Exhausted `max_retries` with error trace captured.
- `RETRYING`: Transient error encountered, scheduled for retry after backoff.

### 2. DAG Scheduling & Cycle Detection
- Uses Depth-First Search (DFS) graph coloring to detect cycles (`has_cycle()`) before dispatch.
- Resolves execution order using topological sorting via Kahn's algorithm or iterative DFS.

### 3. Fault-Tolerant Checkpointing (`StateCheckpointer`)
- Snapshots execution graph state to atomic JSON files (`checkpoints/{run_id}.json`).
- Dynamic Node Reconstitution: when restoring into a fresh `SwarmControlPlane` instance, nodes present in the checkpoint that are not yet instantiated in `self.nodes` MUST be dynamically reconstructed as `TaskNode` instances with their persisted status, payload, retries, and results.
- Preserves output immutability: step results are stored alongside node state so subsequent steps can replay dependencies without re-execution.

### 4. Strangler Fig Facade Pattern
To maintain 100% backward compatibility:
- `WorkflowOrchestrator` delegates DAG chains and task submissions to `SwarmControlPlane`.
- `SwarmOrchestrator` delegates prompt orchestration, skill injection, and execution to `SwarmControlPlane`.
- `Supervisor` in `SwarmEngine` registers steps and executes fault-tolerant retries through `SwarmControlPlane`.
- `ControlPlaneAgentCoordinator` implements `AgentCoordinator` abstract base class by wrapping `SwarmControlPlane`.
- `GerychSwarmCoordinator` anchors all 14 swarm agent operations to `self.control_plane`.

### 5. High-Speed Sub-50ms Skill RAG
- Inverts token-heavy vector lookups with sub-50ms set-intersection keyword and role-tag filtering.
- Gracefully permits ad-hoc worker roles by falling back to matching across all registered skill pools if a role has no specialized tag restrictions.

### 6. SwarmDirector Facade & 14-Agent Routing Matrix (`core/orchestrator/swarm_director.py`)
- Authoritative singleton facade for all 14 DNK OS swarm agents (`gerych_prime`, `gerych_builder`, `gerych_researcher`, `gerych_auditor`, `dnk_dev_fullstack`, `dnk_shopify`, `dnk_video_ai_creator`, `dnk_security_guard`, `dnk_scones_memory`, `dnk_analytics`, `dnk_erp_supply`, `dnk_finance_cfo`, `dnk_marketing_cmo`, `herich_librarian`).
- Semantic routing engine: maps incoming task descriptions to the optimal agent based on domain keywords with support for explicit `preferred_agent` override.
- Native DAG coordination: builds and triggers execution workflows directly through `SwarmControlPlane.add_step` and `execute_graph`.
- Swarm status aggregator: exposes `get_swarm_status()` for visual canvas, metrics, and health observability.

### 7. SwarmEngineAdapter Quantum-to-DAG Translation Bridge (`core/swarm/engine_adapter.py`)
- Bridges quantum engine abstractions (`TaskQuantum`, `SubagentSession`) into `SwarmControlPlane` DAG nodes (`TaskNode`).
- Translates execution status: maps completed/failed execution results (`QuantumExecutionResult`) into control plane node states (`VERIFIED`, `FAILED`).
- Pipeline batch runner: `execute_quanta_via_control_plane` runs a sequence of quanta through the topological control plane, returning structured execution metrics.

### 8. ExecutionBroker & Fluent Pipeline Builder (`core/framework/execution_broker.py`)
- Mediation layer between API/application interfaces and the underlying Swarm Control Plane.
- Fluent `PipelineBuilder` API: enables chaining steps (`.step(node_id, payload, dependencies=[...], agent=...)`) and direct execution (`.run()`).
- Telemetry & batch processing: tracks execution latency, node failure counts, and execution timestamps across parallel/sequential jobs.
