<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/templates/GERYCH_TASK_TEMPLATE.md"
# purpose: "Canonical Task Formulation & Specification Standard v2.5 for Gerych Prime and Swarm Agents."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Approved"
# version: "2.5.0"
# updated_at: "2026-09-04"
# author: "Antigravity (Mentor & Chief Architect) & DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
-->

# 📋 Gerych Task Specification Standard (v2.5)

> **Zero-Waste High-Velocity Protocol (ZWSP) & Mandatory Atomic Slice Execution (MASE)**
> This standard governs all tasks dispatched to **Gerych (Hermes Prime)** and collaborating swarm agents.
> Strict adherence guarantees 100% first-pass completion, zero token waste, and prevents tool-exhaustion loops.

---

## 🎯 Task Header & Metadata

- **Task ID**: `TASK-DNK-[DOMAIN]-[YYYYMMDD]-[001]` *(e.g. TASK-DNK-REMOTION-20260904-001)*
- **Title**: `[Short, descriptive title of the task]`
- **Domain / Bounded Context**: `[apps/visual_shell | apps/api | services/dnk_* | core/*]`
- **Primary Executor**: `[gerych_prime | gerych_builder | dnk_dev_fullstack | dnk_shopify | dnk_video_ai_creator | gerych_auditor]`
- **Collaborating Swarm Agents**: `[e.g. gerych_researcher, dnk_scones_memory, gerych_auditor]`
- **Execution Mode**: `[MUTATION (Code Modification) | READ_ONLY_AUDIT (Investigation / Analysis)]`
- **Estimated Complexity**: `[P0 Critical | P1 High | P2 Medium | P3 Low]`

---

## ⚡ Zero-Waste Execution Contract

Every task MUST enforce the following operational invariants:

| Parameter | Invariant Specification | Purpose |
| :--- | :--- | :--- |
| **Max Tool Calls / Slice** | **≤ 25 tool calls per turn** | Prevents 90/90 budget exhaustion and context saturation. |
| **Virtualenv SSOT** | `.venv` / `$VIRTUAL_ENV` pre-bound | Python and pytest must execute inside project virtualenv. |
| **Context Diet** | `view_file(StartLine, EndLine)` (80–120 lines) | Never dump whole multi-hundred line files into context. |
| **Circuit Breaker** | Block repeated reads & consecutive blind edits | Force verification/test runs between modifications. |
| **Path Invariant** | **Relative paths ONLY** (`./`, `../`) | Zero absolute system paths (`/Users/...`) in code or tests. |
| **MRH Invariant** | Header mandatory on Python/YAML/Markdown | DNK-STD-0075 compliance verified by `verify_all.sh`. |

---

## 💡 1. Problem Statement & Architectural Goal

- **Current State & Context**:
  > [Describe the current behavior, missing feature, or failing component with references to previous tasks/PRs]
- **Target State & Business Value**:
  > [Describe the exact desired outcome and how it enhances the DNK OS ecosystem]
- **Explicit Non-Goals (Out of Scope)**:
  - ❌ [Non-goal 1: e.g. Do not touch unrelated services or tests]
  - ❌ [Non-goal 2: e.g. Do not introduce new external npm packages unless listed]

---

## 🗺️ 2. Targeted File Manifest

Specify the exact files to create, modify, or delete. Do NOT leave file locations ambiguous.

| Action | Target Relative Path | Responsibilities / Core Symbols |
| :--- | :--- | :--- |
| `[NEW]` | `apps/.../filename.ts` | `[Exported functions, classes, interfaces]` |
| `[MODIFY]` | `services/.../module.py` | `[Functions to update or extend]` |
| `[MODIFY]` | `tests/.../test_target.py` | `[Test coverage additions]` |

---

## 🧩 3. Mandatory Atomic Slices (MASE)

Decompose the task into discrete, sequentially verifiable atomic slices. Each slice must take ≤ 25 tool calls.

### 🔹 Slice 1: Core Implementation / Scaffolding
- **Goal**: [Build foundational types, schemas, or service logic]
- **Target Files**: `[List 1-2 files]`
- **Validation Check**: `[Command to verify Slice 1, e.g. npx tsc --noEmit or pytest tests/unit/test_slice1.py]`
- **Budget**: ≤ 20 tool calls.

### 🔹 Slice 2: Integration & Runtime Hooking
- **Goal**: [Wire up the component to event bus, API routers, or canvas engine]
- **Target Files**: `[List 1-2 files]`
- **Validation Check**: `[Command, e.g. vitest run tests/... or curl test endpoint]`
- **Budget**: ≤ 20 tool calls.

### 🔹 Slice 3: Swarm Verification & Evidence Certification
- **Goal**: [Run full test suite and compile evidence artifact]
- **Target Files**: `[Handoff / Evidence generation]`
- **Validation Check**: `bash scripts/verify_all.sh`
- **Budget**: ≤ 10 tool calls.

---

## 🧠 4. SCONES & Distillation Context

- **Memories to Query**:
  - Run `scones_get_memories(query="[Relevant Domain / Topic]")` before starting.
- **Known Distillations / Solutions**:
  - Query `dnk_query_error_solutions(error_text="[Known error or symptom]")`.
  - *Example Pattern*: For `RuntimeEventBus`, import from `core.runtime_events`, NOT `core.event_bus`.
  - *Example Pattern*: Always check lines with `view_file` before applying `replace_file_content` to match exact whitespace.

---

## 🛡️ 5. Quality Gate & Verification Protocol

### A. Local Component Tests
```bash
# Frontend / Vitest:
npx vitest run apps/visual_shell/src/__tests__/target_component.test.ts

# Backend / Python:
.venv/bin/pytest tests/unit/test_target_service.py -v
```

### B. Master Quality Gate
```bash
# Mandatory on MUTATION tasks:
bash scripts/verify_all.sh
```

### C. Evidence & Handoff Generation
```bash
python3 scripts/system/generate_evidence.py \
  --task "<TASK_ID>" \
  --title "<TASK_TITLE>" \
  --components <PATH_TO_MODIFIED_FILE_1> <PATH_TO_MODIFIED_FILE_2>
```

---

## ✅ 6. Definition of Done (DoD) Checklist

Before reporting task completion to the orchestrator or user, ensure:

- [ ] All specified atomic slices implemented without skipping requirements.
- [ ] No absolute `/Users/...` paths exist in newly written code or tests.
- [ ] Valid DNK-MRH header present on all new/updated Python, YAML, and Markdown files.
- [ ] Local tests pass with 100% Green status.
- [ ] If `MUTATION` mode: `bash scripts/verify_all.sh` executes with 0 failures.
- [ ] Evidence report generated in `docs/reports/` or `docs/evidence/`.
- [ ] Response to user provided in Ukrainian (🇺🇦) with clickable file links.
