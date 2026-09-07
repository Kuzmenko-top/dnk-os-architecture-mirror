# --- DNK-MRH-HEADER ---
# mrh_id: "AGENTS.md"
# purpose: "Unified Governance Rules & Zero-Waste High-Velocity Protocol for DNK OS MVP."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.5.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ DNK OS MVP Unified Architecture & Execution Rules

1. **Role Division**:
   - **Antigravity**: Mentor / Architect / Head of Orchestration. Guides architecture, specifications, and quality gates.
   - **Hermes (Gerych)**: Chief Builder & Swarm Manager. Physically constructs files, delegates work across specialized agents, and executes strictly inside the unified `DNK_HUB` workspace.

2. **Unified Workspace & Two-Tier Protocol**:
   - The entire development and R&D hub lives in the unified root: `apps/`, `services/`, `core/`, `tests/`, `scripts/`.
   - Legacy nested subfolders are DEPRECATED and COMPLETELY REMOVED. Everything resides directly at root.
   - Clean standalone releases are generated via `scripts/export_standalone_app.py` per `docs/architecture/TWO_TIER_DEVELOPMENT_PROTOCOL.md`.

3. **Mandatory Invariants**:
   - Relative paths ONLY (`./`, `../`). Never construct or pass absolute `/Users/...` paths in tool calls, file searches, imports, or scripts.
   - All Python/YAML/Markdown files MUST include Machine-Readable Headers (MRH) per `DNK-STD-0075`.
   - Service names prefixed with `dnk_`.
   - Communication with Maxim in Ukrainian (🇺🇦), code in English (🇬🇧).

4. **⚡ Zero-Waste High-Velocity Protocol (MANDATORY)**:
   - **Canonical Task Specification (v2.5)**: Every task assigned to Gerych or delegated across swarm agents MUST strictly follow `docs/templates/GERYCH_TASK_TEMPLATE.md`.
   - **Mandatory Atomic Slice Execution (MASE)**: Multi-step tasks MUST be partitioned into discrete atomic slices bound by ≤ 25 tool calls per slice. Never attempt multi-hour monolithic passes in a single turn.
   - **TaskDNA First**: Before multi-step coding, run `dnk_decompose_task_dna(goal)` to get an evolutionary DAG.
   - **SCONES Retrieval**: Query `scones_get_memories(topic)` to pull existing templates and rules before writing new modules.
   - **Instant Distillation**: On test or lint failures, query `dnk_query_error_solutions(error_text)` immediately instead of guessing.
   - **Swarm Delegation**: Delegate specialized subtasks to domain workers (`dnk_shopify`, `dnk_video_ai_creator`, `dnk_dev_fullstack`, `gerych_auditor`).
   - **Context Diet**: Keep context under 20k tokens by reading targeted code slices (`view_file(StartLine, EndLine)`) instead of whole files.
   - **Adversarial Pre-Commit**: Run `dnk_run_adversarial_review` (Auditor ⚔️ vs Builder 🛡️) before running `scripts/verify_all.sh` and opening PRs.
   - **GitHub Native Fast-Path**: Use environment `$GH_TOKEN` with `gh pr create` or `gh api repos/:owner/:repo/pulls` directly. Never run manual `git credential fill` shell scripts.

5. **🚀 Swarm Parallel Fast-Path Execution (MANDATORY)**:
   - **Environment SSOT**: Subprocesses automatically inherit `$GH_TOKEN`, `$GITHUB_TOKEN`, `$PYTHONPATH`, and `$VERTEX_API_KEY`. Never prompt for manual authentication.
   - **Runtime State Hygiene**: Local JSON databases (`apps/api/visual_shell_db.json`) are ignored in git. Keep the working tree 100% clean for instantaneous branch switching.
   - **Parallel Subagent Dispatch**:
     - `dnk_dev_fullstack`: High-speed generation of API routers, schemas, and ORM models.
     - `dnk_shopify`: E-commerce Liquid AST, Checkout UI, and Shopify Functions.
     - `gerych_auditor`: Background execution of `scripts/verify_all.sh` and fail-closed adversarial gates.
     - `dnk_mentor` (Antigravity): High-level system architecture, cross-module integration, and PR reviews.
