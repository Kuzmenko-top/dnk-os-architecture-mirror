# --- DNK-MRH-HEADER ---
# mrh_id: "core_tests_test_patch_generator"
# purpose: "Unit tests for Autonomous Distiller Patch Generator (task-distiller-patch)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# --- END DNK-MRH-HEADER ---

import os
import json
import tempfile
import pytest

from core.error_distillation.patch_generator import (
    DistillerPatchGenerator,
    MatchResult,
    PatchResult
)


@pytest.fixture
def temp_distill_db():
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
        initial_data = [
            {
                "pattern": "(AttributeError:.*model_dump|\\.dict\\(\\))",
                "category": "PYDANTIC_V2_MIGRATION",
                "root_cause": "Using legacy Pydantic v1 .dict() method instead of v2 .model_dump().",
                "solution": "Replace .dict() with .model_dump() across all domain model calls."
            },
            {
                "pattern": "(ModuleNotFoundError|No module named 'apps\\.)",
                "category": "MODULE_IMPORT_PATH",
                "root_cause": "Module exists in apps/ but was not synced to root apps/ or PYTHONPATH.",
                "solution": "Ensure PYTHONPATH includes root workspace."
            }
        ]
        json.dump(initial_data, f)
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_match_traceback_exact_regex(temp_distill_db):
    generator = DistillerPatchGenerator(db_path=temp_distill_db)
    traceback_sample = """
    Traceback (most recent call last):
      File "main.py", line 42, in <module>
        res = item.dict()
    AttributeError: 'Item' object has no attribute 'dict'
    """
    result = generator.match_traceback(traceback_sample)
    assert result.matched is True
    assert result.category == "PYDANTIC_V2_MIGRATION"
    assert result.score == 1.0
    assert "model_dump" in result.solution


def test_match_traceback_similarity(temp_distill_db):
    generator = DistillerPatchGenerator(db_path=temp_distill_db)
    fuzzy_err = "No module named apps.api.models found during test execution"
    result = generator.match_traceback(fuzzy_err)
    assert result.matched is True
    assert result.category == "MODULE_IMPORT_PATH"
    assert result.score >= 0.20


def test_generate_unified_diff(temp_distill_db):
    generator = DistillerPatchGenerator(db_path=temp_distill_db)
    old = "def foo():\n    return item.dict()\n"
    new = "def foo():\n    return item.model_dump()\n"
    diff = generator.generate_unified_diff("app.py", old, new)
    assert "--- a/app.py" in diff
    assert "+++ b/app.py" in diff
    assert "-    return item.dict()" in diff
    assert "+    return item.model_dump()" in diff


def test_apply_fuzzy_replacement_exact(temp_distill_db):
    generator = DistillerPatchGenerator(db_path=temp_distill_db)
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as f:
        f.write("def calculate():\n    data = obj.dict()\n    return data\n")
        file_path = f.name

    try:
        res = generator.apply_fuzzy_replacement(
            file_path=file_path,
            target_pattern_or_snippet="data = obj.dict()",
            replacement_snippet="data = obj.model_dump()"
        )
        assert res.success is True
        assert "-    data = obj.dict()" in res.diff
        assert "+    data = obj.model_dump()" in res.diff

        with open(file_path, "r") as f:
            content = f.read()
        assert "data = obj.model_dump()" in content
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def test_apply_fuzzy_replacement_fuzzy_window(temp_distill_db):
    generator = DistillerPatchGenerator(db_path=temp_distill_db)
    content = "class A:\n    def run(self):\n        val = self.compute()\n        return val\n"
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as f:
        f.write(content)
        file_path = f.name

    try:
        # Slightly altered whitespace / lines
        target = "    val = self.compute()\n    return val"
        replacement = "        return self.compute_safe()"
        res = generator.apply_fuzzy_replacement(
            file_path=file_path,
            target_pattern_or_snippet=target,
            replacement_snippet=replacement
        )
        assert res.success is True
        with open(file_path, "r") as f:
            updated = f.read()
        assert "compute_safe" in updated
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def test_log_verified_solution(temp_distill_db):
    generator = DistillerPatchGenerator(db_path=temp_distill_db)
    ok = generator.log_verified_solution(
        error_pattern="ZeroDivisionError_TestPattern",
        category="MATH_DIVISION",
        root_cause="Denominator evaluated to 0",
        solution="Guard with if denom != 0",
        workspace_id="ws-test-99"
    )
    assert ok is True

    match = generator.match_traceback("ZeroDivisionError_TestPattern in line 99")
    assert match.matched is True
    assert match.category == "MATH_DIVISION"
    assert "Guard with if denom != 0" in match.solution
