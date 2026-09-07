---
mrh_id: "DNK-SKILL-STD-001"
title: "DNK OS Skill Format Evaluation & Standardisation Proposal"
purpose: "Evaluate existing assimilated skill formats and propose the thin 'Index + Recipes' standard to optimize context tokens and avoid drift."
canonical_source: true
status: "Active"
version: "1.0.0"
updated_at: "2026-08-10"
author: "Maxim"
license: "DNK-INTERNAL"
---

# 🧬 DNK-SKILL-STD-001: DNK OS Skill Format Evaluation & Standardisation

This standard evaluates the current structure of DNK OS assimilated skills using two primary case studies: `open_canvas_assimilated` and `managed_deepagents_assimilated`. It addresses the strategic choice between monolithic skill formats and a decoupled, token-efficient **"Index + Recipes"** architecture.

---

## 📌 1. Executive Summary

- **Core Problem:** Monolithic, text-heavy skill definitions (containing hundreds of lines of code, logs, and verbose descriptions) dramatically inflate LLM context windows during orchestration, leading to **high token costs, latency spikes, and severe knowledge drift** across duplicate document copies.
- **Proposed Solution:** Establish the **"Index + Recipes" (Thin Skill) standard**. Under this protocol, any `SKILL.md` file must serve strictly as:
  1. A **lightweight router/index** (under 50 lines) mapping directly to decentralized specifications (`RN-00X`, `DNK-ARCH-00X`, `DNK-COMP-00X`, `DNK-SEC-00X`).
  2. A repository of **minimal executable recipes** (1-2 quick bootstrap bash/python snippets) for immediate agent startup.

---

## 🔍 2. Case Study Evaluation: `open_canvas_assimilated`

### A. Evaluation Against the 4 Core Pillars

1. **🧭 Navigation (Rating: Outstanding - 10/10):**
   - The file lists clear, absolute paths pointing directly to the decomposed files. An orchestrator or developer agent can parse this structure instantly and retrieve the targeted document in a single step.
2. **🔄 Integration (Rating: Good - 8/10):**
   - Excellent alignment with the Next.js visual shell. However, the skill lacks concrete "Getting Started" terminal commands or code execution recipes within the file itself.
3. **🛡️ Duplication (Rating: Excellent - 10/10):**
   - Minimal to zero duplication. All implementation details (ProseMirror editors, React Flow states, event bindings) are fully relegated to `DNK-COMP-001` and `DNK-ARCH-001`. There is no risk of cognitive mismatch.
4. **⏱️ Recency/Maintenance (Rating: Outstanding - 10/10):**
   - Since the skill is a thin index, it is highly immune to decay. When React Flow hooks or Zustand state signatures change, the index file itself requires zero edits—only the localized `DNK-COMP-001` or component code requires updates.

### B. Real-World MVP Development Scenarios

- **Scenario 1: Custom Agent Node Creation in Next.js Visual Shell**
  - When the agent `dnk-dev-01` needs to implement a custom workflow block on the infinite canvas, it reads `SKILL.md` and routes directly to the Component Contract in `DNK-COMP-001_editors.md`. This allows the agent to fetch the exact interface props (`ArtifactRendererProps`, `onContentChange` callback signature) and write fully compatible React code.
- **Scenario 2: State Synchronization Over WebSockets to PostgreSQL**
  - During back-end database sync configuration, Gerych reads the index and loads `DNK-ARCH-001_canvas-artifacts.md` to retrieve the database schema for the `hub_memory.artifacts` table. Gerych then implements a WebSocket event handler that updates the artifact's state in PostgreSQL and issues a clean `conn.commit()` transaction.

---

## 🔍 3. Case Study Evaluation: `managed_deepagents_assimilated`

### A. Evaluation Against the 4 Core Pillars

1. **🧭 Navigation (Rating: Outstanding - 10/10):**
   - Leverages relative markdown links and filesystem references (`file:../../docs/tech/specs/...`), which allows standard markdown parsers and LLMs to transition instantly from the index to the detailed specs.
2. **🔄 Integration (Rating: Outstanding - 9/10):**
   - Extremely high integration value. It explicitly includes the direct `pytest` command `pytest tests/verification/test_sandbox_hygiene.py` at the bottom of the skill, making it immediately executable by Gerych.
3. **🛡️ Duplication (Rating: Excellent - 10/10):**
   - Zero duplication of Calico network policy files or docker-compose volume mounts. All security standards are completely isolated in `DNK-SEC-002_sandbox-network-egress.md`.
4. **⏱️ Recency/Maintenance (Rating: Outstanding - 10/10):**
   - Keeping the skill thin guarantees that any changes in Kubernetes NetworkPolicies or Docker image tags do not deprecate the skill index. Only the security standard file is edited.

### B. Real-World MVP Development Scenarios

- **Scenario 1: Securing High-Risk Tool Execution for Scraper Agents**
  - When spinning up the `dnk_web_research` subagent to crawl external domains, Gerych reads the index, locates `DNK-SEC-002_sandbox-network-egress.md`, and configures the agent's docker runtime with Calico iptables, forcing a default-DROP policy and restricting egress strictly to validated web endpoints.
- **Scenario 2: Traversal Defense on Cross-Language Filesystem Contracts**
  - During Python subagent workspace configuration, Gerych uses the isolated filesystem contract defined in `DNK-COMP-002_isolated-fs-contracts.md` to build relative path verification, catching and raising `PathTraversalError` if a subagent attempts to read a file outside the designated `/workspace` boundary.

---

## 🏛️ 4. Strategic Recommendation: Monolithic vs. "Index + Recipes"

| Feature | Monolithic Skill Format | "Index + Recipes" (Proposed Standard) |
| :--- | :--- | :--- |
| **Token Consumption** | High (5,000 - 15,000 input tokens per call) | **Low (under 400 input tokens)** |
| **Risk of Drift** | High (same spec copied in multiple files) | **Zero (single source of truth in `/docs`)** |
| **Agent Bootstrap** | Slower (agent must parse large text blocks) | **Fast (immediate bash/code snippet execution)** |
| **Code Refactoring** | Difficult (multiple files require updates) | **Simple (only local component spec is updated)** |

### 🏆 Verdict: Universal Transition to "Index + Recipes" (Thin Skills)

We recommend **standardising all DNK OS skills** onto the **"Index + Recipes"** format:
1. **The Skill as a Router:** Keep the `SKILL.md` under 40-50 lines. It acts as an address book pointing to the decentralized specs.
2. **On-Demand Loading:** The orchestrator loads the skill index first, parses it, and then queries only the *specific* child document (`DNK-ARCH`, `DNK-COMP`, etc.) that is relevant to the active sub-task.
3. **Include Executable Recipes:** Maintain a `## 🛠️ Executable Recipes` section in the skill with 1-2 code blocks of actual code templates or terminal commands, so the agent can immediately launch verification tests or bootstrap boilerplate templates.

---

## 🛡️ 5. Skill-to-Spec Routing Algorithm (Mental Model)

```
              [ User asks to edit a component ]
                              │
                              v
                [ Load Thin SKILL.md Index ]
                              │
                              v
         [ Parse SPEC Paths inside SKILL.md Index ]
                              │
            ┌─────────────────┼─────────────────┐
            v                 v                 v
     [ Load DNK-COMP ]  [ Load DNK-ARCH ] [ Load DNK-SEC ]
            │                 │                 │
            └─────────────────┼─────────────────┘
                              v
             [ Execute Code Change with 100% ]
             [ Type-Safety & Zero Token Waste]
```

This protocol ensures perfect context hygiene, zero billing overhead, and high execution speed for Gerych and all subagents.

---

## Scope & Applicability

This SKILL standard applies to:

- Assimilation of external open-source repositories (e.g., open-canvas, managed-deepagents, open_design, LangGraph, CrewAI).
- Complex DNK OS modules where:
  - We have RN / DNK-ARCH / DNK-COMP / DNK-SEC / SOTA specs.
  - We want agents and developers to quickly locate and apply these specs in real code.

This standard does NOT need to be used for:

- Small internal utilities or one-off scripts.
- Minor bugfixes or UI tweaks that do not introduce new architecture or contracts.
- Simple configuration-only changes.

---

## Canonical SKILL Template: Index + Recipes

Each SKILL.md MUST be a thin document (ideally <= 40–50 lines) with two main sections:

1. **Index** – links into the canonical specs under `docs/` and `skills/`.
2. **Recipes** – 1–2 short, concrete usage patterns that show how to apply the specs in DNK_OS_MVP.

### 1. Index Section

```markdown
# <Repo / Module Name> Assimilation Index

Meta-index for architecture, contracts, and security specs.

## 📁 Core Specifications

1. **[Research & Evidence Trail](../reports/rd_assimilation/<repo>/RN-XXX_<repo>-research.md)**
   - Summary of abstractions, key files, and verification matrix.

2. **[Architecture Specification](../tech/specs/DNK-ARCH-XXX_<topic>.md)**
   - Data models, DB schemas, event bus, lifecycle.

3. **[Component Interfaces & Contracts](../tech/specs/DNK-COMP-XXX_<topic>.md)**
   - Type-safe interfaces (Python / TS), public APIs, error types.

4. **[Security / Sandbox / Egress Standards](../tech/specs/DNK-SEC-XXX_<topic>.md)**
   - Container topology, network policies, filesystem boundaries.

5. **[SOTA Blueprint(s)](../tech/standards/DNK-SOTA-0XX_*.md)** (optional)
   - When a repo defines a reusable SOTA standard (e.g., DNK-SOTA-001 for sandboxed agents).
```

> Note: Paths above are examples; actual relative paths MUST be adjusted per repo layout.

### 2. Recipes Section

```markdown
## 🧪 Quick Recipes (How to Use This Skill)

### Recipe A: Using <Component / Contract> in DNK_OS_MVP

**Goal:** Integrate `<ComponentName>` from the assimilated repo into `visual_shell/web_ui` or `services/`.

- Import the TS interface from DNK-COMP:
  - See: `DNK-COMP-XXX_<topic>.md` for `interface <Name>`.
- Implement a thin wrapper in DNK_OS_MVP:
  - Place in: `services/<module>/` or `visual_shell/web_ui/components/`.
- Wire it into DNK OS event flow:
  - Follow the event bus spec in `DNK-ARCH-XXX_<topic>.md`.

### Recipe B: Applying Sandbox / Egress Policy

**Goal:** Run a DNK subagent with safe egress and filesystem isolation.

- Use `DNK-SEC-XXX_<topic>.md` for:
  - Docker Compose snippets,
  - Calico/iptables rules,
  - Volume masking configuration.
- Implement the Python/TS contracts from `DNK-COMP-XXX_<topic>.md`:
  - `DNKIsolatedFileSystem`,
  - `PathTraversalError`, `ExecutionTimeoutError`.
```

Agents MUST keep Recipes:

- Short and strictly practical (copy-paste friendly).
- Referencing canonical specs instead of duplicating them.
- Focused on **DNK_OS_MVP integration scenarios**, not generic theory.
