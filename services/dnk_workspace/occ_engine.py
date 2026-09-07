# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_workspace/occ_engine.py"
# purpose: "Re-export OCCConcurrencyEngine for backward compatibility"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

from core.occ_merge import (
    OCCConcurrencyEngine,
    OCCGraphMergeResolver,
    OCCMergeResult,
    MergeConflict,
    PositionConflictStrategy,
)

__all__ = [
    "OCCConcurrencyEngine",
    "OCCGraphMergeResolver",
    "OCCMergeResult",
    "MergeConflict",
    "PositionConflictStrategy",
]
