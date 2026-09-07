# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_accounting_langfuse.py"
# purpose: "Verify Langfuse SDK integration with AccountingEngine."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import os
import shutil
import pytest
from typing import Generator
from core.accounting_engine import AccountingEngine

TEST_DIR = "test_run_accounting_temp"
ACCOUNTING_LOG = f"{TEST_DIR}/accounting_log.json"

@pytest.fixture(autouse=True)
def run_around_tests() -> Generator[None, None, None]:
    """Cleans and scaffolds the temporary test directory."""
    os.makedirs(TEST_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR, ignore_errors=True)


def test_accounting_langfuse_mocked(monkeypatch):
    """
    Verifies that AccountingEngine can initialize Langfuse client and send traces
    safely when dummy credentials are provided.
    """
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-mock-key")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-mock-key")
    monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:4000")

    from unittest.mock import MagicMock
    import core.accounting_engine as ac_module
    if ac_module.Langfuse is None:
        monkeypatch.setattr(ac_module, "Langfuse", MagicMock())

    engine = AccountingEngine(log_path=ACCOUNTING_LOG)
    assert engine.langfuse is not None

    # Log telemetry with credentials to trigger SDK trace methods
    record = engine.log_workflow_telemetry(
        project_id="00_CORE",
        task_id="T_LF_TEST",
        tokens_in=100,
        tokens_out=200,
        cost_usd=0.0003,
        duration_ms=45,
        success=True,
        notes="Testing Langfuse non-blocking trace push"
    )

    assert record["task_id"] == "T_LF_TEST"
    assert record["success"] is True


def test_accounting_log_retention():
    """
    Verifies that AccountingEngine enforces max_records retention policy
    to prevent unbounded file growth.
    """
    engine = AccountingEngine(log_path=ACCOUNTING_LOG, max_records=5)
    for i in range(12):
        engine.log_workflow_telemetry(
            project_id="TEST_PROJ",
            task_id=f"TASK_{i}",
            tokens_in=100,
            tokens_out=200,
            cost_usd=0.01 * (i + 1),
            duration_ms=100,
            success=True,
            notes=f"Iteration {i}"
        )

    records = engine._read_records()
    assert len(records) == 5
    # The last recorded tasks should be TASK_7 through TASK_11
    assert records[-1]["task_id"] == "TASK_11"
    assert records[0]["task_id"] == "TASK_7"

