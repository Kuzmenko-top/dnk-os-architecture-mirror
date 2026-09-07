# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-020_crewai-patterns.md"
# purpose: "Architecture Patterns and Topology Spec for crewAI Framework Assimilation"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

# 🏛️ ARCHITECTURE SPEC: CREWAI PATTERNS (DNK-ARCH-020)

Architecture patterns, multi-agent process pipelines, and task delegation topologies assimilated from `crewAIInc/crewAI` into `DNK_HUB`.

---

## 📌 Architectural Topology

crewAI orchestration revolves around 3 primary structural components:

```
                  ┌─────────────────────────────────────┐
                  │              Crew                   │
                  │  (Process: Sequential / Hierarchical)
                  └──────────────────┬──────────────────┘
                                     │
            ┌────────────────────────┴────────────────────────┐
            ▼                                                 ▼
  ┌──────────────────┐                              ┌──────────────────┐
  │      Task        │ ◄──── (Context Passing) ──── │      Task        │
  │     (Task 1)     │                              │     (Task 2)     │
  └─────────┬────────┘                              └─────────┬────────┘
            │                                                 │
            ▼                                                 ▼
  ┌──────────────────┐                              ┌──────────────────┐
  │      Agent       │ ◄─── (Delegation & Query) ──►│      Agent       │
  │    (Role A)      │                              │    (Role B)      │
  └─────────┬────────┘                              └─────────┬────────┘
            │                                                 │
            ├──► Tools (Custom / API)                         ├──► Memory Store (Short/Long/Entity)
            └──► LLM Provider                                 └──► LLM Provider
```

---

## 🔑 Core Architectural Patterns

### Pattern 1: Sequential Process Pipeline ($T_1 
ightarrow T_2 
ightarrow T_3$)
In sequential mode, the `Crew` executes tasks in the exact list order specified. Output from task $i$ is appended to the prompt context of task $i+1$, ensuring zero context loss across multi-stage workflows (e.g. Research ➔ Drafting ➔ Editing).

### Pattern 2: Hierarchical Manager Orchestration
In hierarchical mode, a manager agent orchestrates task distribution:
1. Manager inspects the crew's task list and agent capabilities.
2. Manager dynamically selects the appropriate worker agent for Task 1.
3. Worker agent executes task and submits output back to Manager.
4. Manager evaluates output quality; if unsatisfactory, requests revision or delegates to another worker.

### Pattern 3: Inter-Agent Delegation & Peer Consultation
Agents configured with `allow_delegation=True` can dynamically delegate subtasks or query peer agents during execution:
```
[ Agent A (Researcher) ] ──── Delegate Task ────► [ Agent B (Code Analyst) ]
         ▲                                                  │
         └────────────── Returns Sub-Result ────────────────┘
```

### Pattern 4: Hybrid LangGraph Master + Crew Leaf Pipelines
In DNK OS architecture, complex non-linear graphs (with loops, human-in-the-loop gates, and time-travel checkpoints) are managed by `LangGraph` at the top level, while linear sub-workflows are delegated to lightweight `Crew` pipelines as leaf nodes:

```
[ LangGraph Master Engine ]
        │
        ├──► Node 1: State Evaluation
        ├──► Node 2: [ Crew Pipeline (Researcher + Writer) ] (Leaf Work Unit)
        └──► Node 3: Verification & Output Gate
```

---

## 🛡️ Integration Contract with DNK OS Core
In DNK OS (`DNK-DOMAIN-SWARM`), crewAI patterns map into core services:
- `Agent` (Role/Goal/Backstory) ➔ `dnk_agent_swarm_service`
- `Crew` (Sequential/Hierarchical Process) ➔ `dnk_swarm_orchestrator`
- `Memory` (Short/Long/Entity) ➔ `dnk_memory_shadow_service`
