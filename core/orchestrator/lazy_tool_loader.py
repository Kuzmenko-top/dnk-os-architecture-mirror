# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/lazy_tool_loader.py"
# purpose: "Lazy schema loader and dynamic tool retriever to eliminate Context Window Tax."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
Lazy Tool Schema Loader.

Prevents upfront injection of 60+ full JSON tool schemas into LLM context.
Schemas are registered with lightweight metadata and fully hydrated only
on-demand when explicitly requested by an agent or task domain.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from core.orchestrator.tool_aliases import (
    TOOL_ALIASES,
    TOOL_REGISTRY,
    get_tool_metadata,
    resolve_tool_name,
)


@dataclass
class ToolSpec:
    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    alias: Optional[str] = None


@dataclass
class ToolSchemaEntry:
    name: str
    schema: Optional[Dict[str, Any]] = None
    loader_fn: Optional[Callable[[], Dict[str, Any]]] = None
    domain: str = "general"
    is_loaded: bool = False


class LazyToolLoader:
    """
    Loads tool schemas ON-DEMAND, not upfront.
    Before: 25k токенів (всі схеми)
    After: 2k токенів (тільки назви) + 500 токенів (lazy load per tool)
    """

    def __init__(self, tool_registry: Optional[Dict[str, Any]] = None):
        if tool_registry is None:
            # Seed default mock schemas from TOOL_ALIASES / TOOL_REGISTRY
            self.tool_registry: Dict[str, Any] = {}
            for k, meta in TOOL_REGISTRY.items():
                self.tool_registry[k] = {
                    "name": meta.name,
                    "description": meta.summary,
                    "parameters": {"type": "object", "properties": {p: {"type": "string"} for p in meta.key_params}},
                }
                self.tool_registry[meta.alias] = self.tool_registry[k]
        else:
            self.tool_registry = tool_registry

        self.loaded_tools: Dict[str, Any] = {}
        self.enabled_tools: Set[str] = set()

    def set_enabled_tools(self, tool_names: List[str]) -> None:
        """
        Set which tools are enabled for current task.
        """
        self.enabled_tools = set(tool_names)

    def get_tool(self, tool_name: str) -> Optional[Any]:
        """
        Load tool schema ONLY when actually used.
        Returns None if tool is not enabled.
        """
        if tool_name not in self.enabled_tools:
            return None

        if tool_name not in self.loaded_tools:
            # Lazy load from registry
            resolved_key = tool_name
            if resolved_key not in self.tool_registry and resolve_tool_name(tool_name) in self.tool_registry:
                resolved_key = resolve_tool_name(tool_name)

            if resolved_key in self.tool_registry:
                tool_val = self.tool_registry[resolved_key]
                if callable(tool_val):
                    tool_val = tool_val()
                self.loaded_tools[tool_name] = tool_val
            else:
                # Fallback schema stub if not explicitly defined in registry
                self.loaded_tools[tool_name] = {
                    "name": tool_name,
                    "description": f"On-demand schema for {tool_name}",
                    "parameters": {"type": "object", "properties": {}},
                }

        return self.loaded_tools[tool_name]

    def get_available_tools_summary(self) -> str:
        """
        Return ONLY tool names (not full schemas) for model context.
        Example: "Available tools: file_read, file_write, terminal_run, ..."
        Total: ~500 токенів замість 17,500!
        """
        enabled_list = sorted(self.enabled_tools)
        return f"Available tools: {', '.join(enabled_list)}"

    def get_tool_schema(self, tool_name: str) -> Optional[Any]:
        """
        Return full schema ONLY if tool is in enabled_toolsets.
        """
        return self.get_tool(tool_name)

    def get_slim_guard(self) -> Any:
        """Returns MCPSlimGuard instance bound to this tool registry."""
        from core.orchestrator.mcp_slim_guard import MCPSlimGuard
        return MCPSlimGuard(self.tool_registry)

    def get_meta_tools_schema(self) -> Dict[str, Any]:
        """Returns meta-tools schema (find_tool, call_tool, read_result)."""
        return self.get_slim_guard().get_meta_tools_schema()


class LazyToolRegistry:
    """
    On-demand schema registry. Maintains schema definitions in memory or via
    callables, exposing full JSON schemas only when hydrated.
    """

    def __init__(self) -> None:
        self._entries: Dict[str, ToolSchemaEntry] = {}
        self._active_schemas: Dict[str, Dict[str, Any]] = {}
        self._seed_default_tools()

    def _seed_default_tools(self) -> None:
        """Seeds registry from canonical TOOL_REGISTRY with lazy stubs."""
        for name, meta in TOOL_REGISTRY.items():
            self.register_lazy(
                name=name,
                loader_fn=self._create_stub_loader(name, meta.summary, meta.key_params),
                domain=meta.domain,
            )

    @staticmethod
    def _create_stub_loader(name: str, summary: str, params: List[str]) -> Callable[[], Dict[str, Any]]:
        def _loader() -> Dict[str, Any]:
            properties = {p: {"type": "string", "description": f"Parameter {p}"} for p in params}
            return {
                "name": name,
                "description": summary,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": params[:1] if params else [],
                },
            }
        return _loader

    def register_schema(self, name: str, schema: Dict[str, Any], domain: str = "general") -> None:
        """Registers a fully realized schema directly."""
        canonical_name = resolve_tool_name(name)
        self._entries[canonical_name] = ToolSchemaEntry(
            name=canonical_name,
            schema=schema,
            domain=domain,
            is_loaded=True,
        )
        self._active_schemas[canonical_name] = schema

    def register_lazy(
        self,
        name: str,
        loader_fn: Callable[[], Dict[str, Any]],
        domain: str = "general",
    ) -> None:
        """Registers a schema that will only be evaluated when loaded."""
        canonical_name = resolve_tool_name(name)
        self._entries[canonical_name] = ToolSchemaEntry(
            name=canonical_name,
            loader_fn=loader_fn,
            domain=domain,
            is_loaded=False,
        )

    def is_loaded(self, name_or_alias: str) -> bool:
        """Checks if schema is currently loaded/hydrated in memory."""
        canonical = resolve_tool_name(name_or_alias)
        return canonical in self._active_schemas

    def load_schema(self, name_or_alias: str) -> Dict[str, Any]:
        """
        Loads schema on-demand if not already hydrated.
        Raises KeyError if tool is not registered.
        """
        canonical = resolve_tool_name(name_or_alias)
        if canonical in self._active_schemas:
            return self._active_schemas[canonical]

        if canonical not in self._entries:
            raise KeyError(f"Tool '{name_or_alias}' is not registered in LazyToolRegistry.")

        entry = self._entries[canonical]
        if entry.schema is not None:
            schema = entry.schema
        elif entry.loader_fn is not None:
            schema = entry.loader_fn()
            entry.schema = schema
        else:
            raise ValueError(f"Schema entry '{canonical}' has neither schema nor loader_fn.")

        entry.is_loaded = True
        self._active_schemas[canonical] = schema
        return schema

    def load_schemas_for_domain(self, domain: str) -> Dict[str, Dict[str, Any]]:
        """Hydrates all schemas belonging to a specific domain (with normalization)."""
        hydrated: Dict[str, Dict[str, Any]] = {}
        target = domain.lower()
        for canonical, entry in self._entries.items():
            ed = entry.domain.lower()
            match = (
                ed == target
                or (target in ("shopify_ecom", "shopify") and "shopify" in ed)
                or (target in ("multimedia_video", "video", "media") and ("media" in ed or "video" in ed))
                or (target in ("canvas", "frontend_canvas") and "canvas" in ed)
                or (target in ("backend_api", "backend") and "backend" in ed)
            )
            if match:
                hydrated[canonical] = self.load_schema(canonical)
        return hydrated

    def load_schemas_batch(self, names_or_aliases: List[str]) -> Dict[str, Dict[str, Any]]:
        """Loads a batch of schemas on-demand."""
        hydrated: Dict[str, Dict[str, Any]] = {}
        for item in names_or_aliases:
            hydrated[resolve_tool_name(item)] = self.load_schema(item)
        return hydrated

    def evict_schema(self, name_or_alias: str) -> bool:
        """Evicts a schema from active active list to free context."""
        canonical = resolve_tool_name(name_or_alias)
        if canonical in self._active_schemas:
            del self._active_schemas[canonical]
            if canonical in self._entries:
                self._entries[canonical].is_loaded = False
            return True
        return False

    def clear_active(self) -> int:
        """Unloads all active schemas, returning the number evicted."""
        count = len(self._active_schemas)
        self._active_schemas.clear()
        for entry in self._entries.values():
            entry.is_loaded = False
        return count

    def get_active_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Returns all currently active (hydrated) full JSON schemas."""
        return dict(self._active_schemas)

    def get_registered_count(self) -> int:
        return len(self._entries)

    def get_active_count(self) -> int:
        return len(self._active_schemas)

    def get_token_savings(self) -> Dict[str, Any]:
        """Calculates token savings vs 17,500 baseline upfront schemas."""
        baseline = 17500
        active_count = len(self._active_schemas)
        active_tokens = active_count * 400
        savings_tokens = max(0, baseline - active_tokens)
        savings_pct = round((savings_tokens / baseline) * 100, 1)
        return {
            "baseline_tokens": baseline,
            "active_tokens": active_tokens,
            "saved_tokens": savings_tokens,
            "savings_pct": savings_pct,
            "active_count": active_count,
            "registered_count": len(self._entries),
        }

    def get_slim_guard(self) -> Any:
        """Returns MCPSlimGuard instance bound to this registry."""
        from core.orchestrator.mcp_slim_guard import MCPSlimGuard
        return MCPSlimGuard()

    def get_meta_tools_schema(self) -> Dict[str, Any]:
        """Returns meta-tools schema (find_tool, call_tool, read_result)."""
        return self.get_slim_guard().get_meta_tools_schema()


# Global singleton instances
lazy_tool_loader = LazyToolRegistry()


def get_lazy_loader() -> LazyToolRegistry:
    return lazy_tool_loader


get_lazy_tool_loader = get_lazy_loader
