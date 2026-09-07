# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_sota_assimilation_two_track.py"
# purpose: "Comprehensive verification suite for Vector 4 Two-Track SOTA Repository Assimilation Pipeline (Scout, Two-Track License Audit, Skill Gen, Obsidian, TaskDNA)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity"
# --- END DNK-MRH-HEADER ---

import json
import pytest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.orchestrator.sota_scout import (
    SOTAScoutEngine,
    AssimilationTrack,
    ScoutJobStatus,
    sanitize_code_snippet,
)
from core.hermes_agent.tools.dnk_assimilate_tool import dnk_assimilate_repo


@pytest.fixture
def temp_scout_env(tmp_path):
    """Provides an isolated environment for SOTAScoutEngine testing."""
    cache_file = tmp_path / "test_cache.json"
    queue_file = tmp_path / "test_queue.json"
    engine = SOTAScoutEngine(
        hub_root=tmp_path,
        cache_file=cache_file,
        queue_file=queue_file,
    )
    return engine, tmp_path


def test_sanitize_code_snippet():
    """Verify code sanitization enforces MRH header, relative paths, and token redaction."""
    raw_code = (
        "# Some random script\n"
        "import os\n"
        "GITHUB_TOKEN = 'ghp_12345678901234567890123456789012'\n"
        "CACHE_DIR = '/Users/kuzmenko.top/Kuzmenko/MY_LIFE_WORK/DNK_HUB/data/cache'\n"
        "def run():\n"
        "    return True\n"
    )

    sanitized = sanitize_code_snippet(
        raw_code,
        file_rel_path="core/modules/test_mod.py",
        purpose="Testing sanitization engine"
    )

    # 1. Valid MRH Header
    assert "# --- DNK-MRH-HEADER ---" in sanitized
    assert '# mrh_id: "core/modules/test_mod.py"' in sanitized
    assert '# purpose: "Testing sanitization engine"' in sanitized
    assert "# --- END DNK-MRH-HEADER ---" in sanitized

    # 2. Secret Redaction
    assert "ghp_" not in sanitized
    assert "[REDACTED]" in sanitized

    # 3. Absolute path normalization
    assert "/Users/kuzmenko.top" not in sanitized
    assert "./" in sanitized or "../" in sanitized


def test_license_audit_two_track(temp_scout_env):
    """Verify license categorization into Track 1 (Permissive) and Track 2 (Clean-Room)."""
    engine, _ = temp_scout_env

    # Track 1 Permissive
    for lic in ["MIT", "Apache-2.0", "bsd-3-clause", "ISC"]:
        track, name, boundary = engine.audit_license_two_track({"key": lic, "name": lic})
        assert track == AssimilationTrack.TRACK_1_PERMISSIVE
        assert any("Direct architectural template" in b for b in boundary)

    # Track 2 Restrictive / Copyleft
    for lic in ["GPL-3.0", "agpl-v3", "LGPL-2.1", "SSPL", "BSL-1.1"]:
        track, name, boundary = engine.audit_license_two_track({"key": lic, "name": lic})
        assert track == AssimilationTrack.TRACK_2_CLEAN_ROOM
        assert any("Clean-Room Reverse Engineering" in b for b in boundary)

    # Unknown fallback
    track, name, boundary = engine.audit_license_two_track(None)
    assert track == AssimilationTrack.TRACK_2_CLEAN_ROOM


def test_swarm_routing_logic(temp_scout_env):
    """Verify intelligent mapping to specialized Swarm workers."""
    engine, _ = temp_scout_env

    # 1. Video & Media
    worker, comp, _ = engine.resolve_swarm_routing(
        "video-creator", "Remotion based video synthesis engine", ["video", "remotion", "audio"]
    )
    assert worker == "dnk_video_ai_creator"

    # 2. Canvas & UI
    worker, comp, _ = engine.resolve_swarm_routing(
        "flow-diagram", "Infinite canvas graph editor React Flow", ["canvas", "diagram"]
    )
    assert worker == "gerych_builder"

    # 3. Shopify & Ecom
    worker, comp, _ = engine.resolve_swarm_routing(
        "shopify-theme-kit", "Liquid and checkout extensions for commerce", ["shopify", "liquid"]
    )
    assert worker == "dnk_shopify"

    # 4. Security & Audit
    worker, comp, _ = engine.resolve_swarm_routing(
        "vuln-scanner", "SAST security auditor and red-team scanner", ["security", "audit", "sast"]
    )
    assert worker == "gerych_auditor"

    # 5. Backend / Fullstack
    worker, comp, _ = engine.resolve_swarm_routing(
        "fastapi-orm", "SQLAlchemy 2.0 async postgres pipeline", ["fastapi", "postgres"]
    )
    assert worker == "dnk_dev_fullstack"


def test_full_assimilation_pipeline_track_1(temp_scout_env):
    """Verify end-to-end Track 1 assimilation with all 4 knowledge artifacts created."""
    engine, tmp_path = temp_scout_env

    mock_meta = {
        "name": "PersonaLive",
        "full_name": "GVCLab/PersonaLive",
        "stargazers_count": 1420,
        "language": "Python",
        "description": "High-fidelity Real-time Interactive Video Synthesis and Motion Generation.",
        "license": {"key": "mit", "name": "MIT License"}
    }
    mock_readme = (
        "# PersonaLive\n"
        "Real-time video synthesis and motion generation.\n"
        "## Installation\n"
        "pip install -r requirements.txt\n"
        "## Architecture\n"
        "Streaming video generation pipeline with audio conditioning.\n"
    )

    with patch.object(engine, "fetch_repo_intel", return_value=(mock_meta, mock_readme)):
        result = engine.assimilate(
            repo_url="GVCLab/PersonaLive",
            focus_areas=["streaming", "video", "remotion"],
            generate_skill=True,
            generate_obsidian=True,
            sync_scones=True,
        )

    assert result["status"] == "success"
    assert result["track"] == AssimilationTrack.TRACK_1_PERMISSIVE.value
    assert result["target_worker"] == "dnk_video_ai_creator"

    # 1. Hermes Skill created
    skill_file = tmp_path / result["skill_file"]
    assert skill_file.exists()
    skill_text = skill_file.read_text(encoding="utf-8")
    assert "name: personalive_assimilated" in skill_text
    assert "Quick Recipes" in skill_text
    assert "Pitfalls & Invariants" in skill_text

    # 2. Obsidian Vault Note created per [OBSIDIAN_MRH_HYGIENE]
    obsidian_file = tmp_path / result["obsidian_file"]
    assert obsidian_file.exists()
    obsidian_text = obsidian_file.read_text(encoding="utf-8")
    assert obsidian_text.startswith("---")
    assert "<!-- --- DNK-MRH-HEADER ---" in obsidian_text
    assert "[[000_DNK_HUB_INDEX]]" in obsidian_text
    assert "[[wikilinks]]" in obsidian_text or "[[" in obsidian_text

    # 3. SCONES Memory synced
    assert result["scones_synced"] is True
    scones_file = tmp_path / ".scones" / "sota_memories.json"
    assert scones_file.exists()
    scones_data = json.loads(scones_file.read_text(encoding="utf-8"))
    assert any(m["topic"] == "SOTA_ASSIMILATION_GVCLAB_PERSONALIVE" for m in scones_data)

    # 4. SOTA Digest created
    digest_file = tmp_path / result["digest_file"]
    assert digest_file.exists()

    # 5. TaskDNA generated
    assert result["task_dna"] is not None
    assert result["task_dna"]["assigned_agent"] == "dnk_video_ai_creator"


def test_full_assimilation_pipeline_track_2_clean_room(temp_scout_env):
    """Verify Track 2 Clean-Room isolation for copyleft/GPL repositories."""
    engine, tmp_path = temp_scout_env

    mock_meta = {
        "name": "CopyleftEngine",
        "full_name": "GPLOrg/CopyleftEngine",
        "stargazers_count": 890,
        "language": "TypeScript",
        "description": "GPL-3.0 licensed complex graph visualization canvas engine.",
        "license": {"key": "gpl-3.0", "name": "GNU General Public License v3.0"}
    }
    mock_readme = "# CopyleftEngine\nComplex infinite graph engine under GPL-3.0."

    with patch.object(engine, "fetch_repo_intel", return_value=(mock_meta, mock_readme)):
        result = engine.assimilate(
            repo_url="GPLOrg/CopyleftEngine",
            generate_skill=True,
            generate_obsidian=True,
            sync_scones=True,
        )

    assert result["status"] == "success"
    assert result["track"] == AssimilationTrack.TRACK_2_CLEAN_ROOM.value
    assert "Clean-Room Reverse Engineering" in result["legal_boundary"]

    # Verify Clean-Room Skill notices
    skill_file = tmp_path / result["skill_file"]
    skill_text = skill_file.read_text(encoding="utf-8")
    assert "CLEAN-ROOM REVERSE-ENGINEERING INVARIANT" in skill_text
    assert "Direct code copying is strictly prohibited" in skill_text


def test_scout_queue_lifecycle(temp_scout_env):
    """Verify Scout background queue: enqueue, deduplication, status tracking, process_next."""
    engine, _ = temp_scout_env

    # 1. Enqueue job 1
    job1 = engine.enqueue_job("owner/repo-alpha", focus_areas=["video"], priority=1)
    assert job1["status"] == ScoutJobStatus.PENDING.value
    assert job1["repo_url"] == "owner/repo-alpha"

    # 2. Deduplication check (same pending repo should return existing job)
    job1_dup = engine.enqueue_job("owner/repo-alpha", priority=2)
    assert job1_dup["id"] == job1["id"]

    # 3. Enqueue job 2 with lower priority
    job2 = engine.enqueue_job("owner/repo-beta", priority=10)

    status = engine.get_queue_status()
    assert status["total_jobs"] == 2
    assert status["by_status"]["pending"] == 2

    # 4. Mock assimilation and process next job (should pick highest priority: job1 with priority 1)
    with patch.object(engine, "assimilate", return_value={"status": "success", "repo": "owner/repo-alpha"}):
        processed = engine.process_next_job()
        assert processed["status"] == "success"
        assert processed["job_id"] == job1["id"]

    # Check updated queue status
    status_after = engine.get_queue_status()
    assert status_after["by_status"]["assimilated"] == 1
    assert status_after["by_status"]["pending"] == 1


def test_dnk_assimilate_tool_integration():
    """Verify dnk_assimilate_repo tool executes with SOTAScoutEngine enhancements."""
    mock_meta = {
        "name": "AutoCanvas",
        "full_name": "TestOrg/AutoCanvas",
        "stargazers_count": 320,
        "language": "TypeScript",
        "description": "Infinite canvas workspace engine for multi-agent graphs.",
        "license": {"key": "mit", "name": "MIT License"}
    }
    mock_readme = "# AutoCanvas\nModular canvas graph workspace."

    res = None
    try:
        with patch("core.hermes_agent.tools.dnk_assimilate_tool._fetch_github_repo_data", return_value=(mock_meta, mock_readme)):
            resp_str = dnk_assimilate_repo(
                repo_url="TestOrg/AutoCanvas",
                focus_areas=["canvas", "graph"],
                workspace_id="ws-alpha-001"
            )
            res = json.loads(resp_str)
            assert res["status"] == "success"
            assert res["repo"] == "TestOrg/AutoCanvas"
            assert res["target_worker"] == "gerych_builder"
            assert res["track"] == "Direct Template Assimilation"
            assert res.get("skill_file") is not None
            assert res.get("obsidian_file") is not None
            assert res.get("scones_synced") is True
            assert res.get("task_dna") is not None
    finally:
        if "res" in locals() and isinstance(res, dict) and res.get("obsidian_file"):
            try:
                Path(res["obsidian_file"]).unlink(missing_ok=True)
            except Exception:
                pass
        for p in [
            Path("skills/autocanvas_assimilated"),
            Path("docs/notes/016_autocanvas_sota_assimilation_audit.md"),
            Path("docs/tech/sota_assimilation/SOTA_AUTOCANVAS_ASSIMILATION.md"),
            Path("docs/tech/sota_assimilation/testorg_autocanvas.md")
        ]:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            elif p.is_file():
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
