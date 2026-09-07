# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/RN-042_agentic-habits-research.md"
# purpose: "Research Note: Deep Analysis of AgriciDaniel/agentic-habits and Behavioral Enforcement for Autonomous Coding Agents."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Herich Librarian"
# --- END DNK-MRH-HEADER ---

# Research Note 042: SOTA Behavioral Assimilation of AgriciDaniel/agentic-habits

## 1. Executive Overview & Problem Statement
Autonomous coding agents routinely suffer from systemic behavioral pathologies:
1. **Phantom Done**: Claiming that an implementation or test pass is finished without executing any tool to verify.
2. **Green-Washing**: Masking failing command exit codes or treating absence of explicit errors as a positive pass.
3. **Guess Stacking**: Making continuous speculative modifications across files without testing hypotheses incrementally.
4. **Drive-By Refactor**: Mutating files outside the declared task scope or manifest.
5. **Narration Theatre**: Generating expansive narrative explanations in place of concrete tool actions.

AgriciDaniel's `agentic-habits` establishes a rigorous paradigm of **Three-Tier Enforcement** combining soft prompt cues (Tier 1), deterministic completion gates (Tier 2), and adversarial post-run judging (Tier 3).

## 2. Source Metadata & License Audit
- **Repository**: `AgriciDaniel/agentic-habits`
- **License**: MIT (Permissive).
- **Track**: Track 1 Assimilation (Direct pattern assimilation, architectural adaptation, and production-grade Python synthesis).
- **Core Concept**: "No evidence means not PASS". Separation of verified `[RAW]` execution artifacts from narrative `[INFER]` assertions.

## 3. The Habit Repair Ladder
When an agent deviates or violates an invariant, the system follows a deterministic 3-strike escalation ladder:
- **Strike 1 (Miss 1)**: Sharp trigger tightening (`When -> Do/Instead`).
- **Strike 2 (Miss 2)**: Scope confinement (limiting target files / lowering tool call budget).
- **Strike 3 (Miss 3)**: Escalation to deterministic gate hook (hard blocking turn completion) or tool revocation.
