# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/README.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 🧬 Technical Reference: DNK OS v2 Core MVP

Welcome, Maxim. This technical documentation details the architecture, design patterns, and internal APIs of **DNK OS v2 Core MVP**, embodying the **"Об'єднане Ядро 3-х Донорів з 5-ма Менторськими Вдосконаленнями"** standard.

---

## 🏛️ Architecture Overview

The system consolidates robust mechanisms from three distinct R&D donors (`open-design`, `hermes-agent`, `agentswarms`) and integrates five advanced mentor-driven optimizations to ensure safe, cost-efficient, and highly auditable agentic execution.

```
                             [ FastMCP Entrypoint Kernel ]
                                           │
         ┌───────────────────┬─────────────┴─────────────┬───────────────────┐
         ▼                   ▼                           ▼                   ▼
  [ Auth Engine ]     [ Canvas Engine ]          [ Hermes Runtime ]   [ Swarm Orchestrator ]
  (open-design)       (open-design)              (hermes-agent)       (agentswarms)
         │                   │                           │                   │
         └───────────────────┼───────────────────────────┴───────────────────┘
                             ▼
                [ Accounting Telemetry Engine ]
```

---

## 🛠️ Module Breakdowns & SOTA Implementations

### 1. Auth & Session Engine (`core/auth_engine.py`)
- **Donor Pattern**: `open-design`
- **Security Standard**: `DNK-STD-0086` Credentials Manager.
- **Key Concepts**:
  - Secure hmac-based timing-attack resistant signature comparison (`hmac.compare_digest`).
  - Session state preservation in a local JSON registry using an **Atomic Write Protocol** (`NamedTemporaryFile` + `os.replace` + `os.chmod` to eliminate file locks or write collisions).
  - Strict file permissions: files write with `0600` (owner read-write only) permissions.
  - Automatic credential redaction (`redact_secret()`) for safe logging of tokens.

### 2. Node-Based Canvas & Component Renderer (`core/canvas_engine.py`)
- **Donor Pattern**: `open-design`
- **Key Concepts**:
  - Manages a directed graph of interactive nodes: `TaskNode`, `AgentNode`, `DocNode`.
  - Color status indication reflecting live state transitions:
    - 🟢 `Done`
    - 🔵 `Executing`
    - 🔴 `Blocked`
    - 🔘 `Queued`
  - Automated Loop Detection: Implements a Depth First Search (DFS) algorithm (`has_cycle()`) to detect circular dependency deadlocks before running pipelines.
  - Interactive ASCII console rendering of tasks and dependencies.

### 3. Safe Execution Runtime (`core/hermes_runtime.py`)
- **Donor Pattern**: `hermes-agent`
- **Key Concepts**:
  - **Dry-Run Planning**: Generates non-destructive plans detailing files to modify and tools to utilize before state mutations.
  - **2-Stage Verification Gate**: Destructive actions (e.g. file deletion, DB drops) are registered as pending authorizations and require explicit matching of Maxim's authorization phrase.
  - **Fail-Closed Auto-Rollback**: Pre-execution file states are backed up as pristine checkpoints. If verification tests fail twice consecutively (`max_failures=2`), the runtime automatically rolls back all file mutations and locks itself to prevent catastrophic regression.

### 4. Hybrid Swarm Orchestrator (`core/swarm_orchestrator.py`)
- **Donor Pattern**: `agentswarms`
- **Key Concepts**:
  - Declarative role manifest loading using YAML formatting.
  - **Sub-0.05s RAG Skill Injection**: Employs an optimized in-memory token inverted-index to query and match procedural skills from `hub_memory` in less than 1ms (well within the 50ms budget), dynamically appending matched skills into the agent's system instructions.

### 5. Financial-Technical Accounting Engine (`core/accounting_engine.py`)
- **Key Concepts**:
  - Automatically logs every execution run with strict telemetry metadata: `tokens_in`, `tokens_out`, `cost_usd`, `duration_ms`, `success` status, and calculated token savings.
  - Aggregates ROI parameters, cumulative dollar savings, and task success metrics.

---

## 🧪 Unit Testing & DoD Verification
- Suite: `core/tests/test_phase1_core.py`
- Test Coverage: **94%+** across the entire package.
- Path Portability: Checked by `path_guard.py` verifying 0 absolute paths.