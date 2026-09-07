# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_task_triage.py"
# purpose: "Unit tests for autonomous Task Triage Engine (task_triage.py) covering SOLO, SWARM_PARALLEL, and SWARM_SEQUENTIAL modes."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import pytest
from core.orchestrator.task_triage import dnk_triage_task, extract_file_paths, detect_domains, count_stages_or_slices


def test_solo_mode_single_file():
    """Single-file bugfix should route to SOLO mode."""
    result = dnk_triage_task("Fix typo in core/mindmap/auto_cluster.py")
    assert result.mode == "SOLO"
    assert result.f_files == 1
    assert "gerych_prime" in result.execution_plan[0]["assigned_agent"]


def test_swarm_parallel_cross_domain():
    """Multi-domain task with explicit slices should be SWARM_PARALLEL."""
    prompt = """
    ### СЛАЙС 3.1: Бекенд
    Create core/obsidian/export_canvas.py and apps/api/routers/canvas_v3_ws.py

    ### СЛАЙС 3.2: Фронтенд
    Create apps/web/components/canvas/ObsidianSyncBar.tsx and apps/web/store/canvasStore.ts
    """
    result = dnk_triage_task(prompt)
    assert result.mode in ("SWARM_PARALLEL", "SWARM_SEQUENTIAL")
    assert result.complexity_score > 3
    agents = [s["assigned_agent"] for s in result.execution_plan]
    # Should assign backend to fullstack and frontend to builder
    assert any(a == "dnk_dev_fullstack" for a in agents) or any(a == "gerych_builder" for a in agents)


def test_extract_file_paths():
    """Should correctly extract paths from markdown text."""
    text = "Create core/obsidian/export_canvas.py and apps/web/store/canvasStore.ts"
    paths = extract_file_paths(text)
    assert "core/obsidian/export_canvas.py" in paths
    assert "apps/web/store/canvasStore.ts" in paths


def test_detect_domains_backend():
    """FastAPI and routers should map to backend_api domain."""
    domains = detect_domains("Create FastAPI router in apps/api/routers/test.py", ["apps/api/routers/test.py"])
    assert "backend_api" in domains


def test_detect_domains_frontend():
    """TSX components should map to frontend_canvas domain."""
    domains = detect_domains("Create React component apps/web/components/canvas/MyNode.tsx", ["apps/web/components/canvas/MyNode.tsx"])
    assert "frontend_canvas" in domains


def test_count_stages_with_explicit_slices():
    """Should count and extract named slices correctly."""
    text = """
    ### СЛАЙС 3.1: Backend
    ### СЛАЙС 3.2: Frontend
    ### СЛАЙС 3.3: E2E Tests
    """
    count, slices = count_stages_or_slices(text)
    assert count == 3
    assert len(slices) == 3
    assert slices[0]["slice_id"] == "3-1"


def test_complexity_formula():
    """Verify the C = F + 2D + 3S formula produces correct score."""
    result = dnk_triage_task("""
    ### СЛАЙС 1.1: Backend API
    Files: core/obsidian/export_canvas.py, apps/api/routers/canvas_v3_ws.py

    ### СЛАЙС 1.2: Frontend UI
    Files: apps/web/components/canvas/ObsidianSyncBar.tsx, apps/web/store/canvasStore.ts
    """)
    # F=4, D>=2, S=2 → C >= 4 + 4 + 6 = 14
    assert result.complexity_score >= 10
    assert result.mode in ("SWARM_PARALLEL", "SWARM_SEQUENTIAL")


def test_empty_prompt_defaults_to_solo():
    """Empty or whitespace prompt should default to SOLO mode with zero score."""
    result = dnk_triage_task("")
    assert result.mode == "SOLO"
    assert result.complexity_score == 0


def test_qa_auditor_assigned_for_e2e_slices():
    """E2E test / verify slice should assign gerych_auditor."""
    prompt = """
    ### СЛАЙС 3.1: Backend
    core/obsidian/export_canvas.py

    ### СЛАЙС 3.2: E2E тести verify_all.sh tests/canvas/test_obsidian_sync.py
    """
    result = dnk_triage_task(prompt)
    agents = [s["assigned_agent"] for s in result.execution_plan]
    assert "gerych_auditor" in agents


def test_execution_plan_parallel_groups():
    """Plans with 2 domain workers should have parallel_group=1, QA in group=2."""
    prompt = """
    ### СЛАЙС 1: Бекенд
    core/obsidian/export_canvas.py, apps/api/routers/canvas_v3_ws.py

    ### СЛАЙС 2: Фронтенд
    apps/web/components/canvas/ObsidianSyncBar.tsx

    ### СЛАЙС 3: E2E тести + verify_all.sh
    tests/canvas/test_obsidian_sync.py
    """
    result = dnk_triage_task(prompt)
    assert len(result.execution_plan) >= 2
    groups = {s["parallel_group"] for s in result.execution_plan}
    # Should have at least group 1 and group 2
    assert 1 in groups


def test_dynamic_toolset_pruning_backend_solo():
    """Backend-only solo task should prune non-backend toolsets (Context Window Tax mitigation)."""
    prompt = "Fix typo in core/utils/logger.py and run pytest tests/test_logger.py"
    result = dnk_triage_task(prompt)
    assert result.mode == "SOLO"
    assert "file" in result.enabled_toolsets
    assert "terminal" in result.enabled_toolsets
    # Verify non-relevant domain toolsets are pruned into disabled_toolsets
    assert "dnk_shopify" in result.disabled_toolsets
    assert "dnk_media" in result.disabled_toolsets
    assert "dnk_canvas" in result.disabled_toolsets


def test_dynamic_toolset_pruning_swarm_parallel():
    """In SWARM_PARALLEL mode, Gerych Prime stays on core orchestrator toolsets."""
    prompt = """
    Multi-domain task:
    1. apps/api/routers/shopify_auth.py
    2. apps/web/components/CanvasRenderer.tsx
    """
    result = dnk_triage_task(prompt)
    assert result.mode == "SWARM_PARALLEL"
    # Prime remains lean
    assert "dnk_shopify" in result.disabled_toolsets
    assert "dnk_media" in result.disabled_toolsets
    assert "dnk_orchestration" in result.enabled_toolsets

