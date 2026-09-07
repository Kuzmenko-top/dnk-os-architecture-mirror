# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/capcut/audits/results/command_pattern_analysis.md"
# purpose: "Comprehensive Deconstruction of CapCut Web Command Pattern & Undo/Redo Engine."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime) & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

# 🧠 CapCut Web Command Pattern & Undo/Redo Engine Deconstruction

## 1. Executive Summary
During **Iteration 3 (`CAPCUT-UNDO-REDO-AUDIT-003`)**, deep reverse-engineering of CapCut AI Design web bundles (`initial-canvas-support.dfca157fa4.js`, `initial-graphic-sdk.786f0a8f67.js`, and `initial-canvas-render.cd644a7350.js`) revealed a dual-layered, OT-enabled (Operational Transformation) Command Pattern stack.

---

## 2. Core Class Architecture

### 2.1 `UndoRedoStack` (Base Stack Engine - Module 52362)
Manages the standard LIFO stacks (`undoStack` and `redoStack`) with bounded ring-buffer pruning:
```javascript
class UndoRedoStack {
    constructor(maxSize = 100) {
        this.undoStack = [];
        this.redoStack = [];
        this.maxStackSize = maxSize;
    }

    push(command, clearRedo = true) {
        if (clearRedo) this.clearRedoStack();
        if (command.canUndoRedo || this.undoStack.length !== 0) {
            this.undoStack.unshift(command);
            if (this.undoStack.length > this.maxStackSize) {
                this.undoStack.pop(); // Drop oldest transaction
            }
        }
    }

    undo() {
        if (!this.canUndo()) return [];
        let index = this.getCanUndoRedoItemTopIndex(this.undoStack);
        if (index < 0) return this.clearUndoStack(), [];
        let item = this.undoStack.splice(index, 1)[0];
        item.execute("undo");
        let reversed = item.reverse();
        this.redoStack.unshift(reversed);
        return [item];
    }

    redo() {
        if (!this.canRedo()) return [];
        let item = this.redoStack.shift();
        item.execute("redo");
        let reversed = item.reverse();
        this.undoStack.unshift(reversed);
        return [item];
    }
}
```

### 2.2 `Command` Base Transaction Unit (Module 21895)
Every user mutation is wrapped in a symmetric invertible command:
- **`operateId`**: Globally unique UUID distinguishing distinct actions.
- **`redoCommand`**: Forward delta/execution payload.
- **`undoCommand`**: Reverse delta/restoration payload.
- **`canUndoRedo`**: Boolean flag indicating if action is undoable.
- **`operateType`**: Enum categorizing action type.
- **`reverse()`**: Method that swaps `redoCommand` and `undoCommand` to construct the opposite command cleanly without recalculating full state.

### 2.3 Continuous Transaction Coalescing (`pushWithOperateId`)
To prevent flooding the history stack when users drag nodes or slide values:
1. Intermediate mouse move / slider ticks share the same `operateId`.
2. The engine invokes `composeCommand(existingCmd, nextCmd)` to merge continuous deltas.
3. On mouse release, the `operateId` is finalized, leaving exactly **one** unified transaction in `undoStack`.

---

## 3. Command Topology & Identified Operations

| Command Type | Category | Forward Action (`redo`) | Reverse Action (`undo`) | Coalescing Mode |
| :--- | :--- | :--- | :--- | :--- |
| `ADD_IN_CANVAS` | Structure | Insert node/subtree | Remove node by ID | Discrete |
| `DELETE_NODE` | Structure | Remove node by ID | Restore node + subtree + z-index | Discrete |
| `MOVE_NODE` | Spatial | Set new (x, y) coords | Restore previous (x, y) coords | Continuous (`operateId`) |
| `UPDATE_NODE` | Mutation | Apply property patch | Revert property patch | Continuous (slider/color) |
| `GROUP_CREATE` | Hierarchy | Wrap nodes in Group | Explode Group to nodes | Discrete |
| `GROUP_UNGROUP` | Hierarchy | Explode Group to nodes | Wrap nodes in Group | Discrete |
| `GROUP_UPDATE_BOUNDS`| Spatial | Recalculate container bounds | Restore old bounds | Continuous |
| `SET_DOCUMENT_PROPERTY`| Document | Apply canvas resize/DPI | Restore previous dimensions | Discrete |
| `REMOVE_NODES_BY_FILTER`| Batch | Filter & delete nodes | Restore all filtered nodes | Discrete |

---

## 4. Collaborative Extensions (OT Integration)
Module `35610` (`CollaborativeUndoRedoStack`) extends `UndoRedoStack` with Operational Transformation:
- When a remote user mutates a node concurrently, local `undo` commands are transformed against remote pointers (`collaboratePointer`) before execution.
- Prevents desynchronization when undoing changes to nodes that received concurrent collaborative edits.
