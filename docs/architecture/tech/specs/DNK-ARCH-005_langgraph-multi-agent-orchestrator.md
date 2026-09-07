# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-005_langgraph-multi-agent-orchestrator.md"
# purpose: "Architecture Specification for the LangGraph-style Stateful Multi-Agent Orchestrator"
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

# 🏗️ Architecture Specification: LangGraph Stateful Orchestration (DNK-ARCH-005)

This specification defines the architectural design of the stateful multi-agent graph orchestrator for DNK OS Core, inspired by `langchain-ai/langgraph` and integrated with MCP tool routing.

## 1. System Topology

The DNK OS Core Stateful Orchestrator organizes agent interactions as a directed state graph. Unlike custom static DAGs, this architecture supports looping, state modification, checkpointing, and dynamic tool-routing adapters.

```
       [Centralized Shared State (TypedDict)]
                 ^               ^
                 | Read/Write    |
                 v               v
 [Node: Rick (Scout)] ----> [Node: Yuriy (Slicer)]
         ^                         |
         |                         v
         |                  <Decision Edge>
         |                         |
         |                         +---> [Node: Cas (Synthesizer)]
         |                         |
         +-------------------------+ (Re-evaluate/Cycle)
```

## 2. Stateful Execution Loop

The execution engine follows a dual-track loop:
1. **Compute Track (Nodes):** Invokes functional or agentic nodes. Each node takes the current shared state, performs a subtask (e.g. searching code, patching files), and returns a dictionary of state updates.
2. **Transition Track (Edges & Routers):** Consumes node output, resolves conditional edges, updates the persistent checkpoint store, and decides the next node(s) to execute.

### 2.1 State Merging and Reducers
- Shared state updates are merged following predefined field reducers.
- Messages, logs, or file alterations use append/upsert reducers to prevent overwriting valuable history.

### 2.2 Durable Checkpointing
- The system captures state snapshots before and after every node execution.
- Checkpoints are saved using standard relative path configurations (e.g. `./sessions/{thread_id}/checkpoints/`) preventing absolute host path leaks.
- Enables instant resumption of paused agent workflows or rollback (time-travel) to fix error trajectories.

## 3. Human-in-the-Loop Interrupts

- Nodes or edges can designate `interrupt_before` or `interrupt_after` requirements.
- When an interrupt condition is encountered (e.g. code deployment, billing threshold reached, raw filesystem write), execution is paused, state is committed to a `PAUSED` checkpoint, and a Maksym approval token is requested.
- Execution safely resumes only after a valid cryptographic token signature from the host is verified.

## 4. MCP Adapter Topology

- **MCP Client Adapter:** Translates external Model Context Protocol (MCP) server JSON-RPC schemas into standard DNK OS execution schemas.
- **Dynamic Routing:** Dynamically exposes and routes calls to active MCP servers (`postgresql`, `obsidian`, `context7`) to the execution nodes, providing the stateful loop with immediate SOTA knowledge.
