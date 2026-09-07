# --- DNK-MRH-HEADER ---
# mrh_id: "docs/user-guides/BEST_PRACTICES.md"
# purpose: "15 Essential Best Practices for Development, Swarm Orchestration, and System Architecture in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# DNK OS Best Practices Guide

This guide compiles the 15 architectural, operational, and development standards required to maintain peak velocity, absolute zero-waste execution, and robust stability within the DNK OS ecosystem.

---

## 1. Step 0 Autonomous Triage Before Action
Before opening files or authoring code for any multi-file task, always invoke `dnk_triage_task(prompt)`. Let the autonomous complexity classifier route tasks to `SOLO`, `SWARM_PARALLEL`, or `SWARM_SEQUENTIAL`.

## 2. Mandatory Atomic Slice Execution (MASE)
Partition complex features into independent atomic execution slices bounded by ≤ 25 tool calls. Focus exclusively on target files per slice, run targeted tests, commit, and report milestones.

## 3. Strict Universal Relative Path Invariant
Never pass or construct absolute paths (e.g. `/Users/...` or `C:\...`). Always utilize canonical relative paths (`./apps/web/`, `core/`, `tests/`) to ensure full environment portability and container compliance.

## 4. Machine-Readable Headers (MRH) Everywhere
Every Python, YAML, and Markdown document must feature a canonical `DNK-MRH-HEADER` conforming to `DNK-STD-0075`. This enables automated AST tracking, dependency mapping, and catalog compilation.

## 5. Parallel Swarm Delegation Over Solo Bottlenecks
Gerych Prime acts as orchestrator, not a solo worker. Delegate frontend to `gerych_builder`, backend APIs to `dnk_dev_fullstack`, security testing to `gerych_auditor`, and Shopify tasks to `dnk_shopify` using `dnk_swarm_parallel`.

## 6. SCONES Memory Retrieval First
Before designing interfaces or architectural patterns from scratch, query `scones_get_memories(query=topic)`. Reusing verified solutions eliminates hallucinations and redundant code.

## 7. Fast Symbol Resolution Without File Scans
Refrain from running sequential exploratory grep or find loops. Use `dnk_resolve_symbol(symbol="<name>")` or `repo_map.py` to pinpoint class, interface, and function definitions in under 20 milliseconds.

## 8. Instant Self-Healing Error Distillation
When tests or builds fail, query `dnk_query_error_solutions(error_text)` immediately. Once a bug is resolved, record the fix and root cause via `dnk_record_error_solution` to prevent recurrence.

## 9. One-Shot High-Fidelity Generation & Context Diet
Author complete, typed modules in a single pass. Avoid repetitive partial rewrites of the same file. Keep context windows lean by reading only targeted slices (80–120 lines) rather than dumping entire files.

## 10. Fail-Closed Security Gates & Secret Containment
Guard all critical actions and endpoints with `@security_gate`. Ensure secrets and API tokens are never written to source control or logged in cleartext. Always query secrets via `dnk_vault_get_secret`.

## 11. Thread-Safe TestClient Isolation in High-Concurrency Tests
When running multi-threaded load tests against FastAPI/Starlette backends, never share a single `TestClient` instance across threads. Allocate per-thread clients using `threading.local()` to prevent deadlocks.

## 12. Automated Quality Gate & Pre-Commit Verification
Never push or merge changes without confirming that `bash scripts/verify_all.sh` is 100% Green. Verify path hygiene, gitleaks secrets, docker compose configs, and complete regression test suites.

## 13. Two-Tier Development & Clean Distribution
Develop directly within the unified root (`apps/`, `core/`, `services/`). Release standalone client packages exclusively via `scripts/export_standalone_app.py` per `TWO_TIER_DEVELOPMENT_PROTOCOL.md`.

## 14. Epistemic Status & Grounded Citations
When generating AI responses or documentation summaries, always track epistemic status (`OBSERVED`, `INFERRED`, `HYPOTHESIS`). Anchor claims to concrete source files, line numbers, and evidence artifacts.

## 15. Post-Task Knowledge Harvesting to Obsidian
Upon completing significant features or architecture decisions, proactively document the rationale and tradeoffs in the Obsidian Vault (`./docs/notes/` or `vault:<note.md>`) with rich wikilinks for perpetual team recall.
