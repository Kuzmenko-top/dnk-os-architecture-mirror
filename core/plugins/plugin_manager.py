# --- DNK-MRH-HEADER ---
# mrh_id: "core_plugins_plugin_manager"
# purpose: "Manage registration, lifecycle states, health checking, and error-isolated event triggering for plugins"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from core.plugins.plugin_base import Plugin

logger = logging.getLogger("dnk.plugins.manager")


class PluginState(str, Enum):
    REGISTERED = "REGISTERED"
    INITIALIZED = "INITIALIZED"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    ERROR = "ERROR"


class PluginManager:
    """Manages system plugin lifecycle, error-isolated execution, and health monitoring."""

    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.states: Dict[str, PluginState] = {}

    def register_plugin(self, plugin: Plugin, config: Optional[Dict[str, Any]] = None) -> None:
        self.plugins[plugin.name] = plugin
        try:
            plugin.initialize(config=config)
            self.states[plugin.name] = PluginState.INITIALIZED
            logger.info("Plugin '%s' (v%s) registered & initialized successfully.", plugin.name, plugin.version)
        except Exception as e:
            self.states[plugin.name] = PluginState.ERROR
            logger.error("Failed to initialize plugin '%s': %s", plugin.name, e)

    def unregister_plugin(self, plugin_name: str) -> None:
        if plugin_name in self.plugins:
            self.shutdown_plugin(plugin_name)
            del self.plugins[plugin_name]
            self.states.pop(plugin_name, None)

    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        return self.plugins.get(plugin_name)

    def get_plugin_state(self, plugin_name: str) -> Optional[PluginState]:
        return self.states.get(plugin_name)

    def shutdown_plugin(self, plugin_name: str) -> None:
        plugin = self.plugins.get(plugin_name)
        if plugin:
            try:
                plugin.shutdown()
            except Exception as e:
                logger.warning("Error during plugin '%s' shutdown: %s", plugin_name, e)
            self.states[plugin_name] = PluginState.DISABLED

    def shutdown_all(self) -> None:
        for name in list(self.plugins.keys()):
            self.shutdown_plugin(name)

    def health_check_all(self) -> Dict[str, bool]:
        health_map: Dict[str, bool] = {}
        for name, plugin in self.plugins.items():
            try:
                health_map[name] = plugin.health_check()
            except Exception:
                health_map[name] = False
        return health_map

    def get_all_tools(self) -> List[Dict[str, Any]]:
        tools = []
        for plugin in self.plugins.values():
            if self.states.get(plugin.name) in (PluginState.INITIALIZED, PluginState.ACTIVE):
                tools.extend(plugin.get_tools())
        return tools

    def get_all_event_handlers(self) -> Dict[str, List[Callable]]:
        handlers: Dict[str, List[Callable]] = {}
        for plugin in self.plugins.values():
            if self.states.get(plugin.name) in (PluginState.INITIALIZED, PluginState.ACTIVE):
                plugin_handlers = plugin.get_event_handlers()
                for event_type, handler in plugin_handlers.items():
                    if event_type not in handlers:
                        handlers[event_type] = []
                    handlers[event_type].append(handler)
        return handlers

    def trigger_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Triggers an event across all plugin handlers with strict error isolation."""
        executed = 0
        errors = 0
        details = []

        for name, plugin in self.plugins.items():
            try:
                plugin_handlers = plugin.get_event_handlers()
                if event_type in plugin_handlers:
                    handler = plugin_handlers[event_type]
                    handler(data)
                    executed += 1
                    details.append({"plugin": name, "status": "success"})
            except Exception as e:
                errors += 1
                details.append({"plugin": name, "status": "error", "error": str(e)})
                logger.error("Event handler error in plugin '%s' for event '%s': %s", name, event_type, e)

        return {
            "event_type": event_type,
            "executed": executed,
            "errors": errors,
            "details": details
        }
