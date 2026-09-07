# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/adversarial_gate_runner.py"
# purpose: "Fail-closed Adversarial Gate runner for verify_all.sh Step 2.5. Exits 1 on any ImportError or gate failure."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

"""
Adversarial Gate Runner — Fail-Closed.

Must be invoked with HUB_ROOT in PYTHONPATH:
  PYTHONPATH=$HUB_ROOT:$HUB_ROOT python3 scripts/system/adversarial_gate_runner.py

Exits 1 on:
  - ImportError / ModuleNotFoundError  (fail-closed, never skip)
  - AdversarialReviewEngine gate failure
  - AdversarialEvaluationEngine gate failure (ASR too high)
"""

import sys
import os
import traceback
from pathlib import Path

# Auto-inject hub root to sys.path
HUB_ROOT = Path(__file__).resolve().parent.parent
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))
if str(HUB_ROOT / "services") not in sys.path:
    sys.path.insert(0, str(HUB_ROOT / "services"))

# ── 1. Fail-closed import ────────────────────────────────────────────────────
try:
    from core.security.adversarial_review import AdversarialReviewEngine
    from core.security.adversarial_probe_library import AdversarialEvaluationEngine, GateStage
except ImportError as exc:
    print(f"❌ ADVERSARIAL GATE IMPORT FAILURE (fail-closed): {exc}")
    print("   Ensure PYTHONPATH includes HUB_ROOT and services.")
    print("   Run: PYTHONPATH=$HUB_ROOT:$HUB_ROOT/services python3 scripts/system/adversarial_gate_runner.py")
    traceback.print_exc()
    sys.exit(1)

# ── 2. Red-Team Review (Auditor ⚔️ vs Builder 🛡️) ──────────────────────────
try:
    engine = AdversarialReviewEngine(root_dir=".")
    report = engine.review_target("core/security")
except Exception as exc:
    print(f"❌ AdversarialReviewEngine crashed: {exc}")
    traceback.print_exc()
    sys.exit(1)

if not report.get("passed"):
    summary = report.get("summary", "Findings confirmed — no refutation possible")
    print(f"❌ Adversarial Gate Failed: {summary}")
    sys.exit(1)

# ── 3. Probe Library Evaluation ──────────────────────────────────────────────
try:
    eval_engine = AdversarialEvaluationEngine()
    eval_res = eval_engine.evaluate_text_defense(
        "safe_code_placeholder", stage=GateStage.STAGE_1_PR
    )
except Exception as exc:
    print(f"❌ AdversarialEvaluationEngine crashed: {exc}")
    traceback.print_exc()
    sys.exit(1)

if eval_res.get("gate_verdict") != "PASSED":
    asr_val = eval_res.get("attack_success_rate_percent")
    print(f"❌ Adversarial Probe Gate Failed: ASR={asr_val}%")
    sys.exit(1)

# ── 4. Success summary ───────────────────────────────────────────────────────
audited  = report.get("total_files_audited", 0)
findings = report.get("total_attack_findings", 0)
refuted  = report.get("refuted_false_positives", 0)
probes   = eval_res.get("total_probes", 0)
asr      = eval_res.get("attack_success_rate_percent", 0.0)

print(
    f"✅ Adversarial Gate Passed: {audited} files checked "
    f"({findings} findings, {refuted} refuted) | "
    f"{probes} probes evaluated (ASR={asr}%)."
)
sys.exit(0)
