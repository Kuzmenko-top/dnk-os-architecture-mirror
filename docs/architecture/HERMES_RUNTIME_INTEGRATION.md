# --- DNK-MRH-HEADER ---
# mrh_id: "docs_architecture_hermes_runtime_integration"
# purpose: "Architecture specification for integrating Hermes Agent as an Execution/Runtime Layer under DNK_HUB Control Plane."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

# 🏛️ Hermes Agent Runtime Integration Architecture

## 1. Architectural Philosophy & Layer Separation

Hermes Agent (upstream `NousResearch/hermes-agent`) is **strictly an execution and runtime engine**, NOT the mind, identity, or supervisor of Gerych, and NOT the control plane of DNK OS.

The canonical layered architecture of Gerych within DNK OS:

```text
       ┌────────────────────────────────────────────────────────┐
       │             LLM Tier: Gemini / Vertex AI               │
       └──────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
       ┌────────────────────────────────────────────────────────┐
       │                     Model Adapter                      │
       └──────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
 ══════╡ EXECUTION & RUNTIME LAYER (Hermes Agent Engine) ╞══════
       │  • Agent Loop & Trajectory Management                  │
       │  • Tool Execution Sandbox & Terminal Transport         │
       │  • Session State & DB Management                       │
       │  • Delegation Primitives (`delegate_task`)             │
       │  • Scheduled Cron Scheduler                            │
       │  • Peer Messaging (`hermes peer`)                      │
       │  • Desktop / Browser Automation Rung                   │
       │  • Core File Approval Sandboxing                       │
 ═════════════════════════════════╤═════════════════════════════
                                  │
                                  ▼
 ══════╡ DNK_HUB CONTROL PLANE & GOVERNANCE (Gerych Core) ╞═════
       │  • Gerych Prime Identity & Supervisor Authority        │
       │  • TaskDNA Directed Acyclic Graph (DAG) Engine         │
       │  • Swarm Multi-Agent Orchestrator (14 Profiles)        │
       │  • SCONES L1/L2/L3 Cognitive Memory Management         │
       │  • Dynamic Toolset Registry & Permission Matrix        │
       │  • Financial Accounting, Token Budgeting & OCC Merge   │
       │  • Adversarial Review & Pre-Commit Verification Gates  │
       └────────────────────────────────────────────────────────┘
```

## 2. Core Invariants

1. **No Autonomous Policy Grant**: Capabilities provided by the Hermes runtime (such as peer messaging or browser clicks) do NOT automatically grant permissions in DNK OS. All operations must adhere to `docs/security/HERMES_PERMISSION_MATRIX.md`.
2. **Supervisor Precedence**: Gerych Prime is the sole supervisor. Subagent profiles cannot negotiate tasks autonomously without TaskDNA decomposition and supervisor auditing.
3. **Traceability**: All runtime interactions (peer messages, tool calls, delegation lifecycle events) must be normalized into DNK-compatible event streams per `core/contracts/hermes_event_contract.yaml`.
4. **Isolated Upgrades**: Changes to the runtime engine must follow the Staged Assimilation Runbook (`docs/operations/HERMES_UPGRADE_RUNBOOK.md`). Blind file overwrites are forbidden.
