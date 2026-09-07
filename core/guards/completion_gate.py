# --- DNK-MRH-HEADER ---
# mrh_id: "core/guards/completion_gate.py"
# purpose: "Tier 2 Deterministic Completion Gate: Prevents unverified success claims (Phantom Done / Green-Washing)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VerificationEvidence:
    """Telemetry evidence recorded from actual tool invocations during an agent turn."""
    commands_executed: List[str] = field(default_factory=list)
    exit_codes: List[int] = field(default_factory=list)
    test_passed: bool = False
    stop_hook_active: bool = False


@dataclass
class GateVerdict:
    """Decision rendered by the deterministic Completion Gate."""
    allowed: bool
    reason: Optional[str] = None
    detected_claim: Optional[str] = None


class CompletionGate:
    """
    Tier 2 Completion Gate.
    Refuses to let an agent turn end claiming tests or builds passed when nothing was run to find out.
    
    Design Invariants (assimilated from AgriciDaniel/agentic-habits):
      1. Fail Open: Any uncertainty or parse error allows turn completion (avoids false-positive deadlock).
      2. Never Recurse: Recursion guard prevents repeated blocking in the same turn.
      3. Reward Disclosure: Honest statements like 'I have not run tests' are never blocked.
      4. High-Precision Regex: Tight regex matching specific test/build pass claims without fuzzy hallucinations.
    """

    # Narrow triggers for first-hand claims of test or build success
    CLAIM_PATTERNS = [
        # English
        r"\b(?:all\s+|the\s+)?(?:unit\s+|integration\s+|e2e\s+)?tests?(?:\s+suite)?\s+(?:now\s+)?(?:pass(?:es|ed)?|are\s+passing)\b",
        r"\b(?:all\s+)?(?:checks|verifications)\s+(?:are\s+)?(?:green|passed|passing)\b",
        r"\b(?:test\s+suite|verify_all(?:\.sh)?)\s+(?:now\s+)?(?:passed|clean)\b",
        r"\bbuild\s+(?:is\s+)?clean\b",
        # Ukrainian
        r"\b(?:всі\s+)?тести\s+(?:успішно\s+)?пройш(?:ли|ось)\b",
        r"\bтести\s+пройдено\b",
        r"\bвсі\s+перевірки\s+(?:зелені|пройшли|успішні)\b",
        r"\b(?:перевірка|верифікація)\s+успішна\b",
        r"\bбілд\s+чистий\b",
    ]

    # Hedging / Disqualifiers: statements acknowledging lack of testing are NOT blocked
    DISQUALIFIER_PATTERNS = [
        r"\b(?:have\s+not|haven't|did\s+not|didn't)\s+(?:run|executed?|tested?)\b",
        r"\b(?:not\s+yet\s+run|without\s+running|untested|not\s+verified)\b",
        r"\b(?:не\s+запускав|не\s+тестував|не\s+перевіряв|без\s+запуску)\b",
        r"\b(?:потрібно\s+запустити|слід\s+перевірити|варто\s+протестувати)\b",
    ]

    VERIFICATION_COMMAND_PATTERNS = [
        r"\bpytest\b",
        r"\bverify_all\.sh\b",
        r"\bnpm\s+test\b",
        r"\bvitest\b",
        r"\bcargo\s+test\b",
        r"\bpython3?\s+-m\s+unittest\b",
    ]

    def evaluate(self, assistant_message: str, evidence: Optional[VerificationEvidence] = None) -> GateVerdict:
        try:
            if not assistant_message or not assistant_message.strip():
                return GateVerdict(allowed=True)

            evidence = evidence or VerificationEvidence()

            # Rule 2: Never Recurse (Fail-Open recursion guard)
            if evidence.stop_hook_active:
                return GateVerdict(allowed=True)

            # Rule 3: Reward Disclosure (Check disqualifiers / honest hedging)
            for d_pat in self.DISQUALIFIER_PATTERNS:
                if re.search(d_pat, assistant_message, re.IGNORECASE):
                    return GateVerdict(allowed=True)

            # Rule 4: Match unhedged claims
            matched_claim = None
            for c_pat in self.CLAIM_PATTERNS:
                m = re.search(c_pat, assistant_message, re.IGNORECASE)
                if m:
                    matched_claim = m.group(0)
                    break

            if not matched_claim:
                return GateVerdict(allowed=True)

            # A claim was made. Check if real verification evidence exists
            has_valid_command = False
            for cmd in evidence.commands_executed:
                if any(re.search(v_pat, cmd, re.IGNORECASE) for v_pat in self.VERIFICATION_COMMAND_PATTERNS):
                    has_valid_command = True
                    break

            has_zero_exit = any(ec == 0 for ec in evidence.exit_codes) if evidence.exit_codes else False
            has_evidence = evidence.test_passed or (has_valid_command and has_zero_exit)

            if has_evidence:
                return GateVerdict(allowed=True, detected_claim=matched_claim)

            # No evidence found -> Refuse to let turn end claiming success
            block_reason = (
                f"🛡️ BLOCKED by CompletionGate (Anti-Phantom-Done): "
                f"Assistant claimed '{matched_claim}', but no verification command "
                f"(`pytest`, `bash scripts/verify_all.sh`, etc.) with exit code 0 was executed in this turn! "
                f"Execute the test command or state honestly that testing was omitted."
            )
            return GateVerdict(allowed=False, reason=block_reason, detected_claim=matched_claim)

        except Exception:
            # Rule 1: Fail Open on internal exception
            return GateVerdict(allowed=True)
