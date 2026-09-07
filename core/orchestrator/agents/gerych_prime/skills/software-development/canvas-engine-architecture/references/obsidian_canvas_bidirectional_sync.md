# Obsidian Canvas & Markdown Two-Way Synchronization (Task Forest v1.2)

## Overview
Protocol and patterns for bidirectional synchronization between React Flow / JSON Canvas v1.0 and Obsidian Vaults (Markdown notes + `.canvas` graphs).

## Core Backend Contracts (`core/obsidian/`)

### 1. Export Pipeline (`export_canvas.py`)
- **JSON Canvas Specification v1.0**: Canvas graphs are exported as `.canvas` JSON files with `nodes` and `edges`.
- **Markdown Notes with YAML Frontmatter**: Each card/node is also exported as an individual Markdown file containing frontmatter metadata:
  ```markdown
  ---
  id: node-1
  title: Launch Architecture
  type: task
  status: in_progress
  tags: [architecture, phase-11]
  updated_at: 2026-09-04T12:00:00Z
  source_canvas: mindmap.canvas
  ---
  ```
- **Function Signatures**:
  - `export_canvas_bundle(nodes, edges, output_dir, canvas_name="mindmap") -> {"canvas_path": str, "markdown_files": List[str]}`
    - *Pitfall Alert*: Keyword argument is `output_dir`, not `export_dir`.
  - `export_node_to_markdown(node, output_dir, filename=None) -> str`
    - Defaults to sanitized node ID: `{_sanitize_filename(node_id)}.md`.

### 2. Import & Conflict Resolution Pipeline (`import_canvas.py`)
- **Canvas Parsing**:
  - `parse_canvas_file(file_path) -> {"nodes": list, "edges": list}`
    - *Pitfall Alert*: Returns a dictionary `{"nodes": ..., "edges": ...}`, NOT a tuple `(nodes, edges)`.
  - Nodes parse title and description from Markdown content into `node["data"]["title"]` and `node["data"]["description"]`.
- **Bidirectional Merge & Conflict Resolution**:
  - `resolve_conflicts(existing_nodes, incoming_nodes, strategy="last_write_wins") -> (merged_nodes, conflicts)`
  - Strategy `"last_write_wins"` compares ISO timestamps / file modification times (`mtime`) and merges non-conflicting tags/metadata.
  - `import_canvas_and_markdown(canvas_file, markdown_dir) -> (nodes, edges)`
    - Fuses spatial positions (`x, y, width, height`) from `.canvas` with deep frontmatter (`status`, `tags`, `metrics`) from `.md`.

## Real-Time Collaboration & Frontend State

### 1. WebSocket Protocol (`canvas_v3_ws.py`)
- `OBSIDIAN_SYNC_REQUEST`: Triggers server-side export or import bundle task.
- `OBSIDIAN_SYNC_STATUS`: Broadcasts real-time progress payload:
  `{"status": "syncing" | "success" | "conflict" | "error", "message": "...", "files_synced": 5}`

### 2. UI Bar (`ObsidianSyncBar.tsx`) & Zustand Store (`canvasStore.ts`)
- Mounted as an absolute high-z-index floating widget over `CanvasEngine.tsx`.
- State managed in `canvasStore.ts`:
  - `obsidianSyncStatus: 'idle' | 'syncing' | 'success' | 'conflict' | 'error'`
  - `obsidianSyncMessage: string | null`
  - `syncToObsidian: (options: { vaultPath?: string; canvasName?: string; mode?: 'export' | 'import' | 'two-way' }) => Promise<void>`

## 🏛️ 3. Vault Archival & Master Index Protocol

When archiving architectural decisions and sync protocols to the user's Obsidian Vault:
1. **Target Vault Path**: `~/Documents/DNK_HUB My Notes/DNK_HUB My Notes`
2. **Naming Convention**: 3-digit numbered prefix followed by descriptive title (e.g., `007 Obsidian Vault Bidirectional Canvas Sync Protocol.md`).
3. **Document Invariants**:
   - YAML frontmatter with `title`, `date`, `version`, `tags`, and `status`.
   - Mandatory DNK-MRH-HEADER comment block.
   - Rich internal `[[wikilinks]]` pointing to parent/sibling notes (e.g., `[[000 DNK HUB Index]]`, `[[005 Task Forest Spatial HQ]]`).
4. **Master Index Update**:
   - Immediately update `000 DNK HUB Index.md` under the canonical documentation index table.
   - Maintain chronological ordering and correct status indicators (`Completed`, `Active`).

## 🧪 4. Headless Verification & Virtualenv Testing Invariants

1. **Virtualenv Invariant**:
   - Never run bare `pytest` in the terminal when verifying canvas or obsidian sync modules.
   - Always invoke the project virtual environment runner: `.venv/bin/pytest tests/core/test_obsidian_export_import.py tests/canvas/test_obsidian_sync.py -v`.
2. **Root CWD Invariant**:
   - Canvas verification suites rely on relative imports rooted at `$HUB_ROOT`.
   - If the shell CWD is in a subfolder (e.g. `core/hermes_agent`), navigate to repository root (`cd ../..`) before running test suites or script generators.

---

## 📐 5. Community Grid Enclosing Layout Pattern (Graphify SOTA Assimilation)

When exporting multi-cluster TaskDNA DAGs or code symbol graphs to `.canvas`, use deterministic community grid layout math instead of arbitrary placement:

### A. Mathematical Formulation
1. **Grid Bounding**:
   - Given $N$ clusters/communities (e.g., from Leiden, Louvain, or module domain grouping):
     $$\text{cols} = \lceil\sqrt{N}\rceil, \quad \text{rows} = \lceil N / \text{cols}\rceil$$
2. **Community Group Box Calculation**:
   - For community $C_k$ with $M_k$ nodes, calculate internal sub-grid:
     $$\text{sub\_cols} = \min(4, \lceil\sqrt{M_k}\rceil), \quad \text{sub\_rows} = \lceil M_k / \text{sub\_cols}\rceil$$
   - Width & Height of enclosing frame:
     $$W_k = \text{sub\_cols} \times (\text{card\_w} + \text{gap\_x}) + 2 \times \text{padding}$$
     $$H_k = \text{sub\_rows} \times (\text{card\_h} + \text{gap\_y}) + 2 \times \text{padding} + \text{header\_height}$$
3. **Canvas Palette Binding**:
   - Cycle enclosing frame colors: `CANVAS_COLORS = ["1", "2", "3", "4", "5", "6"]` (Obsidian Canvas group color tokens).

### B. Standard `.canvas` Enclosing Group Node
```json
{
  "id": "group_core_engine",
  "type": "group",
  "label": "Core Engine (Leiden Cluster 1)",
  "x": 0,
  "y": 0,
  "width": 1080,
  "height": 720,
  "color": "4"
}
```
Internal node cards place relative to group bounds:
`node_x = group_x + padding + (col_idx * (card_w + gap_x))`
`node_y = group_y + padding + header_height + (row_idx * (card_h + gap_y))`

