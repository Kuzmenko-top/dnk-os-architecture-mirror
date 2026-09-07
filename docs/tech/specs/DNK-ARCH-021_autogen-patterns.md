# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-021_autogen-patterns.md"
# purpose: "Architecture & Integration Patterns for AutoGen Multi-Agent Conversational Networks"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

# 🏛️ Architecture Specification: AutoGen Patterns (DNK-ARCH-021)

This specification defines the architectural topologies and conversational patterns assimilated from `microsoft/autogen` into the DNK OS core multi-agent framework.

---

## 🎯 Architecture Goals
1. **Conversational Network Layer:** Decouple agent interaction from direct RPC calls, routing messages through structured asynchronous chat channels.
2. **Autonomous Code-Execution Loop:** Implement sandboxed Python/Bash execution with self-healing feedback cycles.
3. **Flexible Swarm Topologies:** Support 1-on-1 paired chats, round-robin group chats, and state-graph-constrained speaker selection.

---

## 📐 Topologies & Interaction Models

### 1. Two-Agent Paired Feedback Loop (Assistant + UserProxy)

```
[ User Request / Goal ]
           │
           ▼
   ┌───────────────┐        Code Block / Plan        ┌───────────────┐
   │ AssistantAgent│ ───────────────────────────────>│ UserProxyAgent │
   │ (LLM Planner) │                                 │ (Sandbox Exec)│
   │               │ <───────────────────────────────│               │
   └───────────────┘       Stdout / Error Trace      └───────────────┘
           │
           ▼ (Termination Condition Met: "TERMINATE")
   [ Final Solution / Summary ]
```

### 2. Group Chat Orchestration (Hub-and-Spoke Topology)

```
                       ┌────────────────────┐
                       │  GroupChatManager  │
                       │  (Speaker Selector)│
                       └─────────┬──────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│  Scout Agent   │      │  Coder Agent   │      │  QA / Critic   │
│  (Data Gather) │      │  (Synthesis)   │      │  (Validation)  │
└────────────────┘      └────────────────┘      └────────────────┘
```

---

## ⚙️ Core Architectural Components

### 1. `DNKConversableAgent`
Base conversational agent capable of sending, receiving, and generating replies via a registered pipeline of handler functions.

### 2. `DNKCodeExecutor`
Pluggable execution environment providing isolation, timeout enforcement, and captured execution logs:
- `DNKLocalCodeExecutor`: Scratch directory execution with clean-up hooks.
- `DNKDockerCodeExecutor`: Ephemeral container execution with volume masking.

### 3. `DNKGroupChat`
State container maintaining shared conversation history, active participant list, and transition rules.

### 4. `DNKGroupChatManager`
Moderator agent driving the selection of the next active speaker using LLM classification or deterministic graphs.

---

## 🔒 Security & Guardrails
- **Execution Sandboxing:** Unsandboxed host execution is strictly prohibited; all code runs inside dedicated workspaces.
- **Max Auto-Reply Limit:** Every conversation turn loop is bounded by `max_consecutive_auto_reply` (default: 10) to prevent infinite token expenditure.
- **Termination Predicate:** Strict evaluation of completion tokens and explicit termination strings (`TERMINATE`).
