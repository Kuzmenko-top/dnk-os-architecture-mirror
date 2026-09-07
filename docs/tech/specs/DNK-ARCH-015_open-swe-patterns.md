# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-015_open-swe-patterns.md"
# purpose: "Architectural Patterns Extraction for open-swe Integration into DNK OS Swarm Engine"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-14"
# --- END DNK-MRH-HEADER ---

# 🏗️ DNK Architecture Spec: open-swe Patterns (DNK-ARCH-015)

Architectural patterns extracted from `langchain-ai/open-swe` for building autonomous software engineering agents in `DNK_HUB`.

---

## 1. System Topology

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DNK OS Application Layer                         │
│                         (DNKSwarmEngine / Task Forest)                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │    DNKSWEDispatcher         │  (Task Routing & Context Filter)
                     └──────────────┬──────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐
│   DNKSWEScheduler    │ │  DNKLangGraphAdapter │ │  DNKContainerSandbox │
│ (Queue / Concurrency)│ │ (Planner-Edit-Verify)│ │  (Isolated Execution)│
└──────────────────────┘ └──────────────────────┘ └──────────────────────┘
```

---

## 2. Key Extracted Patterns

### 2.1 Closed-Loop Plan-Edit-Test Cycle
- **Step 1 (Context Dispatch):** Pack workspace files and issue description.
- **Step 2 (Plan):** Generate structured implementation steps.
- **Step 3 (Edit):** Apply targeted code patches (`patch` / `write_file`).
- **Step 4 (Test):** Run pytest / container tests in sandboxed runtime.
- **Step 5 (Self-Healing Loop):** If test fails, distill error memory and loop back to Step 3 (max 3 retries).

### 2.2 Container Sandbox Isolation
- All code evaluations run inside ephemeral Docker containers mapped to `DNK_HUB`.
- Zero pollution on host macOS environment.

---

## 3. Integration Plan for `DNK_HUB`
- Integrate `DNKSWEDispatcher` with `core/coordinators/`.
- Integrate `DNKSWEScheduler` with `core/queues/`.
- Use `DNKLangChainAdapter` and `DNKLangGraphAdapter` to drive the plan-edit-verify loops.
