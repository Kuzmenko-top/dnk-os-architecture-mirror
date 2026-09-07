# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_dnk_assimilate_real.py"
# purpose: "Verification test suite for live dnk_assimilate_repo tool with GitHub API and Swarm routing."
# author: "DNK-e.com Maksym & Antigravity"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

import os
import json
import pytest
from core.hermes_agent.tools.dnk_assimilate_tool import (
    dnk_assimilate_repo,
    _resolve_target_swarm_worker,
    _parse_readme_insights,
)


def test_swarm_worker_routing_domains():
    """Verify intelligent Swarm capability routing across diverse engineering domains."""
    # Video / Media domain
    worker_video, comp_video, _ = _resolve_target_swarm_worker(
        "GVCLab/PersonaLive", "Expressive Portrait Animation", ["video-generation", "avatar"], "Python"
    )
    assert worker_video == "dnk_video_ai_creator"
    assert "video" in comp_video

    # Canvas / Visual UI domain
    worker_canvas, comp_canvas, _ = _resolve_target_swarm_worker(
        "xyflow/xyflow", "React Flow and spatial canvas library", ["canvas", "diagram"], "TypeScript"
    )
    assert worker_canvas == "gerych_builder"
    assert "canvas" in comp_canvas

    # Shopify / E-Com domain
    worker_shopify, comp_shopify, _ = _resolve_target_swarm_worker(
        "shopify/theme-tools", "Shopify Liquid templates and storefront extensions", ["liquid", "checkout"], "Ruby"
    )
    assert worker_shopify == "dnk_shopify"
    assert "shopify" in comp_shopify or "ecom" in comp_shopify

    # Backend / API domain
    worker_backend, comp_backend, _ = _resolve_target_swarm_worker(
        "tiangolo/fastapi", "FastAPI framework, high performance, easy to learn", ["api", "database"], "Python"
    )
    assert worker_backend == "dnk_dev_fullstack"
    assert "api" in comp_backend or "core" in comp_backend


def test_readme_parsing():
    """Verify parsing of real README markdown snippets."""
    sample_readme = """
# Awesome Engine
A revolutionary streaming media engine for low latency generation.

## Installation
```bash
pip install awesome-engine
```

## Features
- Ultra-low latency pipeline under 30ms
- Real-time keyframe memory caching
- Modular bidirectional WebSocket gateway
"""
    insights = _parse_readme_insights(sample_readme)
    assert "streaming media engine" in insights["summary"]
    assert "pip install awesome-engine" in insights["install_cmd"]
    assert len(insights["highlights"]) >= 2
    assert any("latency" in h for h in insights["highlights"])


def test_dnk_assimilate_repo_permissive_track():
    """Verify end-to-end execution of dnk_assimilate_repo on a permissive repo."""
    res_str = dnk_assimilate_repo(repo_url="GVCLab/PersonaLive")
    res = json.loads(res_str)

    assert res["status"] == "success"
    assert res["repo"] == "GVCLab/PersonaLive"
    assert res["license"] == "APACHE-2.0"
    assert res["track"] == "Direct Template Assimilation"
    assert res["target_worker"] == "dnk_video_ai_creator"
    assert os.path.exists(res["report_file"])
    assert os.path.exists(res["ki_card"])

    with open(res["report_file"], "r", encoding="utf-8") as f:
        content = f.read()
        assert "DNK-MRH-HEADER" in content
        assert "Direct Template Assimilation" in content
        assert "dnk_video_ai_creator" in content
        assert "⭐" in content


def test_dnk_assimilate_repo_copyleft_track():
    """Verify end-to-end execution on copyleft repo routes to Clean-Room track."""
    res_str = dnk_assimilate_repo(repo_url="plannotator/artifact-server")
    res = json.loads(res_str)

    assert res["status"] == "success"
    assert res["license"] == "AGPL-3.0"
    assert res["track"] == "Reverse Engineering Synthesis"
    assert os.path.exists(res["report_file"])

    with open(res["report_file"], "r", encoding="utf-8") as f:
        content = f.read()
        assert "Clean-Room Reverse Engineering" in content
