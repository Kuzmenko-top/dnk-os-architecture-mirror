# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-COMP-042_agentic-habits-contracts.md"
# purpose: "Component Contracts: Python Interfaces, Data Structures, and Telemetry Schemas for Habit Guards."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Herich Librarian"
# --- END DNK-MRH-HEADER ---

# Component Contracts: Habit Guards & Evidence Ledger (DNK-COMP-042)

## 1. Core Classes & Data Structures

### `VerificationEvidence` (`core/guards/completion_gate.py`)
```python
@dataclass
class VerificationEvidence:
    commands_executed: List[str]
    exit_codes: List[int]
    test_passed: bool
    stop_hook_active: bool
```

### `GateVerdict` (`core/guards/completion_gate.py`)
```python
@dataclass
class GateVerdict:
    allowed: bool
    reason: Optional[str] = None
    detected_claim: Optional[str] = None
```

### `EvidenceLedger` (`core/guards/habit_judge.py`)
```python
class EvidenceLedger:
    def record_raw(self, source: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None: ...
    def record_infer(self, source: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None: ...
    def get_raw_entries(self) -> List[EvidenceEntry]: ...
    def get_infer_entries(self) -> List[EvidenceEntry]: ...
```

### `HabitAuditVerdict` (`core/guards/habit_judge.py`)
```python
@dataclass
class HabitAuditVerdict:
    passed: bool
    score: float
    violations: List[str]
    raw_evidence_count: int
    infer_evidence_count: int
    summary: str
```
