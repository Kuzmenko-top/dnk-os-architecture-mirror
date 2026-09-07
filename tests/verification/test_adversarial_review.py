# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_adversarial_review.py"
# purpose: "Unit & Integration tests for Adversarial Review Engine (Auditor vs Builder) in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import tempfile
import sys
import json
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
if HUB_ROOT.name == "DNK OS":
    HUB_ROOT = HUB_ROOT.parent
sys.path.insert(0, str(HUB_ROOT))
sys.path.insert(0, str(HUB_ROOT))

from core.security.adversarial_review import (
    AdversarialReviewEngine,
    AttackFinding,
    DefenseVerdict,
)

hermes_tools_path = str(HUB_ROOT / "core" / "hermes_agent")
if hermes_tools_path not in sys.path:
    sys.path.append(hermes_tools_path)

from tools.dnk_adversarial_review_tool import dnk_run_adversarial_review

if hermes_tools_path in sys.path:
    sys.path.remove(hermes_tools_path)


def test_adversarial_engine_clean_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        clean_code = '''# --- DNK-MRH-HEADER ---
# mrh_id: "core/example.py"
# purpose: "Example test file"
# canonical_source: true
# --- END DNK-MRH-HEADER ---

def add(a: int, b: int) -> int:
    return a + b
'''
        file_path = tmp_p / "example.py"
        file_path.write_text(clean_code)

        engine = AdversarialReviewEngine(root_dir=tmpdir)
        findings = engine.attack_file("example.py")
        assert len(findings) == 0


def test_adversarial_engine_detects_mrh_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        code = '''def hello():
    return "world"
'''
        file_path = tmp_p / "hello.py"
        file_path.write_text(code)

        engine = AdversarialReviewEngine(root_dir=tmpdir)
        findings = engine.attack_file("hello.py")
        assert any(f.category == "MRH_COMPLIANCE" for f in findings)


def test_adversarial_engine_detects_absolute_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        bad_path = "/User" + "s/developer/data"
        code = f'''# --- DNK-MRH-HEADER ---
# mrh_id: "core/data_loader.py"
# purpose: "Testing path"
# --- END DNK-MRH-HEADER ---

def get_data_dir():
    return "{bad_path}"
'''
        file_path = tmp_p / "data_loader.py"
        file_path.write_text(code)

        engine = AdversarialReviewEngine(root_dir=tmpdir)
        findings = engine.attack_file("data_loader.py")
        assert any(f.category == "PATH_HYGIENE" for f in findings)
        path_finding = next(f for f in findings if f.category == "PATH_HYGIENE")
        verdict = engine.defend_finding(path_finding)
        assert verdict.status == "confirmed"


def test_adversarial_engine_refutes_false_positives_in_tests():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        code = '''# --- DNK-MRH-HEADER ---
# mrh_id: "tests/test_mock.py"
# purpose: "Testing mock token"
# --- END DNK-MRH-HEADER ---

def test_api():
    api_key = "ghp_example_mock_token_1234567890abcdef"
    assert api_key.startswith("ghp_")
'''
        file_path = tmp_p / "tests" / "test_mock.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code)

        engine = AdversarialReviewEngine(root_dir=tmpdir)
        findings = engine.attack_file("tests/test_mock.py")
        assert any(f.category == "SECRET_LEAK" for f in findings)
        secret_finding = next(f for f in findings if f.category == "SECRET_LEAK")
        verdict = engine.defend_finding(secret_finding)
        assert verdict.status == "refuted"


def test_adversarial_engine_detects_sync_sleep_in_async():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        code = '''# --- DNK-MRH-HEADER ---
# mrh_id: "core/async_worker.py"
# purpose: "Async worker"
# --- END DNK-MRH-HEADER ---
import time

async def process():
    time.sleep(5)
'''
        file_path = tmp_p / "async_worker.py"
        file_path.write_text(code)

        engine = AdversarialReviewEngine(root_dir=tmpdir)
        findings = engine.attack_file("async_worker.py")
        assert any(f.category == "ASYNC_BLOCKING" for f in findings)


def test_adversarial_engine_detects_eval():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        code = '''# --- DNK-MRH-HEADER ---
# mrh_id: "core/unsafe.py"
# purpose: "Unsafe code"
# --- END DNK-MRH-HEADER ---

def run_user_code(user_input: str):
    return eval(user_input)
'''
        file_path = tmp_p / "unsafe.py"
        file_path.write_text(code)

        engine = AdversarialReviewEngine(root_dir=tmpdir)
        findings = engine.attack_file("unsafe.py")
        assert any(f.category == "SECURITY_RISK" for f in findings)


def test_dnk_run_adversarial_review_tool_execution():
    result_raw = dnk_run_adversarial_review(target_path="core/security")
    data = json.loads(result_raw)
    assert data["status"] == "success"
    assert data["passed"] is True
