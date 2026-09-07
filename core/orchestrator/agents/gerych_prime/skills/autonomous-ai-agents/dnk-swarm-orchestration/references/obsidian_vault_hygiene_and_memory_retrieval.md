# 🏛️ Obsidian Vault Architecture, Tier 4 Memory Retrieval & Task Forest Hygiene

## 1. Context & Architectural Role of `docs/notes`
`./docs/notes` serves as the canonical in-repo Obsidian Knowledge Vault and **Tier 4 Long-Term Memory** for DNK OS.
- Integrates with `core/memory/unified_memory_broker.py` for sub-30ms cognitive retrieval.
- Bridges human visual exploration (Obsidian graph view, `.canvas` boards) with autonomous AI agent task execution (`TaskForestNode`, `TaskDNA`).
- Hosts 40+ canonical architectural blueprints, 170+ task forest nodes (`tasks_and_ideas/`), and formal Architecture Decision Records (`02_Architecture/`).

---

## 2. Invariant: Recursive Vault Retrieval in `UnifiedMemoryBroker`
### Pitfall:
Using flat globbing like `vault_path.glob("*.md")` only scans top-level root notes (`000 DNK HUB Index.md`, `001...`). It silently misses:
- All task and idea nodes in `docs/notes/tasks_and_ideas/*.md` (170+ files).
- All formal architecture decision records in `docs/notes/02_Architecture/*.md`.

Conversely, an unconstrained `rglob("*.md")` sweeps in archived files, deleted trash, Git metadata, and ephemeral test scratchpads, causing cognitive pollution and corrupting `tier_4_obsidian_notes` metrics.

### Standard:
Any tool, broker, or agent querying `docs/notes` MUST use recursive traversal paired with a strict exclusion filter:
```python
# In UnifiedMemoryBroker._query_obsidian_vault:
EXCLUDED_DIRS = {"archive", "trash", ".trash", ".obsidian", ".git", ".venv", "__pycache__"}

all_md_files = [
    p for p in self.vault_path.rglob("*.md")
    if not any(part in EXCLUDED_DIRS for part in p.parts)
    and not p.name.startswith("test-")
    and not p.name.endswith(".tmp")
]
```
Metadata must always return `relative_path` relative to `DNK_HUB` root, preserving portability and avoiding hardcoded paths.

---

## 3. Invariant: Task Forest Test Isolation & Anti-Pollution
### Pitfall:
Running automated tests for task decomposition (e.g. `dnk_decompose_task_dna` test suites) without explicit target directory isolation can cause test fixtures (e.g., `task-test-epic-to-decompose-01-spec-*`, `ws_test_node_alpha`) to be written directly into `docs/notes/tasks_and_ideas/`.
This pollutes the production task registry, corrupts completion percentage calculations (e.g. in `000_DNK_TASK_AND_IDEAS_INDEX.md`), and inflates the vault.

### Standard:
1. Automated tests must write generated test nodes to `tests/fixtures/` or an ephemeral `pytest` `tmp_path`.
2. Periodic vault audits must prune orphaned test nodes using:
   ```bash
   find docs/notes/tasks_and_ideas -name "*test*" -delete
   ```
   followed by re-syncing `000_DNK_TASK_AND_IDEAS_INDEX.md`.

---

## 4. Invariant: Obsidian MRH Header Hygiene
### Pitfall:
Writing Machine-Readable Headers (MRH) in markdown notes using the comment-style heading `# --- DNK-MRH-HEADER ---` causes Obsidian to render an oversized, jarring `H1` title at the top of every note in Reading and Editing views.

### Standard:
Always place standard YAML frontmatter on Line 1, immediately followed by a muted HTML comment block:
```markdown
---
title: "046 Note Title"
tags: [dnk-hub, architecture]
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/046_note_title.md"
purpose: "Canonical note purpose"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "YYYY-MM-DD"
author: "DNK-e.com Maksym"
--- END DNK-MRH-HEADER -->
```
This ensures zero visual noise in Obsidian while preserving 100% machine-readable AST metadata for agents.

---

## 5. Visual Graph Styling & Color Taxonomy (`.obsidian/graph.json`)
To maximize visual clarity in Obsidian's interactive Graph View, define explicit color groups in `graph.json` matching the system taxonomy:
- `#moc` / `#index`: Purple (`#8B5CF6`) - Navigation Hubs
- `#architecture` / `#blueprint`: Blue (`#3B82F6`) - Core Architecture
- `#task` / `#dnk-task`: Green (`#10B981`) - Executable Tasks
- `#idea` / `#backlog`: Amber (`#F59E0B`) - Ideas & Proposals
- `#gate` / `#quality-gate`: Red (`#EF4444`) - Hard Quality Gates

---

## 6. Invariant: Note Prefix & Slot Collision Invariant
### Pitfall:
Multiple notes sharing numeric prefixes (e.g. 8 notes with prefix `014`) cause ambiguous Wikilink resolutions (`[[014...]]`), broken Map of Content indexes, and fragmented graph traversals.

### Standard:
1. Enforce unique numeric slots in `docs/notes/`:
   - `000`–`099`: Root System Blueprints, Architectural Standards, and Major Milestones.
   - `02_Architecture/ADR_XXXX`: Formal Architecture Decision Records.
   - `tasks_and_ideas/`: `idea-*`, `epic-*`, `task-*`, `gate-*`.
2. Before publishing a new architectural note:
   - Check available number slots in `docs/notes/000 DNK HUB Index.md`.
   - Never duplicate an existing prefix. If collisions are detected (e.g. `014-Spam`), reassign legacy notes to unoccupied sequential slots (e.g. `024`–`034`) and immediately update backlink references in the MOC.
3. Automated Deduplication & Atomic Wikilink Migration:
   - Move colliding notes with `git mv "docs/notes/014 Old Name.md" "docs/notes/024 New Name.md"`.
   - Use `search_files` to locate all occurrences of `[[014 Old Name` across `docs/notes/`.
   - Patch each referring document using exact replace (`[[024 New Name|Alias]]` or `[[024 New Name]]`).
   - Register the reassigned block in `docs/notes/000 DNK HUB Index.md` under its respective thematic heading.

---

## 7. Protocol: Session Forensic Audit & Swarm Backlog Synthesis
When requested to conduct a forensic audit of an earlier session (`session_id`), follow the 4-step reconciliation loop:
1. **Retrieve History**: Run `session_search(session_id=...)` to extract historical dialogues, technical decisions, and identified system bottlenecks.
2. **Delta Reconciliation**: Compare historical findings against current `git log` and repository state (`git status`, file trees). Determine what was already implemented in subsequent commits versus what remains open.
3. **Artifact Archival**: Proactively record the audit results in an Obsidian note (`docs/notes/0XX_<slug>.md`) with YAML frontmatter, muted `DNK-MRH-HEADER` comment block, and link it in `docs/notes/000 DNK HUB Index.md`.
4. **Swarm Role-Isolated Backlog**: Decompose remaining action items into specific domain worker assignments (`dnk_dev_fullstack`, `herich_librarian`, `gerych_auditor`, `dnk_analytics`, `dnk_marketing_cmo`) specifying target files and clear acceptance criteria.

---

## 8. Invariant: Sequential Execution & Multi-Branch Non-Interference Protocol
### User Invariant:
*"реалізовуй всі по черзі, щоб напрацювання в інших гілках не зіпсувалися"* (Execute all items sequentially so progress in parallel branches is never corrupted).

### Standards:
1. **Branch Isolation**: Never attempt cross-branch merges or pushes to `main` / `staging` without explicit approval. All commits must live strictly in the isolated tracking feature branch (e.g. `feature/dnk-studio-arch-001`).
2. **Explicit Remote Push**: Always specify the exact remote and branch:
   ```bash
   git push dnk-mvp <feature-branch>
   ```
   Never run bare `git push` when multiple remotes (`origin`, `dnk-mvp`) exist.
3. **Vault Test Fixture .gitignore Shield**:
   Tests creating dynamic nodes in `docs/notes/tasks_and_ideas/` (e.g. `test-batch-*`, `test-ecom-*`, `task-selfheal-*`) must be ignored via `.gitignore`:
   ```gitignore
   docs/notes/tasks_and_ideas/*test*
   docs/notes/tasks_and_ideas/task-selfheal-*
   ```
   This prevents test runs from dirtying the git working tree or blocking commits in parallel developer branches.
4. **Automated Vault Quality Gate**:
   Always run `tests/verification/test_obsidian_vault_hygiene.py` before committing to ensure:
   - Zero absolute paths (`/Users/...`).
   - Clean YAML frontmatter on 100% of root notes.
   - Broker retrieval latency < 50ms across all recursive notes under memory cache.

---

## 9. SCONES Zero-Click Expectation Middleware & Path Invariant
To prevent corrupted or absolute-path cognitive memories from entering Tier 1–4 storage:
1. **Validation Rules**:
   - `importance` must be within `(0.0, 1.0]`.
   - `topic` and `content` must NOT contain `/Users/` or hardcoded absolute OS paths.
2. **Automated Test Suite**:
   Run `pytest tests/core/test_scones_middleware_hook.py` to verify the fail-closed expectation gate and automatic sanitization before storing long-term memory.
