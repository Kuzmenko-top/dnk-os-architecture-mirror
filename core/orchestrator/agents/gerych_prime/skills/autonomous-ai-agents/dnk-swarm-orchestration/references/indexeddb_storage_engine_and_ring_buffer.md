# 💾 IndexedDB Storage Engine, Differential Snapshots & Crash Recovery Protocol

## 🎯 Architecture Overview

The DNK OS Canvas Engine persistence layer lives under `apps/web/src/canvas/storage/` and provides reliable local-first state storage for rich spatial interactive canvases.

### Key Components:
- **`schema.ts`**: Zod runtime validation schemas for `CanvasState`, `Transaction`, `DraftRecord`, `CanvasAsset`, `CanvasMeta`. Stores constants: `drafts`, `history`, `assets`, `meta` inside IndexedDB database `dnk_canvas_db` (v1).
- **`storage.service.ts` (`CanvasStorageService`)**: Production-grade storage coordinator.
- **In-Memory Storage Adapter Fallback**: Automatically activates when `indexedDB` is unavailable (e.g. Node.js test runners, SSR, or restricted webview contexts) so unit tests run at 100% speed without external mock dependencies.

---

## ⚡ Core Invariants & Features

### 1. Ring Buffer History Log (Max 100 Transactions)
- Every user edit records a `Transaction` containing RFC 6902 forward and inverse JSON patches.
- To prevent IndexedDB storage inflation over long editing sessions, history is constrained to `MAX_RING_BUFFER_SIZE = 100` transactions per draft.
- When saving transaction #101+, the oldest transactions are automatically evicted from the `history` store.
- `getRingBufferStats(draftId)` reports `totalRecorded`, `currentCount`, `oldestSequenceNumber`, `newestSequenceNumber`, and `capacity`.

### 2. Differential Snapshots (RFC 6902 JSON Patches)
- `saveDraft(state, { isDifferential: true, baseDraftId: '...' })` compares target state against the base draft using `JsonPatchEngine.generateDiff()`.
- Stores light forward/inverse patch sets instead of repeating complete state trees.
- `getDraft(id)` automatically reconstructs target state by applying `forwardPatches` to `baseDraft.state` via `JsonPatchEngine.applyPatch()`.
- Deterministic FNV-1a checksums (`calculateChecksum()`) ensure state integrity before and after reconstruction.

### 3. Auto-Save Engine & Browser Lifecycle
- `startAutoSave(getStateFn, intervalMs = 300000)` runs a background timer (default 5 min).
- Checks `isDirty()` status before disk writes to eliminate redundant IO.
- Automatically binds `beforeunload` and `pagehide` browser events to trigger sync saves on tab closure or navigation.

### 4. Crash Recovery Protocol (`recoverFromCrash`)
- `flagSessionStart(draftId)` sets `isCrashed = true` in session metadata on startup.
- `flagSessionCleanExit()` clears `isCrashed = false` on graceful shutdown or explicit save.
- `checkCrashStatus()` detects ungraceful exits on application load.
- `recoverFromCrash()`:
  1. Retrieves the last saved base draft state.
  2. Queries all uncommitted transaction logs for that draft in sequence.
  3. Replays forward patches step-by-step to reconstruct exact pre-crash state.
  4. Saves a new recovered draft snapshot and clears crash flags.

---

## 🧪 Testing Invariant

Run Node.js native test runner with `npx tsx`:
```bash
npx tsx --test apps/web/src/canvas/storage/storage.test.ts
```
All 16 unit tests verify schema parsing, draft saving/retrieval, ring buffer truncation, differential patching, auto-save timers, and crash recovery.
