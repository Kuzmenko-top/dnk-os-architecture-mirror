---
name: obsidian-vault-hygiene
description: "Use when checking Obsidian vault hygiene and link gates."
version: 1.0.0
author: Gerych Prime & DNK OS
license: MIT
metadata:
  hermes:
    tags: [obsidian, vault, markdown, hygiene, frontmatter, dead-links, quality-gate, cognitive-memory]
    related_skills: [obsidian, architecture-invariants-and-blast-radius, test-driven-development]
---

# Obsidian Vault Hygiene & Automated Quality Gates

Maintain markdown vaults as high-integrity long-term cognitive memory (Tier 4) and human-in-the-loop visual command centers. Enforces path hygiene, dual-header validity, dynamic numeric indexing, dead-link prevention, and automated CI test gates.

## When to Use

- When creating, re-indexing, or maintaining markdown notes in an Obsidian vault (e.g. `docs/notes/`).
- When setting up automated tests to prevent dead relative links and malformed YAML frontmatter.
- When generating automated audit, research, or assimilation notes with numeric prefixes without colliding with existing notes.
- When organizing knowledge graphs, task forest nodes (`tasks_and_ideas/`), or architecture decision records (ADRs).

## Core Principles

1. **Strict Relative Paths Only**:
   - Never use absolute paths (`/Users/...`, `~/Documents/...`) in notes, scripts, or tool arguments.
   - Always reference the vault via relative paths (e.g. `./docs/notes/`) or symlinks.
2. **Dual-Header Architecture**:
   - Notes must start with clean YAML frontmatter delimited by `---`.
   - Hidden Machine-Readable Headers (MRH) must follow YAML frontmatter inside HTML comments `<!-- --- DNK-MRH-HEADER --- -->`.
   - **Crucial**: Never place `# --- DNK-MRH-HEADER ---` before YAML frontmatter, as it breaks H1 markdown rendering in Obsidian.
3. **Dynamic Prefix Allocation (Zero Collisions)**:
   - When programmatically creating notes with 3-digit prefixes (`001_...`), never hardcode prefix numbers.
   - Dynamically inspect existing files, calculate `max(existing_prefixes) + 1`, and allocate sequentially.

## Step 1 — Validate YAML Frontmatter

Every root note must contain valid YAML frontmatter with mandatory metadata:

```python
import re
import yaml
from pathlib import Path

vault_path = Path("docs/notes")
for md_file in vault_path.glob("*.md"):
    if md_file.name.startswith("."):
        continue
    content = md_file.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", content.strip(), re.DOTALL)
    assert m, f"{md_file.name}: Missing YAML frontmatter"
    
    data = yaml.safe_load(m.group(1))
    assert isinstance(data, dict), f"{md_file.name}: Frontmatter must be a dict"
    assert data.get("title"), f"{md_file.name}: Missing 'title'"
    assert data.get("tags"), f"{md_file.name}: Missing 'tags'"
```

## Step 2 — Enforce Unique Numeric Note Prefixes

Ensure all numbered notes maintain a strictly unique index:

```python
prefixes = {}
for md_file in vault_path.glob("*.md"):
    m = re.match(r"^(\d{3})[_\s]", md_file.name)
    if m:
        num = m.group(1)
        prefixes.setdefault(num, []).append(md_file.name)

duplicates = {k: v for k, v in prefixes.items() if len(v) > 1}
assert not duplicates, f"Duplicate note prefixes: {duplicates}"
```

To allocate the next available prefix dynamically:
```python
existing_nums = [
    int(m.group(1))
    for f in vault_path.glob("*.md")
    if (m := re.match(r"^(\d{3})[_\s]", f.name))
]
next_prefix = f"{max(existing_nums, default=0) + 1:03d}"
```

## Step 3 — Scan and Prevent Dead Links

Validate that markdown links `[label](target)` pointing to relative files exist on disk:

```python
link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
hub_root = Path(".").resolve()

broken_links = []
for md_file in vault_path.glob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    for label, target in link_pattern.findall(content):
        if any(target.startswith(p) for p in ("http://", "https://", "#", "mailto:")):
            continue
        clean_target = target.split("#")[0].split("?")[0].strip()
        if not clean_target:
            continue
        rel_to_note = md_file.parent / clean_target
        rel_to_root = hub_root / clean_target.lstrip("/")
        if not rel_to_note.exists() and not rel_to_root.exists():
            broken_links.append(f"{md_file.name} -> [{label}]({target})")

assert not broken_links, f"Dead links found: {broken_links}"
```

## Step 4 — Automated Pre-Commit / Test Gate

Integrate the checks into a permanent pytest module (e.g. `tests/verification/test_obsidian_vault_hygiene.py`):

```bash
./.venv/bin/pytest tests/verification/test_obsidian_vault_hygiene.py -v
```

Include:
- `test_vault_notes_yaml_frontmatter_validity`: Validates frontmatter parsing and required fields.
- `test_vault_markdown_file_links_integrity`: Detects broken relative links.
- `test_vault_note_prefixes_unique`: Guarantees unique 3-digit identifiers.
- `test_tasks_and_ideas_subfolder_hygiene`: Confirms DAG nodes are organized into subdirectories (`epics`, `tasks`, `ideas`, `gates`).
- `test_task_forest_index_and_telemetry_sync`: Verifies Task Forest DAG metrics calculation (`completion_rate`, `avg_progress`, `epics_summary`, `blocked_nodes`) and validates index synchronization against disk via non-mutating `--verify` mode.

## Pitfalls to Avoid

- **Task Node Exporters Dumping to Vault Root**: Exporters (such as `services/dnk_node_tasks/persistence.py`) must never write `.md` node files directly into `docs/notes/tasks_and_ideas/` root. Nodes must be partitioned into typed subdirectories (`epics/`, `tasks/`, `ideas/`, `gates/`) so they don't break subfolder hygiene gates or leave orphaned files.
- **Index Generators Mutating During CI/Tests**: Always provide a non-destructive verification mode (e.g. `scripts/system/update_task_forest_metrics.py --verify`). Tests must verify index synchronization and exit with code 1 if out-of-sync without silently rewriting production files during test runs.
- **Hardcoded Note Prefixes in Automation Tools**: Avoid static strings like `f"016_{name}.md"` in generators; scan the directory dynamically to avoid overwriting or colliding with canonical notes.
- **Placing Markdown Text Inside Frontmatter**: Putting prose or section headers between the opening and closing `---` delimiters breaks YAML parsers and corrupts Obsidian metadata.
- **Unsanitized Test Artifacts**: If a test suite generates test notes in the vault, always clean them up in a `finally` block or fixture teardown to prevent cluttering the production knowledge graph.
- **Absolute Path Leaks**: Never hardcode user home directories in wikilinks or note bodies; use workspace-relative references or sanitized placeholders (`/Users/<username>/...`) to prevent `test_path_hygiene.py` failures.
- **Prefix Collision in Ad-hoc Architectural Notes**: When manually or semi-automatically authoring new architectural notes, verify existing numbers first to prevent duplicate 3-digit prefixes (e.g. colliding with existing `074` or `075`), re-indexing to the next sequential identifier (e.g. `082`, `083`).
- **Subdirectory-Scoped vs Root Vault Numbering Collisions**: When creating modular domain subdirectories inside the vault (e.g. `docs/notes/marketing/`, `docs/notes/tasks_and_ideas/`), allow scoped indexing starting from `000_...` within the subfolder, but always maintain a canonical root gateway note (e.g. `086_commercial_marketing_assets_hub.md`) in `docs/notes/` so the root vault index remains strictly monotonic and globally discoverable without prefix collisions.
- **Embedded JSON Manifest Validation in Notes**: When authoring architectural or template notes containing code blocks (like Remotion or agent manifests), write unit tests (e.g. `test_marketing_assets_hygiene.py`) that extract and validate the embedded JSON blocks with `json.loads` to guarantee they never drift from production schemas.
- **Ephemeral Test Artifacts in Tasks/Ideas Folders**: Test suites invoking persistence routers (e.g. `test_node_tasks_router.py`) must isolate or cleanly purge created `.md` files in `docs/notes/tasks_and_ideas/` to ensure the git tree remains 100% clean for pre-commit gates.
