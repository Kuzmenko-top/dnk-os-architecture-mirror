#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_task_spec_generator.py"
# purpose: "Unit and integration tests for Autonomous Task Spec Generator, Evidence Planner, Risk Gate, and GitHub Research."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import json
import subprocess
import pytest
from pathlib import Path

from core.orchestrator.task_spec_generator import (
    should_auto_spec,
    extract_task_title,
    get_next_slice_number,
    auto_generate_task_spec,
    format_target_files,
    save_task_spec
)
from core.orchestrator.evidence_planner import (
    generate_evidence_plan,
    classify_statement,
    EpistemicStatus,
    execute_evidence_plan
)
from core.orchestrator.risk_gate import (
    assess_risk,
    RiskLevel,
    create_backup_snapshot
)
from core.orchestrator.github_research import (
    analyze_github_repo,
    classify_license,
    LegalTrack,
    normalize_repo_slug
)

HUB_ROOT = Path(__file__).resolve().parent.parent.parent


def test_should_auto_spec_positive():
    queries = [
        "Герич, зроби аудит архітектури та знайди кращі open-source рішення на github.com",
        "створи новий ендпоінт для авторизації",
        "реалізуй асинхронну синхронізацію канвасу",
        "досліди проблеми у кодовій базі",
        "виправ помилку з тайм-аутом у тестах",
        "build a robust payment integration for shopify",
        "audit database queries for bottlenecks"
    ]
    for q in queries:
        assert should_auto_spec(q) is True, f"Expected True for: {q}"


def test_should_auto_spec_negative_for_questions_and_chat():
    queries = [
        "привіт, як справи?",
        "що таке SCONES memory?",
        "хто ти такий?",
        "what is the meaning of life?",
    ]
    for q in queries:
        assert should_auto_spec(q) is False, f"Expected False for: {q}"


def test_should_auto_spec_negative_for_already_structured_spec():
    structured = """# 🎯 СЛАЙС 13.1: Interactive Onboarding

## 📌 ЦІЛЬОВА ДИРЕКТИВА
Впровадити інтерактивний онбординг.
ВИКОНУЙ НЕГАЙНО.

## 🔒 PRECONDITIONS & BUDGET
- Execution Budget: максимум 25 tool calls

## 📁 ЦІЛЬОВІ ФАЙЛИ
- [NEW] apps/web/src/onboarding.tsx

## ✅ DEFINITION OF DONE (DoD)
- Все готово.
"""
    assert should_auto_spec(structured) is False


def test_extract_task_title():
    raw = "Герич, будь ласка зроби повний аудит нашої архітектури та запропонуй покращення"
    title = extract_task_title(raw)
    assert "аудит нашої архітектури" in title.lower()
    assert not title.lower().startswith("герич")


def test_get_next_slice_number():
    slice_num = get_next_slice_number()
    assert isinstance(slice_num, str)
    assert len(slice_num.split(".")) >= 2


def test_evidence_planner_classification():
    obs = classify_statement("Файл core/orchestrator/task_triage.py існує та має розмір 12 KB")
    assert obs == EpistemicStatus.OBSERVED

    hyp = classify_statement("Можливо витік пам'яті виникає через незвільнені з'єднання")
    assert hyp == EpistemicStatus.HYPOTHESIS

    inf = classify_statement("Архітектура передбачає відокремлення шару збереження від бізнес-логіки")
    assert inf == EpistemicStatus.INFERRED


def test_evidence_planner_generation_and_execution():
    query = """
    - Файл core/orchestrator/task_triage.py існує
    - Тести pytest повинні пройти успішно
    """
    plan = generate_evidence_plan(query, target_files=["core/orchestrator/task_triage.py"])
    assert plan["total_probes"] >= 2
    assert "probes" in plan

    exec_res = execute_evidence_plan(plan)
    assert "total_probes" in exec_res
    assert exec_res["verified_probes"] >= 1


def test_risk_gate_assessment():
    low_risk = assess_risk("Зроби аудит коду та виведи звіт", target_files=["tests/unit/test_sample.py"])
    assert low_risk["risk_level"] == RiskLevel.LOW.value
    assert low_risk["requires_approval"] is False

    high_risk = assess_risk("Видалити всі застарілі таблиці та drop database", target_files=[".env", "core/SOUL.md"])
    assert high_risk["risk_level"] == RiskLevel.HIGH.value
    assert high_risk["requires_approval"] is True
    assert high_risk["backup_required"] is True
    assert len(high_risk["detected_high_risk_patterns"]) >= 1


def test_risk_gate_backup_snapshot(tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("critical data", encoding="utf-8")
    snap_dir = tmp_path / "snapshots"

    manifest = create_backup_snapshot([str(test_file)], snapshot_dir=str(snap_dir))
    assert manifest["files_count"] == 1
    assert Path(manifest["backed_up_files"][0]).exists()


def test_github_research_license_classification():
    mit = classify_license("MIT")
    assert mit["legal_track"] == LegalTrack.DIRECT.value

    gpl = classify_license("GPL-3.0")
    assert gpl["legal_track"] == LegalTrack.CLEAN_ROOM.value


def test_github_research_repo_analysis():
    res = analyze_github_repo("langchain-ai/langgraph")
    assert "langchain-ai/langgraph" in res["repo"]
    assert "patterns" in res
    assert "applicability" in res
    assert res["legal_track"] in (LegalTrack.DIRECT.value, LegalTrack.CLEAN_ROOM.value)


def test_auto_generate_task_spec_structure_with_all_gates():
    query = "Герич, зроби аудит архітектури та досліди репозиторій https://github.com/langchain-ai/langgraph"
    spec = auto_generate_task_spec(query, slice_number="13.2")

    # Mandatory Sections
    assert "# 🎯 СЛАЙС 13.2:" in spec
    assert "## 📌 ЦІЛЬОВА ДИРЕКТИВА" in spec
    assert "## 🔒 PRECONDITIONS & BUDGET" in spec
    assert "максимум 25 tool calls на слайс" in spec
    assert "## 📁 ЦІЛЬОВІ ФАЙЛИ" in spec
    assert "## 🛡️ ОЦІНКА РИЗИКІВ ТА ЗАПОБІЖНИКИ (RISK GATE)" in spec
    assert "## 🔬 ПЛАН ЗБОРУ ЕМПІРИЧНИХ ДОКАЗІВ (EVIDENCE PLANNER)" in spec
    assert "## 🧬 SOTA GITHUB ДОСЛІДЖЕННЯ & TWO-TRACK ЛІЦЕНЗІЯ" in spec
    assert "## 📋 ТЕХНІЧНІ ВИМОГИ" in spec
    assert "## ✅ DEFINITION OF DONE (DoD)" in spec
    assert "## 🔍 КОМАНДА ВЕРИФІКАЦІЇ" in spec
    assert "## 🚀 РЕЖИМ ВИКОНАННЯ" in spec
    assert "## 🛑 BLOCKED RULE" in spec
    assert "## 📤 REQUIRED REPORT" in spec
    assert "## 🧠 STEP 0: TRIAGE PROTOCOL (MANDATORY)" in spec
    assert "## ⚠️ CRITICAL: MASE-Compliance" in spec

    # Verify active task spec file persistence
    active_file = HUB_ROOT / ".hermes" / "active_task_spec.md"
    assert active_file.exists()
    assert active_file.read_text(encoding="utf-8") == spec


def test_cli_auto_task_spec():
    cmd = [
        str(HUB_ROOT / "scripts/system/auto_task_spec.py"),
        "Герич, зроби аудит архітектури",
        "--json",
        "--slice", "13.9"
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["should_auto_spec"] is True
    assert data["slice_number"] == "13.9"
    assert "# 🎯 СЛАЙС 13.9:" in data["spec"]


def test_save_task_spec_persistence_and_obsidian_mrh_hygiene():
    sample_spec = "# 🎯 СЛАЙС 14.1: Test Auto Spec Persistence\n\n## 📌 ЦІЛЬОВА ДИРЕКТИВА\nTest directive."
    saved = save_task_spec(sample_spec, title="Test Auto Spec Persistence", slice_number="14.1")

    assert "active_spec" in saved
    assert "active_plan" in saved
    assert "canonical_task" in saved
    assert "obsidian_note" in saved

    active_file = HUB_ROOT / saved["active_spec"]
    assert active_file.exists()

    plan_file = HUB_ROOT / saved["active_plan"]
    assert plan_file.exists()

    canonical_file = HUB_ROOT / saved["canonical_task"]
    assert canonical_file.exists()
    assert sample_spec in canonical_file.read_text(encoding="utf-8")

    obsidian_file = HUB_ROOT / saved["obsidian_note"]
    assert obsidian_file.exists()
    obs_text = obsidian_file.read_text(encoding="utf-8")
    # Verify Obsidian MRH Hygiene: Frontmatter first, muted HTML comment block second
    assert obs_text.startswith("---\nnode_id:")
    assert "<!--\n# --- DNK-MRH-HEADER ---" in obs_text
    assert "# --- END DNK-MRH-HEADER ---\n-->" in obs_text
    # Ensure no raw unmuted H1 MRH header at line 1
    assert not obs_text.startswith("# --- DNK-MRH-HEADER ---")

