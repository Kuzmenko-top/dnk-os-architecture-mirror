# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_mcp_slim_guard.py"
# purpose: "Unit tests verifying MCPSlimGuard 3 meta-tools, argument validation, sidecar offloading, and chunking."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import pytest
from core.orchestrator.mcp_slim_guard import MCPSlimGuard


@pytest.fixture
def sample_registry():
    return {
        "dnk_shopify_validate_liquid": {
            "name": "dnk_shopify_validate_liquid",
            "description": "Validates and lints Shopify Liquid templates, sections, and snippets syntax.",
            "parameters": {
                "type": "object",
                "properties": {"file_path": {"type": "string"}},
                "required": ["file_path"],
            },
        },
        "file.read": {
            "name": "file.read",
            "description": "Reads lines with pagination from file.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        },
        "mock.large_tool": {
            "name": "mock.large_tool",
            "description": "Returns mock large payload",
            "parameters": {"type": "object", "properties": {}},
        },
    }


def test_find_tool_semantic_search(sample_registry):
    mcp = MCPSlimGuard(sample_registry)
    results = mcp.find_tool("Shopify Liquid validation")
    assert "dnk_shopify_validate_liquid" in results
    assert len(results) <= 5


def test_call_tool_validation(sample_registry):
    mcp = MCPSlimGuard(sample_registry)

    # Valid call
    result = mcp.call_tool("file.read", {"path": "test.txt"})
    assert "content" in result

    # Invalid args (missing required 'path' and extra invalid_arg)
    try:
        mcp.call_tool("file.read", {"invalid_arg": "value"})
        assert False, "Should raise ValueError for invalid arguments"
    except ValueError:
        pass


def test_call_tool_sidecar(sample_registry):
    mcp = MCPSlimGuard(sample_registry)

    # Large result (> 3k)
    result = mcp.call_tool("mock.large_tool", {})
    assert "result_ref:" in result
    assert "sidecar-" in result


def test_read_result_chunking(sample_registry):
    mcp = MCPSlimGuard(sample_registry)

    # Save large result to sidecar
    ref = mcp._save_to_sidecar("x" * 5000)

    # Read chunk 1
    chunk1 = mcp.read_result(ref, chunk_size=1000)
    assert "[Chunk 1]" in chunk1
    assert len(chunk1) < 1500  # Header + 1000 chars

    # Read chunk 2
    chunk2 = mcp.read_result(ref, chunk_size=1000, offset=1000)
    assert "[Chunk 2]" in chunk2


def test_meta_tools_schema(sample_registry):
    mcp = MCPSlimGuard(sample_registry)
    schema = mcp.get_meta_tools_schema()

    assert len(schema["tools"]) == 3
    tool_names = [t["name"] for t in schema["tools"]]
    assert "find_tool" in tool_names
    assert "call_tool" in tool_names
    assert "read_result" in tool_names
