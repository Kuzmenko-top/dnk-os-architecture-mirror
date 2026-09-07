# --- DNK-MRH-HEADER ---
# mrh_id: "docs/user-guides/FAQ.md"
# purpose: "Frequently Asked Questions (FAQ) with 20+ comprehensive answers for DNK OS users."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# DNK OS Frequently Asked Questions (FAQ)

Find answers to common questions about DNK OS architecture, swarm orchestration, canvas operations, security, and developer workflows.

---

### 1. What is DNK OS?
DNK OS is an autonomous multi-agent operating system designed for high-velocity software engineering, automated e-commerce operations, and spatial canvas orchestration.

### 2. Who is Gerych Prime?
Gerych Prime is the autonomous Chief Builder, Swarm Manager, and Master of Knowledge Assimilation running on Hermes Agent within DNK OS.

### 3. How does the 14-Agent Swarm operate?
The swarm partitions specialized responsibilities across 14 autonomous workers, such as `gerych_builder` (UI/Canvas), `dnk_dev_fullstack` (APIs), `dnk_shopify` (Ecom), and `gerych_auditor` (Security & Testing).

### 4. What is the Step 0 Autonomous Triage Protocol?
Before modifying files, the agent runs `dnk_triage_task(prompt)` to compute task complexity (C = F_files + 2*D_domains + 3*S_stages) and pick execution mode (`SOLO`, `SWARM_PARALLEL`, or `SWARM_SEQUENTIAL`).

### 5. What is Mandatory Atomic Slice Execution (MASE)?
MASE enforces that tasks are executed in bounded slices of ≤ 25 tool calls per turn to eliminate token exhaustion and context degradation.

### 6. Why is relative path hygiene mandatory?
Relative paths (`./`, `../`) guarantee that code and tests run identically across macOS local workstations, Linux Docker containers, and CI/CD runners without machine-specific dependencies.

### 7. What are Machine-Readable Headers (MRH)?
MRH is a standardized comment block (`# --- DNK-MRH-HEADER ---`) defining `mrh_id`, `purpose`, `version`, and dependencies, enabling automated AST indexing across the repository.

### 8. How does SCONES cognitive memory work?
SCONES provides persistent episodic and semantic memory storage across workspaces (`ws-alpha-001`), allowing agents to recall verified architectural rules and patterns.

### 9. What is Error Distillation?
Error Distillation queries known fixes for error traces (`dnk_query_error_solutions`) and saves newly discovered resolutions (`dnk_record_error_solution`) to create a self-healing knowledge loop.

### 10. How does Canvas Engine handle concurrent mutations?
The Canvas Engine uses Optimistic Concurrency Control (OCC) with 3-way structural graph merging to reconcile multi-client node movements and edits.

### 11. What is the Two-Tier Development Protocol?
Development occurs in the unified root repo. Standalone release distributions are packaged into `DNKOS_APP` via `scripts/export_standalone_app.py` with zero rsync collisions.

### 12. How are secrets and API credentials secured?
Secrets are encrypted and managed in workspace-isolated vaults accessed via `dnk_vault_get_secret`. Secrets are never committed or printed in logs.

### 13. What is the Master Quality Gate?
`bash scripts/verify_all.sh` executes preflight hygiene, relative path checks, adversarial security audits, gitleaks scans, pip-audit, docker compose checks, and full regression tests.

### 14. What is Epistemic Status in evidence generation?
Epistemic status classifies AI statements into `OBSERVED` (direct empirical measurement), `INFERRED` (deductive conclusion from facts), or `HYPOTHESIS` (unverified assumption).

### 15. How does the Web Audio feedback in Onboarding work?
The tutorial feedback system synthesizes chimes and error tones using browser-native Web Audio API `AudioContext`, requiring zero external audio assets.

### 16. How do I track workspace token spending and costs?
Use `dnk_get_workspace_spending(workspace_id)` or call `GET /api/v1/workspaces/{id}/spending` to inspect token counts, USD expenditures, and runtime durations.

### 17. How does the Shopify AST Engine validate themes?
The Liquid parser analyzes Shopify template tokens, validates schema JSON integrity, verifies tag pairing (`{% if %}` ... `{% endif %}`), and checks schema settings.

### 18. What video aspect ratios are supported by Video Studio?
Video Studio supports `story_9_16` (vertical reels/shorts), `landscape_16_9` (standard video/YouTube), and `square_1_1` (feed posts).

### 19. How do I sync canvas diagrams with Obsidian?
Use `core/obsidian/export_canvas.py` and `import_canvas.py` to seamlessly convert between DNK Canvas graph JSON and standard Obsidian `.canvas` files.

### 20. How do I resolve code definitions quickly?
Call `dnk_resolve_symbol(symbol="<name>")` to instantly find class, function, or type locations in <20ms without performing manual searches.

### 21. What should I do if a verification test fails?
Inspect the pytest traceback, query `dnk_query_error_solutions` for known remedies, apply the fix to the root cause, and re-run `bash scripts/verify_all.sh`.
