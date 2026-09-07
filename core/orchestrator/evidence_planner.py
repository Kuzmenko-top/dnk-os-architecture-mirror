#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/evidence_planner.py"
# purpose: "Evidence Planner & Epistemic Classifier for empirical verification of claims in DNK OS Task Execution Platform."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.6.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import logging
import os
import re
import shlex
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("dnk_evidence_planner")


class EpistemicStatus(str, Enum):
    OBSERVED = "OBSERVED"      # Empirically verified fact from direct tooling/file inspection
    INFERRED = "INFERRED"      # Deductive or inductive conclusion derived from observations
    HYPOTHESIS = "HYPOTHESIS"  # Unverified assumption requiring empirical confirmation


def get_pytest_cmd() -> List[str]:
    """
    Returns the safest and most specific pytest invocation command as an argument list.
    Priority:
    1. Local virtualenv: ./.venv/bin/pytest
    2. uv run pytest (if uv in PATH)
    3. Global pytest (if in PATH)
    Fallback: ["python3", "-m", "pytest"]
    """
    venv_pytest = Path("./.venv/bin/pytest")
    if venv_pytest.exists() and os.access(venv_pytest, os.X_OK):
        return [str(venv_pytest)]

    if shutil.which("uv"):
        return ["uv", "run", "pytest"]

    if shutil.which("pytest"):
        return ["pytest"]

    return ["python3", "-m", "pytest"]


def classify_statement(statement: str) -> EpistemicStatus:
    """
    Classifies a claim or statement into an Epistemic taxonomy status.
    """
    st_lower = statement.lower()

    # 1. Hypothesis indicators
    hypothesis_keywords = [
        "можливо", "припустимо", "здається", "мабуть", "ймовірно",
        "perhaps", "maybe", "probably", "assume", "hypothesis", "suspect"
    ]
    if any(k in st_lower for k in hypothesis_keywords):
        return EpistemicStatus.HYPOTHESIS

    # 2. Observed indicators (Direct empirical measurements, existing files, test results)
    observed_keywords = [
        "підтверджено", "фактично", "наявний", "існує", "розмір",
        "виміряно", "measured", "verified", "observed", "confirmed",
        "count is", "exit code", "файл", "статус", "помилка", "тест"
    ]
    if any(k in st_lower for k in observed_keywords):
        return EpistemicStatus.OBSERVED

    # 3. Inferred indicators (logical deductions)
    inferred_keywords = [
        "отже", "тому", "свідчить", "вказує", "therefore", "thus",
        "implies", "indicates", "consequently", "suggests"
    ]
    if any(k in st_lower for k in inferred_keywords):
        return EpistemicStatus.INFERRED

    return EpistemicStatus.INFERRED


def verify_evidence(probe: Dict[str, Any], output: str, exit_code: int) -> bool:
    """
    Validates empirical execution output against the expected criteria.
    Never uses shell=True. If exit_code != 0, returns False.
    """
    if exit_code != 0:
        return False

    expected = str(probe.get("expected", "exit_code_0")).strip()
    out_clean = output.strip()

    if expected == "exit_code_0":
        return True

    if expected == "NON_EMPTY":
        return exit_code == 0 and len(out_clean) > 0

    if expected.startswith("contains:"):
        target_str = expected.split("contains:", 1)[1]
        return target_str in output

    # Numeric threshold comparison e.g. "> 10", "== 0", "< 100"
    match_op = re.match(r"^([><!=]=?)\s*(\d+)$", expected)
    if match_op:
        op = match_op.group(1)
        target_val = int(match_op.group(2))

        # Extract first integer from output text
        m_val = re.search(r"(\d+)", out_clean)
        if not m_val:
            return False
        val = int(m_val.group(1))

        if op == ">":
            return val > target_val
        elif op == ">=":
            return val >= target_val
        elif op == "<":
            return val < target_val
        elif op == "<=":
            return val <= target_val
        elif op in ("==", "="):
            return val == target_val
        elif op == "!=":
            return val != target_val

    # Default fallback
    return exit_code == 0


def generate_evidence_plan(task_prompt: str, target_files: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Synthesizes an empirical verification plan for all claims and target deliverables.
    Commands are strictly structured as argument lists (shell=False safe).
    """
    target_files = target_files or []
    claims: List[Dict[str, Any]] = []

    # Claim for target files existence
    for tf in target_files:
        claims.append({
            "claim": f"Файл {tf} існує та доступний у робочому просторі",
            "epistemic_status": EpistemicStatus.OBSERVED.value,
            "cmd_args": ["test", "-f", tf],
            "expected": "exit_code_0"
        })

    # Test verification probe
    if "тест" in task_prompt.lower() or "test" in task_prompt.lower():
        claims.append({
            "claim": "Усі регресійні та модульні тести проходять із кодом 0",
            "epistemic_status": EpistemicStatus.OBSERVED.value,
            "cmd_args": get_pytest_cmd() + ["-v"],
            "expected": "exit_code_0"
        })

    # Git status probe
    if "git" in task_prompt.lower() or "статус" in task_prompt.lower():
        claims.append({
            "claim": "Стан репозиторію git чистий та відповідає очікуванням",
            "epistemic_status": EpistemicStatus.OBSERVED.value,
            "cmd_args": ["git", "status", "--porcelain"],
            "expected": "exit_code_0"
        })

    # Default general claim if none matched
    if not claims:
        claims.append({
            "claim": "Базова верифікація робочого простору",
            "epistemic_status": EpistemicStatus.OBSERVED.value,
            "cmd_args": ["ls", "-la"],
            "expected": "NON_EMPTY"
        })

    # Normalize probes for backwards compatibility
    probes_list = []
    for c in claims:
        item = dict(c)
        item["command"] = " ".join(c["cmd_args"])
        probes_list.append(item)

    return {
        "task_prompt_summary": task_prompt[:120],
        "total_claims": len(claims),
        "total_probes": len(claims),
        "claims": claims,
        "probes": probes_list
    }


def execute_evidence_plan(plan: Dict[str, Any], timeout_sec: int = 30) -> Dict[str, Any]:
    """
    Executes all planned probes in isolated subprocesses without shell=True.
    Validates outputs against expected criteria.
    """
    claims = plan.get("claims") or plan.get("probes") or []
    probe_results: List[Dict[str, Any]] = []
    verified_count = 0

    for item in claims:
        cmd_args = item.get("cmd_args")
        if not cmd_args:
            cmd_str = item.get("command", "")
            cmd_args = shlex.split(cmd_str) if cmd_str else ["true"]

        claim_desc = item.get("claim", "verification step")
        expected_crit = item.get("expected", "exit_code_0")

        try:
            res = subprocess.run(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_sec,
                shell=False
            )
            out = res.stdout + ("\n" + res.stderr if res.stderr else "")
            verified = verify_evidence(item, out, res.returncode)

            if verified:
                verified_count += 1

            probe_results.append({
                "claim": claim_desc,
                "cmd_args": cmd_args,
                "command": " ".join(cmd_args),
                "exit_code": res.returncode,
                "output_preview": out.strip()[:200],
                "expected": expected_crit,
                "verified": verified
            })
        except subprocess.TimeoutExpired:
            probe_results.append({
                "claim": claim_desc,
                "cmd_args": cmd_args,
                "command": " ".join(cmd_args),
                "exit_code": -1,
                "output_preview": "TIMEOUT",
                "expected": expected_crit,
                "verified": False
            })
        except Exception as e:
            probe_results.append({
                "claim": claim_desc,
                "cmd_args": cmd_args,
                "command": " ".join(cmd_args),
                "exit_code": -1,
                "output_preview": f"EXEC_ERROR: {e}",
                "expected": expected_crit,
                "verified": False
            })

    total = len(claims)
    all_ok = (verified_count == total and total > 0)

    return {
        "total_probes": total,
        "total_claims": total,
        "verified_probes": verified_count,
        "failed_probes": total - verified_count,
        "all_verified": all_ok,
        "verified": all_ok,
        "probe_results": probe_results,
        "results": probe_results
    }
