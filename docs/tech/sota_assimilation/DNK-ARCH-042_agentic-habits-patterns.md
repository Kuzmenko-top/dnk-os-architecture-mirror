# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-ARCH-042_agentic-habits-patterns.md"
# purpose: "Architecture Specification: Three-Tier Habit Enforcement, Completion Gates, and Habit Ledger Patterns in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Herich Librarian"
# --- END DNK-MRH-HEADER ---

# Architectural Patterns: Three-Tier Habit Enforcement (DNK-ARCH-042)

## 1. System Topology & Three-Tier Hierarchy

```
       +-------------------------------------------------------+
       |             Tier 1: Soft Behavioral Directives        |
       |  (AGENTS.md, SOUL.md, Prompts, When->Instead triggers) |
       +-------------------------------------------------------+
                                  |
                                  v
       +-------------------------------------------------------+
       |             Tier 2: Deterministic Turn Gates          |
       |  (CompletionGate in core/guards/completion_gate.py)    |
       |  - Intercepts turn completions asserting test pass    |
       |  - Requires non-zero RAW test execution telemetry     |
       |  - Fail-open & Hedging-disclosure compliant           |
       +-------------------------------------------------------+
                                  |
                                  v
       +-------------------------------------------------------+
       |             Tier 3: Judged Habit Review & Ledger      |
       |  (HabitJudge & EvidenceLedger in core/guards/)        |
       |  - Separation: [RAW] tool logs vs [INFER] narratives   |
       |  - Adversarial audit against 12 Anti-Habits           |
       |  - Governed by Gerych Auditor before git commit       |
       +-------------------------------------------------------+
```

## 2. Invariants & Guardrails
1. **Evidence Grounding**: No claim of completion is valid without corresponding entries in `EvidenceLedger` marked as `EvidenceType.RAW`.
2. **Drive-By Containment**: Modifications outside `target_files` trigger an immediate `DRIVE_BY_REFACTOR` anti-habit violation.
3. **Fail-Open Safety**: Any parse failure or unexpected exception in the gate falls open to prevent agent loop deadlocks.
