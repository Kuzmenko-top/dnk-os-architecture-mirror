# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/capcut/audits/results/differential_snapshots_analysis.md"
# purpose: "Analysis of CapCut Web Differential Snapshots, Memory Budgeting, and IndexedDB Sync."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime) & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

# ⚡ Differential Snapshots, Memory Budgeting & Storage Strategy

## 1. Differential State Architecture

CapCut Web uses a hybrid **Delta-Forward + Periodic Keyframe Snapshot** architecture:

```
[Full Base Snapshot S0] ──(+Δ1)──> [Δ1] ──(+Δ2)──> [Δ2] ... ──(+Δ10)──> [Full Keyframe Snapshot S1]
```

### 1.1 Snapshot Interval & Triggers
- **Periodic Cadence**: Full keyframe snapshot generated every **10 transactions** (`snapshot_interval: 10`).
- **Major Structural Triggers**: Force-generates a keyframe snapshot on:
  - Document resolution or aspect ratio change (`SET_DOCUMENT_PROPERTY`).
  - Template theme application / global style replacement.
  - Multi-node bulk deletion (`REMOVE_NODES_BY_FILTER`).

### 1.2 In-Memory Delta Format
Deltas are emitted via `_onChangeDiff` with strict operation flags:
- `actionOperateType: 1` (Undo delta)
- `actionOperateType: 2` (Redo delta)
- `diff`: RFC 6902-compliant JSON Patch operations (`op: replace | add | remove`, `path`, `value`, `oldValue`).

---

## 2. Memory Budget & Garbage Collection Strategy

| Metric | CapCut Web Setting | DNK OS Canvas Adaptation |
| :--- | :--- | :--- |
| **Max History Depth** | 100 Transactions | 100 Transactions (Ring Buffer) |
| **Max Memory Budget** | 500 MB heap allocated | 500 MB hard limit |
| **Blob Cache Eviction** | LRU via `updateTime` index | LRU IndexedDB + In-Memory WeakRef |
| **Auto-save Checkpoint** | 5 minutes (300,000 ms) | 5 minutes + Unload Beacon |
| **Dirty Write Buffer** | `lvweb-offline-data` (IndexedDB) | `dnk-canvas-offline-queue` (IndexedDB) |

---

## 3. Storage Hierarchy & IndexedDB Mapping

```
┌───────────────────────────────────────────────────────────┐
│                    RAM State (MobX / Konva)              │
│       Current Active Scene Graph (Live Objects)           │
└─────────────────────────────┬─────────────────────────────┘
                              │
                    Auto-Save & Commit (5m / unload)
                              ▼
┌───────────────────────────────────────────────────────────┐
│                  IndexedDB: graphic-local                 │
│  ├── graphic-local-user-draft     -> Full serialized JSON │
│  ├── graphic-local-user-draft-meta-> Size, thumb, title   │
│  └── user-materials               -> Local uploaded blobs │
└─────────────────────────────┬─────────────────────────────┘
                              │
                    Background Sync
                              ▼
┌───────────────────────────────────────────────────────────┐
│                 Remote Cloud API / S3                     │
└───────────────────────────────────────────────────────────┘
```
