# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_lazy_tool_loader.py"
# purpose: "Unit tests for LazyToolLoader on-demand schema loader."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from core.orchestrator.lazy_tool_loader import LazyToolLoader, ToolSpec

# Mock registry for tests
tool_registry = {
    "file.read": {
        "name": "file.read",
        "description": "Reads file contents",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}},
    },
    "terminal.run": {
        "name": "terminal.run",
        "description": "Runs shell command",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}},
    },
    "shopify.validate_liquid": {
        "name": "shopify.validate_liquid",
        "description": "Validates liquid syntax",
        "parameters": {"type": "object", "properties": {"content_or_path": {"type": "string"}}},
    },
}


def test_lazy_loader_initialization():
    loader = LazyToolLoader(tool_registry)
    assert len(loader.loaded_tools) == 0  # Nothing loaded yet


def test_lazy_loader_get_tool():
    loader = LazyToolLoader(tool_registry)
    loader.set_enabled_tools(["file.read", "terminal.run"])

    # Enabled tool → should load
    tool = loader.get_tool("file.read")
    assert tool is not None
    assert "file.read" in loader.loaded_tools

    # Disabled tool → should return None
    tool = loader.get_tool("shopify.validate_liquid")
    assert tool is None


def test_lazy_loader_summary():
    loader = LazyToolLoader(tool_registry)
    loader.set_enabled_tools(["file.read", "terminal.run"])

    summary = loader.get_available_tools_summary()
    assert "file.read" in summary
    assert "terminal.run" in summary
    assert len(summary.split()) < 100  # ~500 токенів max


def test_lazy_loader_get_tool_schema():
    loader = LazyToolLoader(tool_registry)
    loader.set_enabled_tools(["terminal.run"])
    schema = loader.get_tool_schema("terminal.run")
    assert schema is not None
    assert schema["name"] == "terminal.run"
    assert loader.get_tool_schema("unknown_tool") is None


def test_lazy_loader_default_registry():
    loader = LazyToolLoader()
    loader.set_enabled_tools(["file.read", "orch.triage"])
    tool = loader.get_tool("file.read")
    assert tool is not None
    summary = loader.get_available_tools_summary()
    assert "file.read" in summary
    assert "orch.triage" in summary
