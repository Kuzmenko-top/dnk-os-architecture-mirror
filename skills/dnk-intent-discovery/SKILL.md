---
name: "dnk-intent-discovery"
description: "Socratic Inception Protocol for turning ambiguous developer goals into canonical intent.md artifacts."
version: "1.0.0"
category: "software-development"
author: "Antigravity (Head of Orchestration) & Gerych (Hermes Prime)"
license: "MIT"
metadata:
  hermes:
    tags: ["sdlc", "intent", "golden-thread", "inception", "socratic", "architecture"]
    related_skills: ["plan", "test-driven-development", "sota-repository-assimilation"]
---

<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "skills/dnk-intent-discovery/SKILL.md"
# purpose: "SOTA Inception & Socratic Discovery Protocol for DNK OS AI-Native SDLC."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-INTENT-DISCOVERY"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Antigravity & Gerych"
# --- END DNK-MRH-HEADER ---
-->

# 🎯 DNK Intent Discovery Skill (Phase 0: The Golden Thread)

## 📌 When to Use This Skill
Activate this skill whenever:
1. The developer requests a **new feature**, **new service**, **visual app component**, or **major refactoring**.
2. The user's prompt is high-level, visionary, or underspecified (e.g. "let's build a video pipeline", "integrate open design canvas", "add shopify checkout functions").
3. Starting any multi-step development cycle for **DNK OS MVP**.

> **Cardinal Rule**: NEVER jump directly into writing application code (`services/`, `apps/`) before completing the Socratic Inception phase and signing off `docs/intents/{INTENT_ID}_{slug}.intent.md`.

---

## 🏛️ The Socratic Interview Protocol (3–5 Questions)

When activated, the agent MUST pause execution and conduct a structured Socratic interview with Maxim:

### Question 1: Problem Statement & Value Metric
> *"Яку конкретну проблему кінцевого користувача чи розробника ми вирішуємо, і як ми виміряємо успіх (latency, conversion, автономність)?"*

### Question 2: Bounded Context & Blast Radius
> *"Які саме модулі (`apps/*`, `services/dnk_*`, `core/*`) зачіпає ця зміна, і які існуючі API/схеми БД ми НЕ маємо права зламати?"*

### Question 3: Explicit Non-Goals (Межі та Не-Цілі)
> *"Що ми СВІДОМО НЕ робимо у цій ітерації, щоб не роздувати скоуп (Non-Goals)?"*

### Question 4: Deterministic Proof Criteria
> *"Які тести або автоматичні перевірки (Playwright headless screenshot, pytest, API response status) будуть 100% доказом виконання?"*

---

## 📝 Canonical Workflow Steps

### Step 1: Conduct Socratic Interview
Engage in a concise, high-signal dialogue in Ukrainian (🇺🇦). Identify contradictions between desired features and DNK OS architecture invariants.

### Step 2: Generate Intent Artifact
Using `docs/templates/INTENT_TEMPLATE.md`, generate:
`docs/intents/{INTENT_ID}_{slug}.intent.md`

Where:
- `{INTENT_ID}`: `INTENT-YYYYMMDD-XXX` (e.g. `INTENT-20260903-001`)
- `{slug}`: Short kebab-case name (e.g. `canvas-live-compiler`)

### Step 3: Verify Intent Conformance
Ensure the generated intent includes:
- [x] Valid MRH header (`DNK-STD-0075`).
- [x] Clear Bounded Context.
- [x] At least 2 explicit Non-Goals.
- [x] Measurable Acceptance Criteria.
- [x] Interview Q&A Transcript.

### Step 4: Hand Off to Spec & Plan Gates
Once the developer says "Approved" / "Погоджую":
1. Generate `docs/tech/specs/{ID}_spec.md`.
2. Call `dnk_decompose_task_dna` or run Plan Mode to generate `docs/plans/{ID}_plan.md`.
3. Spawn isolated Git Worktree for Swarm execution.

---

## 🧪 Anti-Pattern Checklist (What to Avoid)
- ❌ **Do not** write code before `intent.md` is committed.
- ❌ **Do not** assume default behavior without asking about edge cases.
- ❌ **Do not** allow fuzzy criteria like "make it fast and beautiful" — require measurable metrics (e.g. "renders < 150ms", "WCAG 2.1 AA compliant").
