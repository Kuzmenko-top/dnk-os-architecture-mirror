# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_dna_assimilation.py"
# purpose: "Comprehensive Unit and Integration Tests for DNAAssimilationEngine."
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
from core.dna_assimilation import DNAAssimilationEngine

TEST_OUTPUT_DIR = "test_run_dna_temp"

@pytest.fixture(autouse=True)
def run_around_tests() -> Generator[None, None, None]:
    """Cleans and scaffolds the temporary test output directory."""
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)


def test_dna_search():
    engine = DNAAssimilationEngine(output_dir=TEST_OUTPUT_DIR)
    
    # Test search with fallback catalog
    results = engine.search_sota("hermes execution")
    assert len(results) > 0
    assert any("hermes" in r["full_name"].lower() for r in results)

    # Test query that has no direct match falls back gracefully
    results_all = engine.search_sota("unmatched query string")
    assert len(results_all) == 2


def test_dna_license_audit():
    engine = DNAAssimilationEngine(output_dir=TEST_OUTPUT_DIR)

    # Permissive case
    lic_mit, track_mit, notes_mit = engine.audit_license({"license": "MIT"})
    assert lic_mit == "MIT"
    assert track_mit == "Direct Template Assimilation"
    assert any("commercial-safe" in n for n in notes_mit)

    # Restrictive GPL case
    lic_gpl, track_gpl, notes_gpl = engine.audit_license({"license": "GPL-3.0"})
    assert lic_gpl == "GPL-3.0"
    assert track_gpl == "Reverse Engineering Synthesis"
    assert any("STRICTLY FORBIDDEN" in n for n in notes_gpl)

    # Unknown case
    lic_unk, track_unk, notes_unk = engine.audit_license({"license": "CUSTOM_PROPRIETARY"})
    assert lic_unk == "CUSTOM_PROPRIETARY"
    assert track_unk == "Reverse Engineering Synthesis"
    assert any("Clean-Room" in n for n in notes_unk)

    # Fast GitHub MCP inspection when license is Unknown
    def mock_mcp(tool_name, args):
        if tool_name == "mcp__github__get_file_contents" and args.get("path") == "LICENSE":
            return {"content": "Apache License Version 2.0, January 2004"}
        return None

    engine_mcp = DNAAssimilationEngine(output_dir=TEST_OUTPUT_DIR, mcp_call_fn=mock_mcp)
    lic_mcp, track_mcp, notes_mcp = engine_mcp.audit_license({"full_name": "owner/repo", "license": "Unknown"})
    assert lic_mcp == "APACHE-2.0"
    assert track_mcp == "Direct Template Assimilation"


def test_dna_extract_patterns():
    engine = DNAAssimilationEngine(output_dir=TEST_OUTPUT_DIR)
    dossier = engine.extract_patterns("nousresearch/hermes-agent")
    assert dossier["repo_name"] == "nousresearch/hermes-agent"
    assert "primary_stack" in dossier
    assert len(dossier["key_features"]) > 0


def test_dna_ingest_ki():
    engine = DNAAssimilationEngine(output_dir=TEST_OUTPUT_DIR)
    dossier = {
        "primary_stack": "Python / FastAPI",
        "architecture": "Clean Layered",
        "key_features": ["Robust parsing", "Logging"],
        "schemas": {"TestSchema": {"id": "int"}}
    }
    
    # Ingest Permissive track
    path_mit = engine.ingest_ki("test/repo-mit", "MIT", "Direct Template Assimilation", dossier)
    assert os.path.exists(path_mit)
    with open(path_mit, "r", encoding="utf-8") as f:
        content = f.read()
        assert "DNK-MRH-HEADER" in content
        assert "Evolution Track" in content
        assert "Direct Template Assimilation" in content
        assert "Permissive License" in content

    # Ingest Restrictive track
    path_gpl = engine.ingest_ki("test/repo-gpl", "GPL-3.0", "Reverse Engineering Synthesis", dossier)
    assert os.path.exists(path_gpl)
    with open(path_gpl, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Evolution Track" in content
        assert "Reverse Engineering Synthesis" in content
        assert "Clean-Room Design" in content


def test_dna_full_cycle():
    engine = DNAAssimilationEngine(output_dir=TEST_OUTPUT_DIR)
    
    res = engine.run_full_assimilation_cycle("social scheduler", "agentic-signal/postiz-gpl")
    assert res["repo_name"] == "agentic-signal/postiz-gpl"
    assert res["license"] == "GPL-3.0"
    assert res["track"] == "Reverse Engineering Synthesis"
    assert os.path.exists(res["knowledge_card_path"])


def test_dna_mcp_mock_calls():
    # Verify mock function is called successfully
    called_tools = []
    def dummy_mcp_call(tool_name: str, args: dict):
        called_tools.append(tool_name)
        if tool_name == "mcp__git_research__semantic_search_repos":
            return {"repos": [{"full_name": "mcp/repo", "license": "MIT", "description": "MCP search"}]}
        elif tool_name == "mcp__git_research__check_license_compatibility":
            return {"safe_for_commercial_saas": True, "warnings": ["mcp warning"]}
        elif tool_name == "mcp__git_research__get_repo_dossier":
            return {"repo_name": "mcp/repo", "key_features": ["mcp feat"]}
        return None

    engine = DNAAssimilationEngine(output_dir=TEST_OUTPUT_DIR, mcp_call_fn=dummy_mcp_call)
    res = engine.run_full_assimilation_cycle("mcp query", "mcp/repo")
    
    assert "mcp__git_research__semantic_search_repos" in called_tools
    assert "mcp__git_research__check_license_compatibility" in called_tools
    assert "mcp__git_research__get_repo_dossier" in called_tools
    assert res["repo_name"] == "mcp/repo"
    assert res["track"] == "Direct Template Assimilation"
