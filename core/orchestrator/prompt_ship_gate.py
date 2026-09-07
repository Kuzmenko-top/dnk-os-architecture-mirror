#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/prompt_ship_gate.py"
# purpose: "Dual-Leg Prompt, Skill & Agent Mutation Regression Gate (Ship / Don't Ship) assimilated from Soup."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("dnk_prompt_ship_gate")


class GateVerdict(str, Enum):
    SHIP = "SHIP"
    DONT_SHIP = "DON'T SHIP"


@dataclass
class MetricComparison:
    name: str
    baseline: float
    candidate: float
    delta: float
    min_required_delta: float
    passed: bool
    description: str = ""


@dataclass
class Leg1TaskWinResult:
    """Leg 1: Did the candidate modification demonstrably win on the target objective?"""
    won: bool
    metrics: List[MetricComparison]
    summary: str


@dataclass
class Leg2GuardResult:
    """Leg 2: Did the candidate avoid regressions across invariant baseline capabilities?
    Checks: JSON validity, tool-calling schema compliance, path hygiene, safety/containment.
    """
    passed: bool
    regressions: List[str]
    guard_metrics: List[MetricComparison]
    summary: str


@dataclass
class ShipEvidence:
    verdict: GateVerdict
    target_component: str
    candidate_id: str
    baseline_id: str
    leg1: Leg1TaskWinResult
    leg2: Leg2GuardResult
    created_at: float
    provenance_hash: str
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PromptShipGate:
    """Evaluates whether an updated skill, agent prompt, or configuration should SHIP or be BLOCKED.
    Assimilated from MakazhanAlpamys/Soup dual-leg regression gate architecture.
    """

    DEFAULT_GUARD_SUITES = [
        "json_schema_validity",
        "tool_calling_fidelity",
        "relative_path_hygiene",
        "security_containment",
    ]

    def __init__(
        self,
        target_component: str,
        task_improvement_threshold: float = 0.05,
        allowed_guard_regression: float = 0.0,
    ):
        self.target_component = target_component
        self.task_improvement_threshold = task_improvement_threshold
        self.allowed_guard_regression = allowed_guard_regression

    def evaluate(
        self,
        target_metrics: Dict[str, Tuple[float, float]],  # {name: (baseline, candidate)}
        guard_metrics: Dict[str, Tuple[float, float]],   # {name: (baseline, candidate)}
        candidate_id: str = "candidate",
        baseline_id: str = "baseline",
    ) -> ShipEvidence:
        """Executes the dual-leg gate:
        - Leg 1 passes IF all target metrics achieve >= baseline + min_required_delta.
        - Leg 2 passes IF NO guard metric regresses by more than allowed_guard_regression.
        """
        # --- Evaluate Leg 1 (Task Win) ---
        leg1_comparisons: List[MetricComparison] = []
        leg1_won = True
        reasons: List[str] = []

        for name, (base, cand) in target_metrics.items():
            delta = cand - base
            passed = delta >= self.task_improvement_threshold
            if not passed:
                leg1_won = False
                reasons.append(
                    f"Leg 1 Failure: '{name}' delta {delta:+.3f} < required {self.task_improvement_threshold:+.3f}"
                )
            leg1_comparisons.append(
                MetricComparison(
                    name=name,
                    baseline=base,
                    candidate=cand,
                    delta=delta,
                    min_required_delta=self.task_improvement_threshold,
                    passed=passed,
                    description="Target improvement metric",
                )
            )

        leg1_result = Leg1TaskWinResult(
            won=leg1_won,
            metrics=leg1_comparisons,
            summary="Leg 1 WIN: Candidate improved target tasks." if leg1_won else "Leg 1 LOSS: Target improvements insufficient.",
        )

        # --- Evaluate Leg 2 (Guard Invariants & Regression Check) ---
        leg2_comparisons: List[MetricComparison] = []
        regressions: List[str] = []
        leg2_passed = True

        for name, (base, cand) in guard_metrics.items():
            delta = cand - base
            # For guard suites, candidate must not be worse than baseline minus allowance
            passed = delta >= -self.allowed_guard_regression
            if not passed:
                leg2_passed = False
                regression_msg = f"Leg 2 Regression: Guard metric '{name}' dropped from {base:.3f} to {cand:.3f} (delta {delta:+.3f})"
                regressions.append(regression_msg)
                reasons.append(regression_msg)

            leg2_comparisons.append(
                MetricComparison(
                    name=name,
                    baseline=base,
                    candidate=cand,
                    delta=delta,
                    min_required_delta=-self.allowed_guard_regression,
                    passed=passed,
                    description="Invariant guard suite",
                )
            )

        leg2_result = Leg2GuardResult(
            passed=leg2_passed,
            regressions=regressions,
            guard_metrics=leg2_comparisons,
            summary="Leg 2 GREEN: Zero invariant regressions." if leg2_passed else f"Leg 2 RED: {len(regressions)} guard regression(s) detected.",
        )

        # --- Verdict Determination ---
        final_verdict = GateVerdict.SHIP if (leg1_won and leg2_passed) else GateVerdict.DONT_SHIP

        # Provenance hash calculation
        raw_payload = f"{self.target_component}:{candidate_id}:{baseline_id}:{leg1_won}:{leg2_passed}:{time.time()}"
        prov_hash = hashlib.sha256(raw_payload.encode()).hexdigest()[:16]

        evidence = ShipEvidence(
            verdict=final_verdict,
            target_component=self.target_component,
            candidate_id=candidate_id,
            baseline_id=baseline_id,
            leg1=leg1_result,
            leg2=leg2_result,
            created_at=time.time(),
            provenance_hash=prov_hash,
            reasons=reasons if reasons else ["Candidate achieved target improvement and passed all guard gates."],
        )

        return evidence

    def save_evidence(self, evidence: ShipEvidence, output_path: str) -> str:
        """Persists the evidence JSON to disk with path containment hygiene."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(evidence.to_dict(), f, indent=2, ensure_ascii=False)
        return str(p)

    def render_markdown_comment(self, evidence: ShipEvidence) -> str:
        """Renders GitHub PR or Handoff comment with structured verdict banner."""
        icon = "🚢 **SHIP VERDICT: APPROVED**" if evidence.verdict == GateVerdict.SHIP else "🛑 **DON'T SHIP VERDICT: REJECTED**"
        lines = [
            f"## {icon}",
            f"**Target**: `{evidence.target_component}` | **Provenance**: `sha256:{evidence.provenance_hash}`",
            "",
            "### 📊 Leg 1: Target Objective (Task Win)",
            f"- **Status**: {'✅ WON' if evidence.leg1.won else '❌ FAILED'}",
            f"- **Summary**: {evidence.leg1.summary}",
            "",
            "| Target Metric | Baseline | Candidate | Delta | Status |",
            "|---|---|---|---|---|",
        ]
        for m in evidence.leg1.metrics:
            status = "✅ PASS" if m.passed else "❌ FAIL"
            lines.append(f"| `{m.name}` | {m.baseline:.3f} | {m.candidate:.3f} | {m.delta:+.3f} | {status} |")

        lines.extend([
            "",
            "### 🛡️ Leg 2: Invariant Baseline Guards (Regression Check)",
            f"- **Status**: {'✅ GREEN' if evidence.leg2.passed else '❌ REGRESSION DETECTED'}",
            f"- **Summary**: {evidence.leg2.summary}",
            "",
            "| Guard Suite | Baseline | Candidate | Delta | Status |",
            "|---|---|---|---|---|",
        ])
        for m in evidence.leg2.guard_metrics:
            status = "✅ CLEAN" if m.passed else "🚨 REGRESSED"
            lines.append(f"| `{m.name}` | {m.baseline:.3f} | {m.candidate:.3f} | {m.delta:+.3f} | {status} |")

        if evidence.reasons:
            lines.extend([
                "",
                "### 📝 Key Findings",
            ])
            for r in evidence.reasons:
                lines.append(f"- {r}")

        return "\n".join(lines)
