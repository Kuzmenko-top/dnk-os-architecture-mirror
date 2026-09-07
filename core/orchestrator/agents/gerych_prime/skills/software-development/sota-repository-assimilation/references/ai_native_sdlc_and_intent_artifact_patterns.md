# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/ai_native_sdlc_and_intent_artifact_patterns.md"
# purpose: "Condensed Architectural Knowledge Bank for AI-Native SDLC, INTENT.MD Artifact Chains, and Spec-Driven Gates."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

# AI-Native SDLC, INTENT.MD Artifact Chains & Spec-Driven Development Patterns

## 1. Core Thesis: Bottleneck Inversion
With autonomous coding agents (Claude Code, Hermes Prime), coding speed has compressed 5-10x. The primary SDLC bottleneck shifts from **Build** to:
- **Left**: Intent Discovery & Architecture Specification (`intent.md` -> `spec.md`).
- **Right**: Autonomous Verification, Guardrail Hooks & Multi-Agent Reviews (`plan.md` -> `evidence.json` -> `REVIEW.md`).

## 2. The Artifact Chain (Golden Thread)
Every development cycle must adhere to a deterministic, human-readable & machine-actionable chain:
1. `intent/*.intent.md`: Inception / Discovery. Iterative agent-user interview loop (probing 3-5 clarification questions, edge cases, non-goals, measurable criteria).
2. `specs/*.spec.md`: Design phase. Automated generation guided by `AGENTS.md`, `skills/`, and domain bounded contexts.
3. `plans/*.plan.md`: Construction plan. **Self-contained invariant**: Plan must be executable by subagents with zero conversational history. Must include: changed files list, task DAG, blast radius, deterministic proof criteria.
4. `evidence/evidence.json`: Verification phase. Autonomous tests, headless browser validation, and zero prose without proof.
5. `REVIEW.md` / PR: Operation phase. Asynchronous PR review by an independent AI Auditor against security & architectural policies.

## 3. Critical Guardrail Invariants
- **Anti-Tampering Test Hook**: When an agent executes a bugfix, pre-tool guardrails must block modifications to existing files in `tests/` to prevent turning failing tests green by deleting asserts.
- **Git Worktree Isolation**: Multi-agent swarms (`dnk_swarm_parallel`) must spawn in isolated `git worktree add .worktrees/<task_id>` branches to prevent dirty working tree conflicts.
- **Continuous Evals Suite**: Maintain 15-20 historical golden issues in `core/evals/` to benchmark prompts, skills, and LLM upgrades in CI.

## 4. SOTA Reference Repositories
- `wico216/ai-sdlc`: 3-phase, 5-gate AI-SDLC framework for Claude Code with Golden Thread and DoR gates.
- `ai-sdlc-framework/ai-sdlc`: Spec-driven AI decision engine with RFC-0011 (DoR Gate) and RFC-0035 (Decision Catalog).
- `github/spec-kit`: GitHub official Spec Kit for Spec -> Plan -> Tasks -> Implement pipelines.
- `switch-dimension/molten-os-core`: Rob Shocks' Agentic Product Development OS with validation, brand, and design skills.
