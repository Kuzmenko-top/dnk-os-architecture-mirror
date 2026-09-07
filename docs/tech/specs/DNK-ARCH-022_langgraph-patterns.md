# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-022_langgraph-patterns.md"
# purpose: "Architecture & Topology Specifications for LangGraph Cyclic Workflows"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

# 🏛️ Architecture Specification: LangGraph Patterns (DNK-ARCH-022)

This specification defines the architectural patterns and state-graph topologies assimilated from `langchain-ai/langgraph` into DNK OS.

---

## 📐 Cyclic State Graph Topologies

### 1. Agent-Tool Loop Topology

```
                  ┌──────────────┐
                  │    START     │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Agent Node   │◄──────────────┐
                  └──────┬───────┘               │
                         │                       │
                Conditional Router               │ State Update
                         │                       │ (Tool Results)
           ┌─────────────┴─────────────┐         │
           ▼                           ▼         │
    [ Has Tool Calls ]          [ Final Answer ] │
           │                           │         │
           ▼                           ▼         │
    ┌──────────────┐             ┌───────────┐   │
    │  Tool Node   │────────────►│   END     │───┘
    └──────────────┘             └───────────┘
```

### 2. Human-in-the-Loop Interrupted Flow

```
   ┌──────────────┐      ┌─────────────────┐      ┌──────────────┐
   │ Input State  │─────►│ Pre-Check Node  │─────►│  [PAUSE]     │
   └──────────────┘      └─────────────────┘      │ HITL Gate    │
                                                  └──────┬───────┘
                                                         │ Human Approval / State Edit
                                                         ▼
                                                  ┌──────────────┐
                                                  │ Commit Node  │
                                                  └──────────────┘
```

---

## ⚙️ Core Architectural Components

### 1. `DNKStateGraph`
Flow controller maintaining registered node functions, direct edges, and conditional routing functions.

### 2. `DNKGraphState`
Immutable state container with schema validation and explicit key reducers (e.g., `append_messages`, `merge_dict`).

### 3. `DNKCheckpointer`
Persistence layer storing graph state snapshots across execution steps (`MemoryCheckpointer`, `PostgresCheckpointer`).

### 4. `DNKCompiledGraph`
Executable graph instance exposing `.invoke()`, `.stream()`, and `.resume()` interfaces.
