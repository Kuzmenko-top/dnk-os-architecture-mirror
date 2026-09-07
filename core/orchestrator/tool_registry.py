# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/tool_registry.py"
# purpose: "Centralized SSOT Tool Registry and Schema Specifications for MCP Slim Guard."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any
from core.orchestrator.tool_aliases import TOOL_REGISTRY as ALIAS_TOOL_REGISTRY

# Standardized TOOL_REGISTRY with full parameter JSON schemas
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "file.read": {
        "name": "file.read",
        "alias": "file.read",
        "description": "Reads file content with line numbers and pagination",
        "domain": "system",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file"},
                "offset": {"type": "integer", "description": "Starting line number"},
                "limit": {"type": "integer", "description": "Maximum number of lines"},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    "file.write": {
        "name": "file.write",
        "alias": "file.write",
        "description": "Writes content to file",
        "domain": "system",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    "mock.large_tool": {
        "name": "mock.large_tool",
        "alias": "mock.large_tool",
        "description": "Returns large output exceeding 3k chars for sidecar paging testing",
        "domain": "test",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        },
    },
    "dnk_shopify_validate_liquid": {
        "name": "dnk_shopify_validate_liquid",
        "alias": "shopify.validate_liquid",
        "description": "Validates Liquid template syntax, schema JSON, and tag balance for Shopify themes",
        "domain": "dnk_shopify",
        "parameters": {
            "type": "object",
            "properties": {
                "content_or_path": {"type": "string", "description": "Liquid source code or relative path"},
                "content": {"type": "string", "description": "Liquid source code"},
            },
            "additionalProperties": True,
        },
    },
    "dnk_video_generate": {
        "name": "dnk_video_generate",
        "alias": "video.generate",
        "description": "Generates video composition from script using Remotion and FFmpeg",
        "domain": "dnk_media",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Video title"},
                "duration_seconds": {"type": "integer", "description": "Duration in seconds"},
            },
            "additionalProperties": True,
        },
    },
    "dnk_video_generate_composition": {
        "name": "dnk_video_generate_composition",
        "alias": "video.generate",
        "description": "Synthesizes programmatic Remotion/FrameCN video composition for product marketing",
        "domain": "dnk_media",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Video headline or product title"},
                "duration_seconds": {"type": "integer", "description": "Duration in seconds"},
                "format_type": {"type": "string", "description": "Aspect ratio format"},
            },
            "required": ["title"],
            "additionalProperties": True,
        },
    },
    "canvas.sync": {
        "name": "canvas.sync",
        "alias": "canvas.sync",
        "description": "Synchronizes and merges canvas graph nodes and state",
        "domain": "dnk_canvas",
        "parameters": {
            "type": "object",
            "properties": {
                "canvas_id": {"type": "string"},
            },
            "additionalProperties": True,
        },
    },
    "canvas.merge": {
        "name": "canvas.merge",
        "alias": "canvas.merge",
        "description": "Merges operational changes in Canvas with OCC conflict resolution",
        "domain": "dnk_canvas",
        "parameters": {
            "type": "object",
            "properties": {
                "base_state": {"type": "object"},
                "current_state": {"type": "object"},
            },
            "additionalProperties": True,
        },
    },
    "dnk_workspace_occ_merge": {
        "name": "dnk_workspace_occ_merge",
        "alias": "canvas.merge",
        "description": "Performs an OCC 3-way structural merge on multi-user Canvas graph mutations",
        "domain": "dnk_canvas",
        "parameters": {
            "type": "object",
            "properties": {
                "base_state_json": {"type": "string"},
                "current_state_json": {"type": "string"},
                "incoming_state_json": {"type": "string"},
            },
            "required": ["base_state_json", "current_state_json", "incoming_state_json"],
            "additionalProperties": True,
        },
    },
    "dnk_triage_task": {
        "name": "dnk_triage_task",
        "alias": "orch.triage",
        "description": "Step 0 Autonomous Complexity Classifier for Gerych Prime (SOLO, SWARM_PARALLEL, SWARM_SEQUENTIAL)",
        "domain": "dnk_orchestration",
        "parameters": {
            "type": "object",
            "properties": {
                "goal_or_prompt": {"type": "string"},
            },
            "required": ["goal_or_prompt"],
            "additionalProperties": True,
        },
    },
    "dnk_resolve_symbol": {
        "name": "dnk_resolve_symbol",
        "alias": "code.resolve_symbol",
        "description": "Instantly locate where any class, function, interface, type, or constant is defined in repository",
        "domain": "dnk_introspection",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
            },
            "required": ["symbol"],
            "additionalProperties": True,
        },
    },
    "terminal.run": {
        "name": "terminal.run",
        "alias": "terminal.run",
        "description": "Executes shell commands in Linux/macOS environment",
        "domain": "system",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
            },
            "required": ["command"],
            "additionalProperties": True,
        },
    },
}

# Integrate entries from ALIAS_TOOL_REGISTRY for complete coverage
for _key, _meta in ALIAS_TOOL_REGISTRY.items():
    if _meta.name not in TOOL_REGISTRY:
        TOOL_REGISTRY[_meta.name] = {
            "name": _meta.name,
            "alias": _meta.alias,
            "description": _meta.summary,
            "domain": _meta.domain,
            "parameters": {
                "type": "object",
                "properties": {p: {"type": "string"} for p in _meta.key_params},
                "required": _meta.key_params,
                "additionalProperties": True,
            },
        }
    if _meta.alias not in TOOL_REGISTRY:
        TOOL_REGISTRY[_meta.alias] = {
            "name": _meta.alias,
            "alias": _meta.alias,
            "description": _meta.summary,
            "domain": _meta.domain,
            "parameters": {
                "type": "object",
                "properties": {p: {"type": "string"} for p in _meta.key_params},
                "required": _meta.key_params,
                "additionalProperties": True,
            },
        }
