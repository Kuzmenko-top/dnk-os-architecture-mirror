# Obsidian Canvas & Task Forest Bidirectional Sync Protocol (v1.4)

## Purpose & Overview
Integrates Task Forest hierarchical DAGs and Spatial Canvas nodes with Obsidian JSON Canvas (`.canvas`) and Markdown note vaults. Enables two-way synchronization:
1. **Export**: Converts Task Forest / Canvas nodes & directed edges into a standard Obsidian JSON Canvas v1.0 file and decomposes text/task nodes into discrete Markdown notes.
2. **Import**: Parses Obsidian `.canvas` files and Markdown vaults into Canvas nodes and dependency edges.
3. **Hardened Canonical Paths**: Enforces strict path validation restricting synchronization targets to the canonical Vault root to prevent path traversal.
4. **Deterministic LWW Conflict Resolution**: Arbitrates conflicts via a 3-tier deterministic tuple `(updated_at, revision, content_hash)`, preserving spatial canvas coordinates ($x, y, w, h$) upon updates.

---

## 1. Canonical Vault Paths & Path Traversal Shield

To ensure safe multi-tenant and multi-agent synchronization without allowing arbitrary filesystem writes:
- **Canonical Vault Root**: Retrieved via `get_canonical_vault_root()`. Evaluates `DNK_OBSIDIAN_VAULT_ROOT` or `OBSIDIAN_VAULT_ROOT` environment variables, defaulting to `~/Documents/DNK_HUB My Notes`.
- **Canonical Task Forest Dir**: `get_canonical_task_forest_dir()`, defaulting to `~/Documents/DNK_HUB My Notes/TaskForest`.
- **Traversal Defense (`validate_vault_path`)**:
  - Resolves target path and checks `resolved_path.is_relative_to(resolved_vault_root)`.
  - Rejects traversal attempts (`../`, `/etc`, outside directories) with `ValueError: Path traversal forbidden: target_dir '<path>' is outside canonical Vault root '<root>'`.
  - WebSocket requests (`OBSIDIAN_SYNC_REQUEST`) attempting traversal are immediately halted and return error status.

```python
def validate_vault_path(target_path: Union[str, Path], vault_root: Optional[Union[str, Path]] = None) -> Path:
    """
    Validate that target_path resolves strictly inside vault_root.
    Prevents path traversal attacks (e.g. ../../etc/passwd).
    """
    if vault_root is None:
        root_path = get_canonical_vault_root()
    else:
        root_path = Path(vault_root).expanduser().resolve()

    target = Path(target_path).expanduser()
    if not target.is_absolute():
        target = (root_path / target).resolve()
    else:
        target = target.resolve()

    try:
        target.relative_to(root_path)
    except ValueError as exc:
        raise ValueError(
            f"Path traversal forbidden: target path '{target_path}' resolves outside canonical Vault root '{root_path}'"
        ) from exc

    return target
```

---

## 2. Data Contract & JSON Canvas Mapping (v1.0 Spec)

### Node Mapping Specification
An Obsidian `.canvas` file contains arrays of `nodes` and `edges`:

| Task Forest / Canvas Attribute | Obsidian Canvas Node Key | Format / Type |
|--------------------------------|--------------------------|---------------|
| `id`                           | `id`                     | String ID     |
| `position.x`, `position.y`     | `x`, `y`                 | Integer / Float px |
| `width`, `height`              | `width`, `height`        | Integer / Float px |
| `type` (`task` / `text` / `file` / `group`) | `type`      | String enum (`text`, `file`, `link`, `group`) |
| `data.title` / `data.description` | `text` (or `file`)    | Markdown text |
| `data.color`                   | `color`                  | Preset "1"-"6" or hex |

### Edge Mapping Specification
Edges connect nodes with directional arrows representing task dependencies:
```json
{
  "id": "e1-2",
  "fromNode": "node-001",
  "fromSide": "right",
  "toNode": "node-002",
  "toSide": "left",
  "label": "enables",
  "color": "1"
}
```

---

## 3. Markdown Note Decomposition with YAML Frontmatter

When exporting nodes containing rich metadata to the vault:
- **Strict Frontmatter Placement**: YAML frontmatter MUST start on Line 1 (`---`). In Obsidian, if any comments, blank lines, or headers precede `---`, the frontmatter properties (`tags`, `status`, `type`) fail to parse and are rendered as raw text.
- Write notes with valid YAML frontmatter containing:
  - `id`: Unique node ID
  - `title`: Node/task title
  - `type`: Node type (`task`, `decision`, `milestone`, `text`, `agent`, `file`)
  - `status`: Task status (`pending`, `in_progress`, `completed`, `blocked`)
  - `priority`: Priority rank (`low`, `medium`, `high`, `critical`)
  - `revision`: Integer revision counter (starts at 1)
  - `content_hash`: Deterministic SHA-256 hash digest of node title + description
  - `tags`: Category tags for Dataview and search
  - `updated_at`: UNIX timestamp float
  - `source_canvas`: Relative filename of parent `.canvas`
- **DNK-MRH Header Coexistence**: Per `DNK-STD-0075`, Markdown files require a DNK-MRH header. To prevent breaking Obsidian's frontmatter, format the MRH header as an HTML comment block placed immediately AFTER the closing frontmatter delimiter `---`:
  ```markdown
  ---
  id: "node-001"
  title: "Core API Architecture"
  type: "task"
  status: "in_progress"
  tags: [dnk-task-forest, architecture]
  ---
  <!-- --- DNK-MRH-HEADER ---
  # mrh_id: "docs/notes/task_forest/node-001.md"
  # purpose: "Task node note for core API architecture"
  # canonical_source: false
  # status: "Active"
  # --- END DNK-MRH-HEADER --- -->

  # Core API Architecture
  ...
  ```
- **Bidirectional [[wikilinks]] Navigation**: Transform inter-node and dependency references into `[[Target Node Title]]` wikilinks. This populates Obsidian's interactive graph view edges and enables `core.obsidian.task_forest_sync.ObsidianTaskForestSync` to accurately extract parent-child dependency edges during vault imports.

### Content Hash Calculation
```python
import hashlib

def compute_node_content_hash(title: str, text: str) -> str:
    raw = f"{title.strip()}\n{text.strip()}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
```

### Bundle Structure Layout
```
TaskForest/
├── phase-11-mindmap.canvas          # Interactive Obsidian Canvas
├── node-001.md                     # Discrete note for node-001
├── node-002.md                     # Discrete note for node-002
└── ...
```

---

## 4. Deterministic 3-Tier Last-Write-Wins (LWW) Tie-Breaker

Arbitrates conflicts between Canvas runtime and Obsidian Vault markdown files using a strict deterministic priority tuple:
$$\text{key} = (\text{updated\_at}, \text{revision}, \text{content\_hash})$$

- **Tier 1 (Timestamp)**: Higher `updated_at` wins.
- **Tier 2 (Revision)**: If timestamps match, higher `revision` wins.
- **Tier 3 (Content Hash)**: If timestamps and revisions match, lexicographically larger SHA-256 `content_hash` breaks the tie deterministically.
- **Spatial Topology Preservation**: If Markdown wins, spatial position ($x, y, w, h$) from Canvas is preserved intact. If Canvas wins, tags and metadata are merged.

```python
def resolve_conflicts(canvas_nodes: list[dict], md_nodes: list[dict], strategy: str = "last-write-wins") -> list[dict]:
    """
    Arbitrates conflicts between Canvas runtime and Obsidian Vault files.
    Preserves spatial layout while syncing latest content and metadata with a
    deterministic (updated_at, revision, content_hash) tie-breaker.
    """
    md_map = {m["id"]: m for m in md_nodes}
    merged = []

    for c_node in canvas_nodes:
        nid = c_node["id"]
        if nid not in md_map:
            merged.append(c_node)
            continue

        m_node = md_map[nid]
        c_data = c_node.get("data", {})
        m_data = m_node.get("data", {})

        c_ts = float(c_data.get("updated_at", 0) or 0)
        m_ts = float(m_data.get("updated_at", 0) or 0)
        c_rev = int(c_data.get("revision", 1) or 1)
        m_rev = int(m_data.get("revision", 1) or 1)
        c_hash = str(c_data.get("content_hash", ""))
        m_hash = str(m_data.get("content_hash", ""))

        c_key = (c_ts, c_rev, c_hash)
        m_key = (m_ts, m_rev, m_hash)

        if m_key >= c_key:
            # Markdown wins or ties -> update content & metadata, preserve canvas coordinates
            merged_node = {
                **c_node,
                "data": {
                    **c_data,
                    **m_data,
                    "tags": list(dict.fromkeys(c_data.get("tags", []) + m_data.get("tags", []))),
                    "updated_at": max(m_ts, c_ts),
                    "revision": max(m_rev, c_rev),
                    "content_hash": m_hash or c_hash,
                }
            }
        else:
            # Canvas wins -> keep canvas data, merge markdown tags
            merged_node = {
                **c_node,
                "data": {
                    **c_data,
                    "tags": list(dict.fromkeys(c_data.get("tags", []) + m_data.get("tags", []))),
                    "updated_at": c_ts,
                    "revision": c_rev,
                    "content_hash": c_hash,
                }
            }
        merged.append(merged_node)
    return merged
```

---

## 5. WebSocket RPC Event Flow (`apps/api/routers/canvas_v3_ws.py`)

Real-time bidirectional synchronization over WebSocket:

### 1. Client Request (`OBSIDIAN_SYNC_REQUEST`)
```json
{
  "type": "OBSIDIAN_SYNC_REQUEST",
  "direction": "export",
  "canvas_id": "phase-11-mindmap",
  "canvas_name": "phase-11-mindmap",
  "target_dir": "TaskForest",
  "export_individual_md": true,
  "link_as_file_nodes": false,
  "conflict_strategy": "last-write-wins",
  "nodes": [...],
  "edges": [...]
}
```

### 2. Server Broadcast Success (`OBSIDIAN_SYNC_STATUS`)
```json
{
  "type": "OBSIDIAN_SYNC_STATUS",
  "event": "OBSIDIAN_SYNC_STATUS",
  "status": "success",
  "canvas_id": "phase-11-mindmap",
  "direction": "export",
  "result": {
    "canvas_path": "/Users/kuzmenko.top/Documents/DNK_HUB My Notes/TaskForest/phase-11-mindmap.canvas",
    "markdown_files": [".../node-001.md"],
    "node_count": 5,
    "edge_count": 4
  },
  "nodes": [...],
  "edges": [...],
  "timestamp": 1725478205.12
}
```

### 3. Server Broadcast Error on Path Traversal or Validation Failure
```json
{
  "type": "OBSIDIAN_SYNC_STATUS",
  "event": "OBSIDIAN_SYNC_STATUS",
  "status": "error",
  "canvas_id": "phase-11-mindmap",
  "direction": "export",
  "error": "Path traversal forbidden: target path '../../etc' resolves outside canonical Vault root '/Users/kuzmenko.top/Documents/DNK_HUB My Notes'",
  "nodes": [],
  "edges": [],
  "timestamp": 1725478210.45
}
```

---

## 6. In-Repo ADR Canonicalization & Bidirectional Vault Synchronization (`scripts/system/obsidian_vault_sync.py`)

### Problem Statement & Invariant
- **Risk**: Storing ADRs or system notes via symlink to an external folder causes notes to leak outside Git tracking, creating a divergence between repository history and local knowledge.
- **Rule**: `docs/notes/` in the repository root is the Single Source of Truth (SSOT) and MUST be a physical directory tracked by Git.
- **Gitignore Hygiene**: `.gitignore` MUST track `docs/notes/*.md` while excluding local Obsidian metadata (`docs/notes/.obsidian/` and `.DS_Store`).

### Bidirectional Vault Sync Engine
To maintain real-time parity between the in-repo SSOT and the local Obsidian app (`~/Documents/DNK_HUB My Notes/DNK_HUB My Notes`), use `scripts/system/obsidian_vault_sync.py`:

```bash
# Bidirectional sync (newest file wins based on mtime and sha256)
./.venv/bin/python3 scripts/system/obsidian_vault_sync.py

# Force export from repository to Obsidian Vault
./.venv/bin/python3 scripts/system/obsidian_vault_sync.py --direction to-vault

# Force import from Obsidian Vault to repository
./.venv/bin/python3 scripts/system/obsidian_vault_sync.py --direction to-repo

# Dry run audit without modifying files
./.venv/bin/python3 scripts/system/obsidian_vault_sync.py --dry-run
```

### Pre-Commit & Hygiene Gate
Before committing, always ensure no untracked notes or tests drift via:
```bash
./.venv/bin/python3 scripts/system/git_hygiene_guard.py
```

---

## 7. Native Zero-Copy SSOT Detection (`obsidian.json`)

When the desktop Obsidian application opens `docs/notes/` directly as an in-repo vault:
- `scripts/system/obsidian_vault_sync.py` inspects `~/Library/Application Support/obsidian/obsidian.json`.
- If an active vault path points directly to `docs/notes/` (or its absolute resolution), the synchronizer enters **Zero-Copy SSOT Mode**.
- No file copying or duplicate storage is performed; changes made in git or by swarm agents are immediately live and native in the desktop Obsidian app.

---

## 8. Subfolder Taxonomy & Autonomous DAG Metric Calculation

### Structured Task Forest Layout
All task and idea nodes under `docs/notes/tasks_and_ideas/` must be partitioned into categorized subfolders:
- `epics/`: High-level strategic umbrellas and major milestones.
- `tasks/`: Executable atomic units of work (`task-XXX`).
- `ideas/`: Concept proposals, RFCs, and exploratory blueprints.
- `gates/`: Quality, security, and verification checkpoints.
- `archive/`: Deprecated or completed historical items.
- Root contains ONLY `000_DNK_TASK_AND_IDEAS_INDEX.md` (MOC).

### Automated Metric Calculator
Run the DAG calculator to refresh graph telemetry, blocker counts, and completion percentages in the master MOC:
```bash
./.venv/bin/python3 scripts/system/update_task_forest_metrics.py
```

### Vault Hygiene Test Gate
Enforced via `tests/verification/test_obsidian_vault_hygiene.py`:
- `test_tasks_and_ideas_subfolder_hygiene`: Rejects any unorganized `.md` file directly in `tasks_and_ideas/`.
- `test_note_numbers_unique_in_root`: Ensures no collision in note numbering prefixes.
- `test_no_cyrillic_note_titles`: Strictly forbids Cyrillic filenames in the knowledge base.


