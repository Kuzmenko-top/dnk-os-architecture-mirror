<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/templates/INTENT_TEMPLATE.md"
# purpose: "Canonical Machine-Readable Template for Business Intent Specification in DNK OS AI-Native SDLC."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-INTENT-DISCOVERY"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Antigravity (Mentor & Chief Architect)"
# --- END DNK-MRH-HEADER ---
-->

# 🎯 Intent: [Feature, Architecture Change, or Defect Remediation]

## 📋 Metadata
- **Intent ID**: `INTENT-YYYYMMDD-XXX`
- **Originator**: `[Developer / Architect / Automated Monitor]`
- **Domain / Bounded Context**: `[e.g. apps/visual_shell, services/dnk_canvas_api, services/dnk_shopify]`
- **Target Release**: `DNK OS MVP`
- **Created Date**: `YYYY-MM-DD`
- **Status**: `Draft` | `In Review` | `Approved`

---

## 💡 1. Problem Statement & Core Business Value
- **What is the current pain point or bottleneck?**
  > [Describe what doesn't work, what is missing, or why current developer velocity is hindered]
- **Who is the user or beneficiary?**
  > [Developer, Store Merchant, Canvas End-User, Swarm Agent]
- **What is the expected outcome and tangible value?**
  > [Describe the target state after implementation]

---

## 🗺️ 2. Bounded Context & Affected Repositories / Files
- **Target Services / Subsystems**:
  - `services/dnk_*`
  - `apps/*`
  - `core/orchestrator/*`
- **Estimated Blast Radius**: `[LOW | MEDIUM | HIGH]`
- **Existing Contracts Affected**:
  - [List any APIs, database tables, or message queues that might break]

---

## 🚫 3. Explicit Non-Goals (Boundary Invariants)
*What are we explicitly NOT doing in this iteration?*
- ❌ **Non-Goal 1**: [e.g. We are not rewriting the entire DB schema]
- ❌ **Non-Goal 2**: [e.g. We are not adding 3rd-party OAuth providers in this pass]
- ❌ **Non-Goal 3**: [e.g. No manual test edits allowed]

---

## 🔒 4. Critical Constraints & Architectural Invariants
- **Runtime Rules**:
  - Relative paths ONLY (`./`, `../`). Zero hardcoded absolute paths.
  - All Python/YAML/Markdown files MUST have valid MRH headers.
  - Zero modifications to existing tests in `tests/` without explicit `--allow-test-tamper` permission.
  - Performance / Latency budget: `< 200ms` for API endpoints.

---

## 🧪 5. Deterministic Acceptance Criteria (Definition of Done)
- [ ] 1. **Unit & Integration Tests**: 100% pass on `pytest tests/` (zero false-green test modifications).
- [ ] 2. **Static Analysis & Types**: Zero mypy / pyright / ruff errors.
- [ ] 3. **Verification Evidence**: `evidence.json` generated containing deterministic execution proofs.
- [ ] 4. **Adversarial Review**: Passes `scripts/system/gerych_swarm.sh --adversarial-review` with zero critical vulnerabilities.

---

## 💬 6. Socratic Interview Loop (Human-Agent Alignment)
*Transcript of the clarifying questions asked by Antigravity / Gerych to eliminate ambiguity before planning:*

- **Agent Question 1**: *[Ambiguity clarification]*
  - **Developer Answer**: ...
- **Agent Question 2**: *[Edge case / error handling clarification]*
  - **Developer Answer**: ...
- **Agent Question 3**: *[Boundary invariant check]*
  - **Developer Answer**: ...
