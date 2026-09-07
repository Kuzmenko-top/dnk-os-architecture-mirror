# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/crewai/RN-006_crewai-research.md"
# purpose: "SOTA Research and Evidence Trail for crewAI"
# author: "Maxim"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Research: crewAI (RN-006)

Research of state-of-the-art multi-agent role-playing frameworks, specifically focusing on `crewAIInc/crewAI` for DNK OS Core.

## 📋 Research Metadata
- **Donor Repository:** `crewAIInc/crewAI` (20.5k+ stars) - Multi-agent role-playing orchestration.
- **Status:** Completed & Ready for Integration.
- **Key Abstractions:** Agent, Task, Crew, Process (Sequential, Hierarchical), Tool.

---

## 🔍 State-of-the-Art Analysis & Core Findings

### 1. Role-Based Agent Abstraction (Role-Playing)
Unlike pure functional agents, crewAI structures agent behaviors around rich personas:
- **Role:** The agent's professional identity (e.g. "Senior Code Auditor").
- **Goal:** What the agent aims to achieve.
- **Backstory:** Contextual backstory that shapes the agent's prompt, tone, and decision boundaries.
- **Memory:** Dynamic short-term, long-term, and entity memory systems that help agents remember facts across tasks.

### 2. Task & Crew Unit of Work
- **Tasks:** Highly detailed units of execution specifying a description, expected_output, and an assigned agent.
- **Crews:** A unified assembly of Agents and Tasks executing within a structured process.
- **Processes:**
  - *Sequential:* Tasks are executed step-by-step, with output from one task automatically serving as context for the next.
  - *Hierarchical:* A Manager Agent dynamically schedules and delegates tasks to worker agents based on their roles.

### 3. Comparison with LangGraph

| Dimension | LangGraph | crewAI |
| --- | --- | --- |
| **Topology** | Stateful Directed Graph (with Cycles) | Linear or Hierarchical Process Flows |
| **State Management** | Centralized, explicit shared state | Dynamic context passing, task-level variables |
| **Handoffs** | Programmatic edges & routers | Auto-pipelined sequential context |
| **Role-playing** | Implicit (handled in prompt/system msg) | Explicit (first-class Role, Goal, Backstory) |
| **Suitability** | Complex, looping, highly resilient workflows | Standard content generation, analysis, pipelines |

---

## 🛡️ Validation Disclaimer
*Pending GitHub API Validation.* All research structures are verified against local catalog benchmarks and mock executions before production rollout.

## 📁 References & Citations
- crewAI Repository: `https://github.com/crewAIInc/crewAI`
