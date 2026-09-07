# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/capcut/audits/results/DNK-COMP-AI-DESIGN-DTO.py"
# purpose: "Canonical Pydantic v2 DTO for DNK OS AI Design Canvas & Undo/Redo Engine (v0.2)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "0.2.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime) & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CommandCategory(str, Enum):
    STRUCTURE = "Structure"
    SPATIAL = "Spatial"
    MUTATION = "Mutation"
    HIERARCHY = "Hierarchy"
    DOCUMENT = "Document"
    BATCH = "Batch"


class CommandType(str, Enum):
    ADD_IN_CANVAS = "ADD_IN_CANVAS"
    ADD_PLACEHOLDER_OPERATION = "ADD_PLACEHOLDER_OPERATION"
    DELETE_NODE = "DELETE_NODE"
    REMOVE_NODES_BY_FILTER = "REMOVE_NODES_BY_FILTER"
    UPDATE_NODE = "UPDATE_NODE"
    MOVE_NODE = "MOVE_NODE"
    RESIZE_NODE = "RESIZE_NODE"
    GROUP_CREATE = "GROUP_CREATE"
    GROUP_UNGROUP = "GROUP_UNGROUP"
    GROUP_UPDATE_BOUNDS = "GROUP_UPDATE_BOUNDS"
    SET_DOCUMENT_PROPERTY = "SET_DOCUMENT_PROPERTY"
    SET_DOCUMENT_METADATA = "SET_DOCUMENT_METADATA"


class JSONPatchOp(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"
    MOVE = "move"
    COPY = "copy"
    TEST = "test"


class JSONPatchEntry(BaseModel):
    op: JSONPatchOp
    path: str
    value: Optional[Any] = None
    old_value: Optional[Any] = Field(default=None, alias="oldValue")


class CommandPayload(BaseModel):
    target_ids: List[str] = Field(default_factory=list)
    patch: Optional[List[JSONPatchEntry]] = None
    node_snapshot: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Transaction(BaseModel):
    operate_id: str = Field(description="Unique UUID for transaction coalescing")
    operate_type: CommandType
    category: CommandCategory
    can_undo_redo: bool = True
    is_collaborative: bool = False
    redo_command: CommandPayload
    undo_command: CommandPayload
    timestamp: int = Field(description="Epoch ms timestamp")

    def reverse(self) -> "Transaction":
        """Returns the symmetric inverse transaction."""
        return Transaction(
            operate_id=self.operate_id,
            operate_type=self.operate_type,
            category=self.category,
            can_undo_redo=self.can_undo_redo,
            is_collaborative=self.is_collaborative,
            redo_command=self.undo_command,
            undo_command=self.redo_command,
            timestamp=self.timestamp,
        )


class DifferentialSnapshot(BaseModel):
    snapshot_id: str
    base_state_hash: str
    transaction_index: int
    full_state_tree: Optional[Dict[str, Any]] = None
    is_keyframe: bool = False
    timestamp: int


class UndoRedoState(BaseModel):
    """Canonical Undo/Redo Engine State for DNK OS Canvas."""
    undo_stack: List[Transaction] = Field(default_factory=list)
    redo_stack: List[Transaction] = Field(default_factory=list)
    max_stack_size: int = 100
    max_memory_mb: int = 500
    auto_checkpoint_minutes: int = 5
    differential_snapshots: bool = True
    snapshot_interval: int = 10

    def can_undo(self) -> bool:
        return any(t.can_undo_redo for t in self.undo_stack)

    def can_redo(self) -> bool:
        return any(t.can_undo_redo for t in self.redo_stack)

    def push(self, transaction: Transaction, clear_redo: bool = True) -> None:
        if clear_redo:
            self.redo_stack.clear()
        self.undo_stack.insert(0, transaction)
        if len(self.undo_stack) > self.max_stack_size:
            self.undo_stack.pop()

    def undo(self) -> Optional[Transaction]:
        if not self.can_undo():
            return None
        tx = self.undo_stack.pop(0)
        reversed_tx = tx.reverse()
        self.redo_stack.insert(0, reversed_tx)
        return tx

    def redo(self) -> Optional[Transaction]:
        if not self.can_redo():
            return None
        tx = self.redo_stack.pop(0)
        reversed_tx = tx.reverse()
        self.undo_stack.insert(0, reversed_tx)
        return tx


class DraftMetaSchema(BaseModel):
    id: str
    title: str
    width: int
    height: int
    dpi: int = 300
    preview_url: Optional[str] = None
    update_time: int
    create_time: int


class DraftStorageRecord(BaseModel):
    id: str
    meta: DraftMetaSchema
    scene_graph: Dict[str, Any]
    history_state: UndoRedoState
    update_time: int


# Rebuild models for typing
Transaction.model_rebuild()
UndoRedoState.model_rebuild()
DraftStorageRecord.model_rebuild()
