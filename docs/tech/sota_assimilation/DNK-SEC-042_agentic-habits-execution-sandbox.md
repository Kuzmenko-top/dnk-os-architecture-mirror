# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-SEC-042_agentic-habits-execution-sandbox.md"
# purpose: "Security Specification: Adversarial Gatekeeping, SpendGuard Budget Limits, and Anti-Greenwashing Sandboxing."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Herich Librarian"
# --- END DNK-MRH-HEADER ---

# Security & Sandboxing: Habit Guards & Anti-Hallucination Controls (DNK-SEC-042)

## 1. Threat Model & Mitigation Matrix

| Threat / Anti-Habit | Attack Vector / Failure Mode | Mitigating Control | Enforcement Tier |
|---|---|---|---|
| **Phantom Done** | Agent declares task complete without executing verification suite | `CompletionGate.evaluate()` blocks turn termination if claims made without non-zero exit code | Tier 2 Gate Hook |
| **Green-Washing** | Masking exit codes via piping (`cmd \|\| true`) or claiming tests passed | `HabitJudge.audit()` requires raw evidence with exit code 0 on verified runners | Tier 3 Ledger Audit |
| **Guess Stacking** | Multi-file edits without intermediate tests leading to cascading bugs | Atomic slice boundary (≤25 tools per turn, MASE) | Tier 1 & Orchestrator |
| **Drive-By Refactor** | Modifying unauthorized files outside declared scope | `HabitJudge` validates `touched_files` against `target_files` | Tier 3 Ledger Audit |
| **Narration Theatre** | Token burn through speculative rambling instead of tool actions | Ratio check: >5 `[INFER]` entries with 0 `[RAW]` triggers violation | Tier 3 Ledger Audit |

## 2. SpendGuard & Recursion Prevention Invariants
1. **Never Recurse**: When a gate intervention fires, `stop_hook_active` is flagged to prevent infinite interception loops.
2. **Reward Disclosure**: If an agent explicitly discloses missing tests ("I have not yet run pytest"), turn completion is allowed unconditionally.
