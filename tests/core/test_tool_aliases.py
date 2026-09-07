# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_tool_aliases.py"
# purpose: "Unit tests for TOOL_ALIASES dictionary and summary formatters."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from core.orchestrator.tool_aliases import (
    TOOL_ALIASES,
    format_tool_summary,
    format_all_tool_summaries,
    resolve_tool_name,
)


def test_tool_aliases_format():
    assert "dnk_shopify_validate_liquid" in TOOL_ALIASES
    assert TOOL_ALIASES["dnk_shopify_validate_liquid"]["alias"] == "shopify.validate_liquid"
    assert "Validates Liquid" in TOOL_ALIASES["dnk_shopify_validate_liquid"]["summary"]


def test_format_tool_summary():
    summary = format_tool_summary("dnk_shopify_validate_liquid")
    assert "shopify.validate_liquid" in summary
    assert "Validates Liquid" in summary


def test_format_all_tool_summaries():
    enabled = ["dnk_shopify_validate_liquid", "file.read", "terminal.run"]
    summary = format_all_tool_summaries(enabled)

    assert "shopify.validate_liquid" in summary
    assert "file.read" in summary
    assert "terminal.run" in summary
    assert len(summary.split()) < 200  # ~500 токенів max


def test_fallback_unregistered_tool():
    summary = format_tool_summary("unknown_custom_tool_xyz")
    assert "unknown_custom_tool_xyz" in summary
    assert "no summary available" in summary


def test_resolve_tool_name_backwards_compat():
    assert resolve_tool_name("file.read") == "read_file"
    assert resolve_tool_name("shopify.validate_liquid") == "dnk_shopify_validate_liquid"
    assert resolve_tool_name("video.generate") == "dnk_video_generate_composition"
