---
name: "agentic-habits"
description: "Agentic habits, three-tier enforcement ladder, deterministic completion-gate verification, and 12 anti-habits catalogue assimilated from AgriciDaniel/agentic-habits."
version: "1.0.0"
category: "governance"
assimilated_at: "2026-09-05"
---

# --- DNK-MRH-HEADER ---
# mrh_id: "skills/agentic-habits/SKILL.md"
# purpose: "DNK OS Assimilated Skill: Three-Tier Enforcement, Completion Gate & Anti-Habit Elimination."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

# 🧬 Agentic Habits & Three-Tier Guard System

> **Donor Repository**: `https://github.com/AgriciDaniel/agentic-habits`  
> **License**: MIT (Track 1: Direct Component & Template Assimilation)  
> **Core Value**: *"Loading an instruction is deterministic. Following it is not."*

---

## 🏛️ 1. The Three-Tier Enforcement Ladder

| Tier | Name | Mechanism | Reliability | DNK OS Implementation |
|---|---|---|---|---|
| **Tier 1** | **Stated** | Rules in `AGENTS.md`, `SOUL.md`, `SKILL.md` formatted as `When -> Do / Instead` | ~50–70% (Advisory) | Context-budgeted prompt rules (≤12 system, ≤10 project, ≤6 path) |
| **Tier 2** | **Gated** | Deterministic Lifecycle Hooks (Stop-Hooks, Pre/Post Tool Hooks) | **100% (Deterministic)** | `scripts/system/hermes_pre_tool_hook.py`, `core/guards/completion_gate.py` |
| **Tier 3** | **Judged** | Independent read-only verifier (`gerych_auditor`) evaluating evidence | **Objective Audit** | Evidence Ledger (`[RAW]` log vs `[INFER]` claim). Formula: *No evidence = not PASS* |

---

## 🪜 2. The Habit Repair Ladder

When an agent violates a rule or repeats an operational mistake, follow this 3-step escalation ladder:

1. **Miss 1 (Sharpen Trigger)**: Rephrase rule to explicit `When [Specific Condition] -> Do [Action] / Instead of [Anti-Pattern]`.
2. **Miss 2 (Constrain Scope)**: Move rule closer to the point of impact (e.g. per-directory rule, specific path filter).
3. **Miss 3 (Escalate to Gate)**: **Stop writing prompt rules.** Implement a deterministic hook in `hermes_pre_tool_hook.py` or `core/guards/completion_gate.py` that physically blocks the action with exit code / rejection JSON.
   *(There is no 4th rung. Do not repeat prompts.)*

---

## 🚫 3. The 12 Anti-Habits Catalogue

| # | Anti-Habit | Description | Corrective Action |
|---|---|---|---|
| 1 | **Phantom Done** | Claiming a task/test is complete without actually executing the verification command. | Tier 2 `CompletionGate`: Intercept claims, block turn until `verify_all.sh` / `pytest` runs cleanly. |
| 2 | **Green-Washing** | Suppressing errors via `\|\| true`, catching all exceptions silently, or modifying tests to fake pass. | Tier 2 Pre-Tool Hook blocks test tampering and masks. |
| 3 | **Guess Stacking** | Repeatedly editing files without reading error traces or running reproduction commands. | Circuit breaker blocks >2 consecutive edits without verification. |
| 4 | **Drive-By Refactor** | Modifying unrelated files or reformatting code outside task scope. | Restrict diff to targets declared in TaskDNA / MASE slice. |
| 5 | **Silent Assumption** | Making unverified assumptions about dependencies or environment rather than checking. | Read config or query SCONES before coding. |
| 6 | **Context Amnesia** | Re-reading files already in context or failing to check existing architectural artifacts. | Circuit breaker blocks consecutive identical reads. |
| 7 | **Confident Invention** | Hallucinating non-existent APIs, CLI flags, or mock responses. | Query live schema or official docs before generating calls. |
| 8 | **Sycophantic Fold** | Blindly agreeing with an incorrect prompt assumption rather than checking repository ground truth. | Validate via `git status`, test suite, and AST checks. |
| 9 | **Boil the Ocean** | Trying to execute a massive multi-module overhaul in a single monolithic turn. | MASE (Mandatory Atomic Slice Execution): limit turns to ≤25 tool calls. |
| 10 | **Narration Theatre** | Generating long explanations of what the agent "plans to do" instead of making tool calls. | Execute actions directly, summarize with evidence upon completion. |
| 11 | **Cleanup Destruction** | Deleting tests, documentation, or historical records to "clean up". | HermesRuntime dry-run simulation and auto-rollback protection. |
| 12 | **Habit Hoarding** | Bloating prompt files with dozens of vague rules until model degrades. | Strict context budget: ≤12 system, ≤10 project, ≤6 path rules. |

---

## 💻 4. Python API: Completion Gate Integration

```python
from core.guards.completion_gate import CompletionGate, VerificationEvidence

# Check assistant message against executed session tool evidence
evidence = VerificationEvidence(
    commands_executed=["pytest tests/verification/test_obsidian_vault_path_hygiene.py"],
    exit_codes=[0],
    test_passed=True
)

gate = CompletionGate()
verdict = gate.evaluate(
    assistant_message="All unit tests passed successfully and verify_all is clean.",
    evidence=evidence
)

if not verdict.allowed:
    print(f"BLOCKED: {verdict.reason}")
    # Force agent to execute tests or remove unverified claim
```
