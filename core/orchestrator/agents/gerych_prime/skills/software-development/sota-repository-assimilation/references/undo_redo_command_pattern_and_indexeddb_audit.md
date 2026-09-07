# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/undo_redo_command_pattern_and_indexeddb_audit.md"
# purpose: "Standard Reference for Auditing & Synthesizing Web Canvas Undo/Redo, Command Pattern & Multi-Store IndexedDB Engines."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Gerych"
# --- END DNK-MRH-HEADER ---

# ⏪ Undo/Redo Command Pattern & IndexedDB Persistence Audit Reference

## 🎯 Scope
Best-practice methodologies for reverse-engineering, analyzing, and synthesizing high-performance Undo/Redo engines, Command Patterns, and IndexedDB multi-store persistence layers from modern web-based visual/canvas tools (CapCut, Figma, Canva).

---

## 🏗️ 1. Core Architectural Pillars

### 1.1 Bidirectional Invertible Command Pattern
Every user action is encapsulated as an atomic `Command` holding forward (`redoCommand`) and inverse (`undoCommand`) mutations.
- **Instant Swap Inversion**: `command.reverse()` swaps forward/backward operations without re-computing the full scene graph.
- **Collaborative/OT Bridge**: Separate operational payload (`operateType`, `operateId`) from local execution logic to allow sync over WebSocket/CRDT.

### 1.2 Micro-Transaction Coalescing (`pushWithOperateId`)
To prevent history stack pollution during continuous user interactions (e.g. dragging an object, scrubbing sliders, typing text):
- Tag intra-action frames with a unique `operateId`.
- Successive commands sharing the same `operateId` are merged via `composeCommand(prev, next)` instead of creating new history frames.
- Terminal event (e.g., `mouseup`, `blur`) finalizes the single atomic transaction in the Undo stack.

### 1.3 Differential Snapshots (Hybrid Strategy)
- **Keyframe Interval**: Full scene-graph snapshot captured every $N$ transactions (typically $N=10$) or upon document boundary changes (canvas resize).
- **Differential Patches**: In-between transactions store RFC 6902 JSON Patch deltas (`op`, `path`, `value`, `old_value`).
- **Memory Budgeting**: Cap memory consumption (e.g., 500 MB) and stack depth (e.g., 100 entries) via FIFO ring-buffer eviction.

---

## 💾 2. Multi-Store IndexedDB Persistence Topology

When auditing client-side storage for rich web canvas applications, inspect and categorize object stores:

| Store Category | Purpose | Eviction / Flush Strategy |
| :--- | :--- | :--- |
| **`drafts` / `projects`** | Full document state, scene-graph tree, metadata. | Periodic auto-checkpoint (e.g. 5m) + `beforeunload`. |
| **`draft_history` / `offline`** | Dirty transaction journals, uncommitted undo deltas. | Flushed immediately on action for crash recovery. |
| **`asset_cache` / `materials`** | Local blob cache (images, custom fonts, audio waveforms). | LRU cache with quota monitoring. |
| **`user_preferences` / `session`** | UI layout, tool selection, canvas zoom/pan position. | Updated on UI state change. |

---

## 🔍 3. Headless Browser Audit & Deconstruction Playbook

1. **Extract Webpack/Vite Modules**:
   - Locate history/canvas support chunks (`initial-canvas-support`, `history-engine`, `editor-core`).
   - Query runtime registry for symbols like `UndoRedoStack`, `HistoryManager`, `TransactionManager`.
2. **IndexedDB Schema Dump**:
   - Use `indexedDB.databases()` and iterate object stores to capture database names, version, key paths, and index layouts.
3. **Pydantic v2 DTO Synthesis**:
   - Map discovered JavaScript object contracts to strict Python Pydantic v2 models (`Transaction`, `UndoRedoState`, `CommandPayload`, `DraftStorageRecord`).
