# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-043_agno_infinite_canvas_patterns.md"
# purpose: "Architecture Specification for Agno Agent/Team/Workflow Integration into DNK OS Infinite Canvas."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-CANVAS-AGNO-ARCH"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

# 🏛️ DNK-ARCH-043: Agno Spatial Execution & Infinite Canvas Architecture Specification

## 1. Overview & Objectives
This specification formalizes the architectural integration of **Agno multi-agent primitives** (Agents, Teams, Workflows, Memory, Checkpoints, and HITL approvals) with the **DNK OS Infinite Canvas Engine**.

The goal is to provide a reactive, visual, high-throughput spatial execution environment where:
1. Every Agent, Swarm Team, and Workflow is an addressable node on an infinite 2D plane.
2. Data flows between nodes via typed connection edges with runtime validation.
3. Long-running asynchronous execution states (running, paused for HITL, completed, failed) are persisted and synchronized in real-time.
4. Memory and vector knowledge can be attached dynamically to canvas nodes.

---

## 2. System Topology & Component Layout

```
                                  DNK OS INFINITE CANVAS
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                        │
│   [ 🧠 SCONES Memory Node ] ───────┐                                                   │
│      (Workspace Knowledge)         │                                                   │
│                                    ▼                                                   │
│   [ 🤖 Agent Node: Gerych ] ───► [ 👥 Team Node: Swarm ] ───► [ ⚡ Workflow Node: DAG ]│
│      • Model: Gemini 2.5            • Mode: Route/Broadcast     • Step 1: Liquid AST   │
│      • Tools: Code, Git, Bash       • Workers: [Shopify, Dev]   • Step 2: Test Gate    │
│                                    ▲                                                   │
│   [ 🛑 HITL Approval Gate ] ───────┘                                                   │
│      • Token Budget / Deployment                                                       │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                    │  WebSocket / JSON-RPC / SSE
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DNK AGNO CANVAS ADAPTER (Hexagonal Core)                        │
├────────────────────────┬───────────────────────────────┬───────────────────────────────┤
│ Canvas Node Translator │ Agno Workflow DAG Engine      │ Checkpoint & State Manager    │
├────────────────────────┼───────────────────────────────┼───────────────────────────────┤
│ Team Consensus Router  │ SCONES Memory Synchronizer    │ HITL Sandbox & Policy Guard   │
└────────────────────────┴───────────────────────────────┴───────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND AGENT RUNTIME (FastAPI / SSE)                          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Architectural Subsystems

### 3.1 Canvas AST to Agno Runtime Graph Translation
- The Infinite Canvas maintains a directed acyclic graph (DAG) of nodes:
  - `agent_node`: Instantiates an autonomous Agno agent configured with specific tools, system instructions, and LLM providers.
  - `team_node`: Instantiates a multi-agent team with coordination modes (`route`, `broadcast`, `tasks`, `consensus`).
  - `workflow_node`: Executes sequential or parallel pipelines composed of steps (`StepNode`, `ParallelNode`, `ConditionNode`).
  - `memory_node`: Supplies persistent contextual memory from SCONES.
  - `tool_node`: Binds local DNK tools or MCP server endpoints.
  - `hitl_node`: Intercepts sensitive operations and suspends execution until user verification.

### 3.2 State Machine & Asynchronous Checkpointing
Every node on the canvas transitions through a deterministic state machine:
- `IDLE`: Node configured, awaiting inputs.
- `QUEUED`: Inputs ready, scheduled for execution in topological order.
- `RUNNING`: Active LLM reasoning or tool invocation in progress with token streaming.
- `PAUSED_HITL`: Execution suspended pending human approval for dangerous tool call / quota limit.
- `COMPLETED`: Execution succeeded, output emitted to connected output ports.
- `FAILED`: Execution halted with error; error payload serialized for visual inspection.

### 3.3 Two-Way Memory Synchronization
- **Canvas to SCONES**: When an agent node concludes a run with `enable_agentic_memory=True`, extracted facts, user preferences, and synthesized artifacts are committed to SCONES Memory DB.
- **SCONES to Canvas**: Upstream memory nodes inject workspace-scoped memories (`ws-alpha-001`) into the agent's dynamic context before prompt compilation.

---

## 4. Execution Flow Sequence

```
User (Canvas UI)        Canvas Adapter           Agno Runtime Engine         SCONES Memory / DB
      │                       │                          │                           │
      ├── [Execute Graph] ───►│                          │                           │
      │                       ├── [Compile Node DAG] ───►│                           │
      │                       │                          ├── [Query Context] ───────►│
      │                       │                          │◄── [Workspace Memories] ──┤
      │                       │                          │                           │
      │                       │                          ├── [Execute Step 1 (Agent)]│
      │                       │◄── [Stream Token SSE] ───┤                           │
      │◄── [Update UI Node] ──┤                          │                           │
      │                       │                          ├── [Require HITL Approval] │
      │◄── [Show Prompt] ─────┼◄── [Paused Checkpoint] ──┤                           │
      │                       │                          │                           │
      ├── [User: "Approve"] ─►├── [Resume Checkpoint] ──►│                           │
      │                       │                          ├── [Execute Step 2 (Tool)] │
      │                       │                          ├── [Save Session State] ──►│
      │◄── [Graph Finished] ──┼◄── [Final Output] ───────┤                           │
```

---

## 5. Architectural Invariants & Non-Functional Requirements
1. **Zero Thread-Locking**: All HITL operations must be persisted as serializable checkpoints in SQLite / Postgres; no active worker threads or open DB locks during user wait.
2. **Schema Strictness**: All inputs and outputs traversing canvas edges MUST conform to Pydantic v2 schemas.
3. **Decoupled Architecture**: The Canvas UI must interact with Agno primitives exclusively through `DnkAgnoCanvasAdapter` using asynchronous events.
4. **Resilience**: Any node failure should isolate the sub-branch without crashing the canvas process.
