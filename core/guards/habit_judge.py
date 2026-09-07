# --- DNK-MRH-HEADER ---
# mrh_id: "core/guards/habit_judge.py"
# purpose: "Tier 3 Judged Habit Reviewer & Evidence Ledger: Prevents Phantom Done, Green-Washing, and Inferrence Hallucinations"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceType(str, Enum):
    RAW = "RAW"        # Physical execution logs, stdout, diffs, tool outputs
    INFER = "INFER"    # Unverified claims, beliefs, narrative summaries


@dataclass
class EvidenceEntry:
    entry_type: EvidenceType
    source: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HabitAuditVerdict:
    passed: bool
    score: float
    violations: List[str] = field(default_factory=list)
    raw_evidence_count: int = 0
    infer_evidence_count: int = 0
    summary: str = ""


class EvidenceLedger:
    """
    Evidence Ledger enforcing strict separation between verified execution artifacts [RAW]
    and unverified narrative deductions [INFER].
    Rule: 'No evidence means not PASS'.
    """

    def __init__(self):
        self.entries: List[EvidenceEntry] = []

    def record_raw(self, source: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Record concrete tool execution, file diff, or exit code."""
        self.entries.append(
            EvidenceEntry(
                entry_type=EvidenceType.RAW,
                source=source,
                content=content,
                metadata=metadata or {},
            )
        )

    def record_infer(self, source: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Record model belief, unverified assumption, or intent."""
        self.entries.append(
            EvidenceEntry(
                entry_type=EvidenceType.INFER,
                source=source,
                content=content,
                metadata=metadata or {},
            )
        )

    def get_raw_entries(self) -> List[EvidenceEntry]:
        return [e for e in self.entries if e.entry_type == EvidenceType.RAW]

    def get_infer_entries(self) -> List[EvidenceEntry]:
        return [e for e in self.entries if e.entry_type == EvidenceType.INFER]

    def clear(self):
        self.entries.clear()


class HabitJudge:
    """
    Tier 3 Judged Habit Reviewer (inspired by AgriciDaniel/agentic-habits).
    Audits agent execution history against the 12 Anti-Habits:
      1. Phantom Done: claiming completion without test execution.
      2. Green-Washing: masking failing exit codes or asserting passes without execution.
      3. Guess Stacking: making multiple speculative changes without intermediate verification.
      4. Drive-by Refactor: touching files unrelated to the explicit task manifest.
      5. Silent Assumption: guessing missing configuration without verification or inquiry.
      6. Narration Theatre: long narrative descriptions substituted for tool actions.
    """

    ANTI_HABIT_PHANTOM_DONE = "PHANTOM_DONE"
    ANTI_HABIT_GREEN_WASHING = "GREEN_WASHING"
    ANTI_HABIT_GUESS_STACKING = "GUESS_STACKING"
    ANTI_HABIT_DRIVE_BY_REFACTOR = "DRIVE_BY_REFACTOR"
    ANTI_HABIT_NARRATION_THEATRE = "NARRATION_THEATRE"

    def __init__(self, ledger: Optional[EvidenceLedger] = None):
        self.ledger = ledger or EvidenceLedger()

    def audit(
        self,
        task_claim: str,
        target_files: Optional[List[str]] = None,
        touched_files: Optional[List[str]] = None,
    ) -> HabitAuditVerdict:
        raw_items = self.ledger.get_raw_entries()
        infer_items = self.ledger.get_infer_entries()
        violations: List[str] = []

        # 1. Anti-Habit: Phantom Done / Green-Washing
        # If task_claim asserts success/passes, verify that RAW evidence has a successful test exit code
        claim_lower = task_claim.lower()
        success_phrases = ["passed", "all tests green", "success", "пройшли", "успішно", "100% green"]
        asserts_success = any(phrase in claim_lower for phrase in success_phrases)

        has_raw_test_pass = False
        for entry in raw_items:
            if "test" in entry.source.lower() or "pytest" in entry.content.lower() or "verify" in entry.source.lower():
                exit_code = entry.metadata.get("exit_code", 0)
                if exit_code == 0:
                    has_raw_test_pass = True
                    break

        if asserts_success and not has_raw_test_pass:
            if len(raw_items) == 0:
                violations.append(f"{self.ANTI_HABIT_PHANTOM_DONE}: Claimed success without any RAW execution evidence.")
            else:
                violations.append(f"{self.ANTI_HABIT_GREEN_WASHING}: Claimed tests passed, but no zero exit-code test execution found in RAW evidence.")

        # 2. Anti-Habit: Drive-By Refactor
        if target_files is not None and touched_files is not None:
            target_set = set(target_files)
            unauthorized_touches = [f for f in touched_files if f not in target_set]
            if unauthorized_touches:
                violations.append(
                    f"{self.ANTI_HABIT_DRIVE_BY_REFACTOR}: Modified unauthorized files outside manifest: {unauthorized_touches}"
                )

        # 3. Anti-Habit: Narration Theatre
        # High volume of inferential assertions without raw grounding
        if len(infer_items) > 5 and len(raw_items) == 0:
            violations.append(
                f"{self.ANTI_HABIT_NARRATION_THEATRE}: Excessive narrative statements ({len(infer_items)}) with zero raw evidence."
            )

        passed = len(violations) == 0
        total_evidence = len(raw_items) + len(infer_items)
        score = (len(raw_items) / total_evidence * 100.0) if total_evidence > 0 else (100.0 if passed else 0.0)
        if not passed:
            score = min(score, 40.0)

        summary = "PASS: Verified by RAW evidence ledger." if passed else f"FAIL: {len(violations)} anti-habit violation(s) detected."

        return HabitAuditVerdict(
            passed=passed,
            score=round(score, 2),
            violations=violations,
            raw_evidence_count=len(raw_items),
            infer_evidence_count=len(infer_items),
            summary=summary,
        )
