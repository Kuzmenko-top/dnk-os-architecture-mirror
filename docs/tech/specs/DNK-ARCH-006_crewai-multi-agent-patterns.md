# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-006_crewai-multi-agent-patterns.md"
# purpose: "Architecture Specification for crewAI-style Role-Based Multi-Agent Workflows"
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

# 🏗️ Architecture Specification: crewAI Multi-Agent Patterns (DNK-ARCH-006)

This specification defines the integration of crewAI-style role-based multi-agent patterns into the DNK OS Core, complementing our existing LangGraph-style stateful graph architecture.

## 1. Role-Based Agent Integration

The crewAI pattern introduces rich persona-driven prompting as a first-class citizen in DNK OS. Rather than using generic system messages, our core agent factory (`core/agent_factory/`) integrates role-playing fields:
- **Role:** Explicit title (e.g. `dnk_koder` -> `Senior Systems Architect`).
- **Goal:** Specific target boundaries.
- **Backstory:** High-signal contextual motivation.

This structured metadata is automatically compiled into the system prompts of subagents (Rick, Yuriy, Cas), enhancing domain specificity and reasoning quality.

## 2. Pipelined Task Dependencies (Crew Unit of Work)

To handle linear or hierarchical tasks efficiently, we introduce the **Crew Unit of Work** pattern:
- **Tasks as Pipeline Steps:** Task inputs and expected outputs are clearly structured. When executing in a linear "Crew", the output of task `N` is automatically injected as context for task `N+1`.
- **Durable Queues:** Tasks are scheduled via our asynchronous background queues (`core/queues/`), supporting prioritized worker polling.

## 3. Hybrid Orchestration (LangGraph + crewAI)

DNK OS utilizes a unified hybrid orchestration model:
- **LangGraph as the Master Orchestrator:** Used for complex state transitions, cycles, human-in-the-loop validation, and overall system state management.
- **Crews as Leaf Pipelines:** Individual nodes inside the master LangGraph can compile and trigger a "Crew" (a sequential or hierarchical multi-agent team) to solve a concrete, linear subtask (such as writing code, generating documentation, or scraping products).

```
 [Master LangGraph Stateful Orchestration]
                    |
                    v
    [Node 1: Research (Crew Unit)] ---> (Executes Crew: Rick & Yuriy sequentially)
                    |
                    v
    [Node 2: Code Synthesis (Crew)] -> (Executes Crew: Cas & Tiffany)
```

## 4. Impact on Core Modules
- `core/orchestrator/`: Integrates crew execution adapters.
- `core/agents/`: Adds support for Role, Goal, and Backstory metadata.
- `core/queues/`: Task dependency queue handling for sequential task passing.
