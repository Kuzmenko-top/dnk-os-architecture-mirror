# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/tool_aliases.py"
# purpose: "Compact tool alias and summary mapping to drastically minimize Context Window Tax."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
Tool Aliases & Compact Summaries.

Eliminates Context Window Tax by mapping 60+ verbose tool names and full JSON
schemas into ultra-dense, token-efficient alias signatures.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set


@dataclass(frozen=True)
class ToolMetadata:
    name: str
    alias: str
    summary: str
    domain: str
    key_params: List[str]


TOOL_REGISTRY: Dict[str, ToolMetadata] = {
    # File Tools
    "read_file": ToolMetadata(
        name="read_file",
        alias="file.read",
        summary="Reads lines with line numbers and pagination",
        domain="file",
        key_params=["path", "offset", "limit"],
    ),
    "write_file": ToolMetadata(
        name="write_file",
        alias="file.write",
        summary="Writes complete file contents, auto-lints",
        domain="file",
        key_params=["path", "content"],
    ),
    "patch": ToolMetadata(
        name="patch",
        alias="file.patch",
        summary="Replaces string in file using 9 fuzzy strategies",
        domain="file",
        key_params=["path", "old_string", "new_string"],
    ),
    "search_files": ToolMetadata(
        name="search_files",
        alias="file.search",
        summary="Searches file contents (regex) or finds paths by glob",
        domain="file",
        key_params=["pattern", "target", "path"],
    ),
    # Terminal & Execution
    "terminal": ToolMetadata(
        name="terminal",
        alias="terminal.run",
        summary="Executes shell command in persistent session",
        domain="terminal",
        key_params=["command", "timeout", "background"],
    ),
    "execute_code": ToolMetadata(
        name="execute_code",
        alias="code.eval",
        summary="Runs multi-step Python logic with tool invocation",
        domain="terminal",
        key_params=["code"],
    ),
    "process": ToolMetadata(
        name="process",
        alias="proc.ctrl",
        summary="Polls, logs, or kills background processes",
        domain="terminal",
        key_params=["action", "session_id"],
    ),
    # Introspection & Code Intel
    "dnk_resolve_symbol": ToolMetadata(
        name="dnk_resolve_symbol",
        alias="code.resolve_symbol",
        summary="Resolves symbol (class/function) location in codebase via AST",
        domain="dnk_introspection",
        key_params=["symbol"],
    ),
    "dnk_find_files": ToolMetadata(
        name="dnk_find_files",
        alias="code.find_files",
        summary="Fast repo path/name fragment search without find",
        domain="dnk_introspection",
        key_params=["pattern"],
    ),
    "dnk_get_architecture_map": ToolMetadata(
        name="dnk_get_architecture_map",
        alias="orch.arch_map",
        summary="SSOT map of apps, services, and core engines",
        domain="dnk_introspection",
        key_params=[],
    ),
    # Swarm & Orchestration
    "dnk_triage_task": ToolMetadata(
        name="dnk_triage_task",
        alias="orch.triage",
        summary="Analyzes task complexity, returns mode (SOLO/SWARM) + execution plan",
        domain="dnk_orchestration",
        key_params=["goal_or_prompt"],
    ),
    "dnk_swarm_dispatch": ToolMetadata(
        name="dnk_swarm_dispatch",
        alias="swarm.dispatch",
        summary="Dispatches task to specialized worker with streaming events",
        domain="dnk_orchestration",
        key_params=["agent", "task_description"],
    ),
    "dnk_swarm_parallel": ToolMetadata(
        name="dnk_swarm_parallel",
        alias="swarm.parallel",
        summary="Executes concurrent multi-agent tasks across domains",
        domain="dnk_orchestration",
        key_params=["tasks_json"],
    ),
    "dnk_swarm_pipeline": ToolMetadata(
        name="dnk_swarm_pipeline",
        alias="swarm.pipeline",
        summary="Runs 4-stage Gerych Swarm pipeline (Prime->Audit)",
        domain="dnk_orchestration",
        key_params=["goal"],
    ),
    "dnk_swarm_status": ToolMetadata(
        name="dnk_swarm_status",
        alias="swarm.status",
        summary="Queries live status/availability of all 14 workers",
        domain="dnk_orchestration",
        key_params=["swarm_id"],
    ),
    "dnk_decompose_task_dna": ToolMetadata(
        name="dnk_decompose_task_dna",
        alias="orch.task_dna",
        summary="Decomposes goal into evolutionary TaskDNA DAG",
        domain="dnk_orchestration",
        key_params=["goal"],
    ),
    "delegate_task": ToolMetadata(
        name="delegate_task",
        alias="orch.delegate",
        summary="Spawns isolated subagents for heavy reasoning",
        domain="dnk_orchestration",
        key_params=["goal", "role"],
    ),
    # Cognitive & Memory
    "scones_get_memories": ToolMetadata(
        name="scones_get_memories",
        alias="mem.search",
        summary="Searches SCONES long-term cognitive memories",
        domain="dnk_cognitive",
        key_params=["query", "limit"],
    ),
    "dnk_rag_query": ToolMetadata(
        name="dnk_rag_query",
        alias="rag.query",
        summary="High-precision dual-level LightRAG query across knowledge graph",
        domain="dnk_cognitive",
        key_params=["query", "mode", "top_k"],
    ),
    "dnk_rag_ingest": ToolMetadata(
        name="dnk_rag_ingest",
        alias="rag.ingest",
        summary="Ingests multimodal documents, text, or Canvas graphs into RAG",
        domain="dnk_cognitive",
        key_params=["content_or_path", "title"],
    ),
    "dnk_rag_sync_scones": ToolMetadata(
        name="dnk_rag_sync_scones",
        alias="rag.sync_scones",
        summary="Syncs multimodal knowledge graph themes into SCONES memory",
        domain="dnk_cognitive",
        key_params=["workspace_id"],
    ),
    "dnk_generate_marketing_banner": ToolMetadata(
        name="dnk_generate_marketing_banner",
        alias="rag.marketing_banner",
        summary="Synthesizes grounded marketing banner using cross-workspace knowledge and extracted visual assets",
        domain="dnk_multimedia",
        key_params=["product_name", "marketing_goal", "workspace_ids"],
    ),
    "scones_add_memory": ToolMetadata(
        name="scones_add_memory",
        alias="mem.add",
        summary="Saves long-term cognitive episode or architectural rule",
        domain="dnk_cognitive",
        key_params=["topic", "content", "importance"],
    ),
    "memory": ToolMetadata(
        name="memory",
        alias="mem.notes",
        summary="Saves persistent memory facts across sessions",
        domain="dnk_cognitive",
        key_params=["action", "target", "content"],
    ),
    "session_search": ToolMetadata(
        name="session_search",
        alias="mem.session_search",
        summary="FTS5 search over past session history and messages",
        domain="dnk_cognitive",
        key_params=["query", "limit"],
    ),
    "dnk_query_error_solutions": ToolMetadata(
        name="dnk_query_error_solutions",
        alias="heal.query_fix",
        summary="Queries Error Distillation DB for verified fixes",
        domain="dnk_cognitive",
        key_params=["error_text"],
    ),
    "dnk_record_error_solution": ToolMetadata(
        name="dnk_record_error_solution",
        alias="heal.record_fix",
        summary="Records solved error into Self-Healing DB",
        domain="dnk_cognitive",
        key_params=["error_text", "solution_text"],
    ),
    # Skills
    "skill_view": ToolMetadata(
        name="skill_view",
        alias="skill.load",
        summary="Loads procedural skill content or linked files",
        domain="skills",
        key_params=["name", "section"],
    ),
    "skills_list": ToolMetadata(
        name="skills_list",
        alias="skill.list",
        summary="Lists available skills with short descriptions",
        domain="skills",
        key_params=["category"],
    ),
    "skill_manage": ToolMetadata(
        name="skill_manage",
        alias="skill.edit",
        summary="Creates, patches, or deletes procedural skills",
        domain="skills",
        key_params=["action", "name"],
    ),
    # Stealth Scraping
    "dnk_stealth_scrape": ToolMetadata(
        name="dnk_stealth_scrape",
        alias="stealth.scrape",
        summary="Stealth zero-CDP web scraping and DOM extraction bypassing bot detection",
        domain="browser",
        key_params=["url", "selector", "eval_expression"],
    ),
    # Shopify
    "dnk_shopify_validate_liquid": ToolMetadata(
        name="dnk_shopify_validate_liquid",
        alias="shopify.validate_liquid",
        summary="Validates Liquid template syntax & security (XSS, performance, best practices)",
        domain="dnk_shopify",
        key_params=["content_or_path"],
    ),
    "dnk_one_click_product_launch": ToolMetadata(
        name="dnk_one_click_product_launch",
        alias="shopify.launch_product",
        summary="Executes autonomous product launch pipeline",
        domain="dnk_shopify",
        key_params=["product_name", "price_usd", "cost_usd"],
    ),
    # Video & Media
    "dnk_video_generate_composition": ToolMetadata(
        name="dnk_video_generate_composition",
        alias="video.generate",
        summary="Generates video composition from script (Remotion, FFmpeg)",
        domain="dnk_media",
        key_params=["title", "duration_seconds", "format_type"],
    ),
    # Canvas & Workspace
    "dnk_workspace_occ_merge": ToolMetadata(
        name="dnk_workspace_occ_merge",
        alias="canvas.merge",
        summary="Merges operational changes in Canvas (OCC conflict resolution)",
        domain="dnk_canvas",
        key_params=["base_state_json", "current_state_json", "incoming_state_json"],
    ),
    "dnk_visual_context_query": ToolMetadata(
        name="dnk_visual_context_query",
        alias="canvas.query_context",
        summary="Queries visual context selections from Canvas",
        domain="dnk_canvas",
        key_params=["context_id"],
    ),
    # Security
    "dnk_run_adversarial_review": ToolMetadata(
        name="dnk_run_adversarial_review",
        alias="sec.adversarial_review",
        summary="Executes 2-Agent Adversarial Review (Red vs Blue)",
        domain="dnk_security",
        key_params=["target_path"],
    ),
    "dnk_vault_get_secret": ToolMetadata(
        name="dnk_vault_get_secret",
        alias="sec.get_secret",
        summary="Safely retrieves workspace secret without logging",
        domain="dnk_security",
        key_params=["key_name"],
    ),
    "dnk_vault_set_secret": ToolMetadata(
        name="dnk_vault_set_secret",
        alias="sec.set_secret",
        summary="Securely stores API token in workspace vault",
        domain="dnk_security",
        key_params=["key_name", "secret_value"],
    ),
}

# Standardized TOOL_ALIASES dictionary per Technical Specification
TOOL_ALIASES: Dict[str, Dict[str, Any]] = {
    "dnk_shopify_validate_liquid": {
        "alias": "shopify.validate_liquid",
        "summary": "Validates Liquid template syntax & security (XSS, performance, best practices)",
        "full_schema_on_demand": True,
    },
    "dnk_shopify": {
        "alias": "shopify.validate_liquid",
        "summary": "Validates Liquid template syntax & security (XSS, performance, best practices)",
        "full_schema_on_demand": True,
    },
    "dnk_video_generate_composition": {
        "alias": "video.generate",
        "summary": "Generates video composition from script (Remotion, FFmpeg)",
        "full_schema_on_demand": True,
    },
    "dnk_media": {
        "alias": "video.generate",
        "summary": "Generates video composition from script (Remotion, FFmpeg)",
        "full_schema_on_demand": True,
    },
    "dnk_workspace_occ_merge": {
        "alias": "canvas.merge",
        "summary": "Merges operational changes in Canvas (OCC conflict resolution)",
        "full_schema_on_demand": True,
    },
    "dnk_canvas": {
        "alias": "canvas.merge",
        "summary": "Merges operational changes in Canvas (OCC conflict resolution)",
        "full_schema_on_demand": True,
    },
    "dnk_orchestrator_triage_task": {
        "alias": "orch.triage",
        "summary": "Analyzes task complexity, returns mode (SOLO/SWARM) + execution plan",
        "full_schema_on_demand": True,
    },
    "dnk_orchestration": {
        "alias": "orch.triage",
        "summary": "Analyzes task complexity, returns mode (SOLO/SWARM) + execution plan",
        "full_schema_on_demand": True,
    },
    "dnk_introspection_resolve_symbol": {
        "alias": "code.resolve_symbol",
        "summary": "Resolves symbol (class/function) location in codebase via AST",
        "full_schema_on_demand": True,
    },
    "dnk_introspection": {
        "alias": "code.resolve_symbol",
        "summary": "Resolves symbol (class/function) location in codebase via AST",
        "full_schema_on_demand": True,
    },
    "dnk_cognitive": {
        "alias": "memory.recall",
        "summary": "Searches SCONES long-term cognitive memories",
        "full_schema_on_demand": True,
    },
    "dnk_introspection_resolve_symbol": {
        "alias": "code.resolve_symbol",
        "summary": "Resolves symbol (class/function) location in codebase via AST",
        "full_schema_on_demand": True,
    },
    "dnk_resolve_symbol": {
        "alias": "code.resolve_symbol",
        "summary": "Resolves symbol (class/function) location in codebase via AST",
        "full_schema_on_demand": True,
    },
    # Common tools aliases
    "file.read": {
        "alias": "file.read",
        "summary": "Reads file content with line numbers and pagination",
        "full_schema_on_demand": True,
    },
    "read_file": {
        "alias": "file.read",
        "summary": "Reads file content with line numbers and pagination",
        "full_schema_on_demand": True,
    },
    "terminal.run": {
        "alias": "terminal.run",
        "summary": "Executes shell command in virtual environment",
        "full_schema_on_demand": True,
    },
    "terminal": {
        "alias": "terminal.run",
        "summary": "Executes shell command in virtual environment",
        "full_schema_on_demand": True,
    },
}

# Populate all other registry entries into TOOL_ALIASES if not present
for _name, _meta in TOOL_REGISTRY.items():
    if _name not in TOOL_ALIASES:
        TOOL_ALIASES[_name] = {
            "alias": _meta.alias,
            "summary": _meta.summary,
            "full_schema_on_demand": True,
        }
    if _meta.alias not in TOOL_ALIASES:
        TOOL_ALIASES[_meta.alias] = {
            "alias": _meta.alias,
            "summary": _meta.summary,
            "full_schema_on_demand": True,
        }

ALIAS_MAP: Dict[str, str] = {meta.alias: name for name, meta in TOOL_REGISTRY.items()}
for k, v in TOOL_ALIASES.items():
    alias = v["alias"]
    # Preserve full canonical tool names over generic domain toolsets
    if alias not in ALIAS_MAP or k.startswith("dnk_shopify_validate_liquid"):
        ALIAS_MAP[alias] = k
ALIAS_MAP["shopify.validate_liquid"] = "dnk_shopify_validate_liquid"
ALIAS_MAP["video.generate"] = "dnk_video_generate_composition"
ALIAS_MAP["canvas.merge"] = "dnk_workspace_occ_merge"
ALIAS_MAP["orch.triage"] = "dnk_orchestrator_triage_task"
ALIAS_MAP["code.resolve_symbol"] = "dnk_introspection_resolve_symbol"
ALIAS_MAP["sh"] = "terminal"
ALIAS_MAP["bash"] = "terminal"
ALIAS_MAP["shell"] = "terminal"
ALIAS_MAP["cat"] = "read_file"


def resolve_tool_name(name_or_alias: str) -> str:
    """Translates a short alias back to its canonical full tool name."""
    clean = name_or_alias.strip()
    return ALIAS_MAP.get(clean, clean)


def get_tool_metadata(name_or_alias: str) -> Optional[ToolMetadata]:
    """Retrieves tool metadata by either canonical name or alias."""
    canonical = resolve_tool_name(name_or_alias)
    return TOOL_REGISTRY.get(canonical)


TOOLSET_TO_TOOLS: Dict[str, List[str]] = {
    "stealth": ["dnk_stealth_scrape"],
    "browser": ["dnk_stealth_scrape"],
    "shopify": ["dnk_shopify_validate_liquid", "dnk_one_click_product_launch"],
    "remotion": ["dnk_video_generate_composition"],
    "multimedia": ["dnk_video_generate_composition", "dnk_generate_marketing_banner", "text_to_speech"],
    "canvas": ["dnk_workspace_occ_merge", "dnk_visual_context_query"],
    "core": [
        "terminal", "read_file", "write_file", "patch", "search_files",
        "dnk_triage_task", "dnk_resolve_symbol", "dnk_find_files",
        "scones_get_memories", "scones_add_memory",
        "dnk_rag_query", "dnk_rag_ingest", "dnk_generate_marketing_banner",
        "dnk_query_error_solutions", "dnk_record_error_solution"
    ],
}


def format_tool_summary(tool_name: str) -> str:
    """
    Returns: "- shopify.validate_liquid: Validates Liquid template syntax & security..."
    """
    if tool_name in TOOL_ALIASES:
        alias = TOOL_ALIASES[tool_name]["alias"]
        summary = TOOL_ALIASES[tool_name]["summary"]
        return f"- {alias}: {summary}"
    meta = get_tool_metadata(tool_name)
    if meta:
        return f"- {meta.alias}: {meta.summary}"
    return f"- {tool_name}: (no summary available)"


def format_all_tool_summaries(enabled_tools: List[str]) -> str:
    """
    Returns formatted multi-line summary of enabled tools.
    Expands toolsets (e.g. 'shopify', 'remotion', 'multimedia') to their constituent tools.
    """
    expanded_tools: Set[str] = set()
    for item in enabled_tools:
        if item in TOOLSET_TO_TOOLS:
            expanded_tools.update(TOOLSET_TO_TOOLS[item])
        elif item in TOOL_REGISTRY or item in TOOL_ALIASES:
            expanded_tools.add(item)
        else:
            matched = False
            for canonical, meta in TOOL_REGISTRY.items():
                if meta.domain.lower() == item.lower() or item.lower() in meta.domain.lower():
                    expanded_tools.add(canonical)
                    matched = True
            if not matched:
                expanded_tools.add(item)

    lines = ["Available tools:"]
    for tool in sorted(expanded_tools):
        lines.append(format_tool_summary(tool))
    return "\n".join(lines)


def format_compact_tool_catalog(
    enabled_domains: Optional[List[str]] = None,
    domains: Optional[List[str]] = None,
) -> str:
    """
    Generates an ultra-dense tool signature catalog for system prompts.
    Reduces token usage from ~17,500 down to ~350-500 tokens.
    """
    active_domains = domains or enabled_domains
    lines = ["# 🛠️ Available Tool Aliases (Lazy Loaded):"]
    domain_groups: Dict[str, List[ToolMetadata]] = {}
    for meta in TOOL_REGISTRY.values():
        if active_domains and meta.domain not in active_domains:
            continue
        domain_groups.setdefault(meta.domain, []).append(meta)

    for domain, tools in domain_groups.items():
        lines.append(f"## {domain}:")
        for tool in tools:
            params_str = ", ".join(tool.key_params) if tool.key_params else "none"
            lines.append(f"- `{tool.alias}` ({tool.name}): {tool.summary} [params: {params_str}]")

    lines.append("\n*Note: Full schemas are hydrated on demand; invoke via standard tool calls.*")
    return "\n".join(lines)


def estimate_tool_tokens(enabled_domains: Optional[List[str]] = None) -> int:
    """Estimates approximate token footprint for current tool catalog."""
    catalog = format_compact_tool_catalog(enabled_domains)
    return max(50, int(len(catalog.split()) * 1.3))
