# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_repo_map_enhancements.py"
# purpose: "Unit tests for enhanced repo_map AST symbol call graph and caller resolution."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from scripts.system.repo_map import find_symbol, find_callers, resolve_symbol_graph
from core.hermes_agent.tools.dnk_repo_map_tool import dnk_resolve_symbol
import json


def test_find_symbol_definition():
    defs = find_symbol("DNAAssimilationEngine")
    assert len(defs) >= 1
    assert any(d["name"] == "DNAAssimilationEngine" and d["kind"] == "class" for d in defs)


def test_find_callers_and_references():
    calls = find_callers("DNAAssimilationEngine")
    assert isinstance(calls, list)
    assert len(calls) >= 1
    assert any("test_dna_assimilation.py" in c["file"] or "core" in c["file"] for c in calls)


def test_resolve_symbol_graph():
    graph = resolve_symbol_graph("DNAAssimilationEngine")
    assert graph["symbol"] == "DNAAssimilationEngine"
    assert graph["definition_count"] >= 1
    assert graph["call_count"] >= 1
    assert isinstance(graph["callers_by_file"], dict)


def test_dnk_resolve_symbol_with_calls():
    res_raw = dnk_resolve_symbol("DNAAssimilationEngine", include_calls=True)
    res = json.loads(res_raw)
    assert res["status"] == "success"
    assert "graph" in res
    assert res["graph"]["symbol"] == "DNAAssimilationEngine"
    assert res["graph"]["definition_count"] >= 1
