# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/agentic_habits_three_tier_enforcement_and_completion_gates.md"
# purpose: "Reference patterns for Agentic Habits: Three-Tier Enforcement, Stop Hooks, and Anti-Habit Audits."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧬 Agentic Habits: Three-Tier Enforcement, Completion Gates & Anti-Habit Auditing

> Assimilated from `AgriciDaniel/agentic-habits` (MIT License).

## 1. Core Paradigm: The Limits of Context Instructions
An agent's bottleneck is not memory or instruction storage, but deterministic enforcement.
As measured on Anthropic's *Impossible Tasks* benchmarks:
- Forceful written instructions in context reduce error rates from ~55% to ~23-35%.
- **Written instructions leave ~25-33% of failures standing.**
- Writing rules "louder" (Caps Lock, repeated prompts) degrades context attention and causes instruction collisions.

## 2. The Three-Tier Enforcement Ladder
1. **Tier 1: Stated (Rules / Context Hints)**
   - Format: `When [Trigger] -> Do [Action] / Instead [Replacement]`.
   - Strict Context Budgets: System Scope (<= 12 rules), Project Scope (<= 10 rules), Path Scope (<= 6 rules).
   - Adding a rule at the budget limit requires retiring or merging a weaker rule.
2. **Tier 2: Gated (Deterministic Lifecycle Hooks)**
   - Implemented via shell stop-hooks (e.g. `completion-gate.sh`).
   - Intercepts turn termination if the agent claims success (*"tests pass"*, *"all green"*, *"build is clean"*) without having executed an actual verification command (`pytest`, `tsc`, `verify_all.sh`) with exit code 0.
   - Fail-open & recursion guard: blocks once per turn, never deadlocks.
3. **Tier 3: Judged (Independent Read-Only Auditor)**
   - Executed by an isolated subagent (`gerych_auditor`).
   - Read-only tools only (no edit/write tools).
   - Emits an **Evidence Ledger** distinguishing `[RAW]` tool outputs/diffs from `[INFER]` assumptions.
   - Core rule: **No evidence means not PASS**.

## 3. The Habit Repair Ladder
When an agent misses a rule:
- **Miss 1**: Sharpen the trigger (`When -> Do/Instead`).
- **Miss 2**: Change placement (narrow to specific paths or elevate scope).
- **Miss 3**: Escalate to a deterministic Gate (hook) or retire it. *There is no fourth rung.*

## 4. The 12 Anti-Habits Matrix
- `Phantom done`: Claiming completion without running verification.
- `Green-washing`: Masking failures with `|| true` or ignoring stderr.
- `Guess stacking`: Sequential speculative edits without root-cause diagnosis.
- `Drive-by refactor`: Unprompted restyling of neighboring files.
- `Silent assumption`: Acting on unverified domain assumptions.
- `Context amnesia`: Re-asking questions answered in transcripts/memories.
- `Confident invention`: Hallucinating non-existent APIs or parameters.
- `Sycophantic fold`: Conceding errors without checking test facts.
- `Boil the ocean`: Monolithic turns violating MASE (<= 25 tools).
- `Narration theatre`: Verbose descriptions of future plans instead of immediate execution.
- `Cleanup by destruction`: Deleting tests/code to make builds pass.
- `Habit hoarding`: Inflating prompt rules beyond token budgets.

## 5. Practical Implementation Notes & Pitfalls
- **Evidence Ledger Strict Separation**: `EvidenceLedger` entries must mandate a distinct modality flag (`is_raw: bool`). Raw entries represent unmanipulated tool/test subprocess outputs; inferred entries represent the model's self-evaluations. The `HabitJudge` requires at least one raw exit-code zero verification entry before accepting completion.
- **Fail-Closed Gate vs Fail-Open Stop Hook**: Tier 2 completion gates in CI/CD or local test runners should fail closed (blocking exit), while interactive REPL stop-hooks should fail open on unexpected execution crashes with a single warning to prevent infinite agent recursion loops.
