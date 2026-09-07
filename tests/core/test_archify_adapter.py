# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_archify_adapter.py"
# purpose: "Unit & Integration tests for DNKArchifyAdapter."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

import os
import tempfile
import pytest
from core.adapters.dnk_archify_adapter import DNKArchifyAdapter, ArchifyDiagramType


def test_archify_engine_ready():
    adapter = DNKArchifyAdapter()
    assert adapter.is_engine_ready() is True


def test_render_swarm_workflow_diagram():
    adapter = DNKArchifyAdapter()
    preset = adapter.build_swarm_workflow_preset()

    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "swarm_test.html")
        rendered_path = adapter.render_diagram(ArchifyDiagramType.WORKFLOW, preset, out_file)
        
        assert os.path.exists(rendered_path)
        assert os.path.getsize(rendered_path) > 1000  # Standalone HTML is substantial
        
        with open(rendered_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content or "<html" in content
            assert "DNK OS 14-Agent Swarm Execution Workflow" in content
            assert "gerych_prime" in content or "Gerych Prime" in content


def test_zero_disk_io_in_memory_streaming():
    adapter = DNKArchifyAdapter()
    preset = adapter.build_swarm_workflow_preset()
    rendered_html = adapter.render_diagram(ArchifyDiagramType.WORKFLOW, preset)
    assert isinstance(rendered_html, str)
    assert len(rendered_html) > 50000
    assert "<!DOCTYPE html>" in rendered_html or "<html" in rendered_html
    assert "DNK OS 14-Agent Swarm Execution Workflow" in rendered_html


def test_generate_live_repo_architecture():
    adapter = DNKArchifyAdapter()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "live_arch.html")
        res = adapter.generate_live_repo_architecture(repo_root=".", output_path=out_file)

        assert "metrics" in res
        metrics = res["metrics"]
        assert metrics["routers_count"] > 10
        assert metrics["adapters_count"] > 5
        assert metrics["swarm_agents_count"] == 14
        assert os.path.exists(res["rendered_path"])
        assert os.path.getsize(res["rendered_path"]) > 10000


def test_validate_diagram_spec():
    adapter = DNKArchifyAdapter()
    preset = adapter.build_swarm_workflow_preset()
    validation = adapter.validate_diagram(ArchifyDiagramType.WORKFLOW, preset)
    assert validation.get("ok") is True
