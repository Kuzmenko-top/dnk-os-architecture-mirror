# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_specs_dnk_impl_009_plugin_system"
# purpose: "Technical specification and architectural standard for modular Plugin System"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

# DNK-IMPL-009: Plugin System

This document specifies the architecture and usage standards for the **Modular Plugin System** of DNK OS, allowing third-party tools, integrations, and event handlers to be hot-loaded without modifying core kernel directories.

---

## 1. Plugin Interface

Every pluggable extension must implement the abstract base class `Plugin` defined in `core/plugins/plugin_base.py`.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_event_handlers(self) -> Dict[str, callable]:
        pass
```

---

## 2. Plugin Manager

The registration and cataloging of plugins are handled by `PluginManager` located in `core/plugins/plugin_manager.py`. It provides functions to register, retrieve, and synthesize all compiled tools and event handlers across active plugins:

- `register_plugin(plugin: Plugin)` — registers and runs initial initialization parameters.
- `unregister_plugin(plugin_name: str)` — prunes plugin dependencies.
- `get_all_tools()` — flattens and returns a unified list of json schemas for LLM tool calling.
- `get_all_event_handlers()` — aggregates event-driven callback hooks for execution telemetry.

---

## 3. Autoloading (Plugin Loader)

The `PluginLoader` class in `core/plugins/plugin_loader.py` dynamically scans the designated filesystem folder (defaulting to `plugins/` under workspace) using robust python `importlib` specs.
Each plugin must follow the folder-naming pattern:
```text
plugins/
  <plugin_name_folder>/
    __init__.py
    plugin.py       # Holds the main Plugin subclass (e.g. SlackPlugin)
```
The loader dynamically parses subclasses, instantiates them, and registers them directly in the active context's `PluginManager`.

---

## 4. Agent Integration

Agents hook up to the plugin system using `AgentWithPlugins` in `core/agents/agent_with_plugins.py`. The agent accesses compiled tools from the `PluginManager`.

Before executing any custom plugin tool (e.g., `send_slack_message`), the agent automatically evaluates the execution request through the **Security Gate Service**, ensuring third-party tools are strictly governed and bounded by active system policies.

---

## 5. Configuration

Configuration parameters in `core/config/plugins_config.py`:
- `PLUGINS_DIR` (str, default="plugins") — directory target for plugin discovery.
- `ENABLED_PLUGINS` (List[str]) — list of allowed directory folders to scan (comma-separated env var).
- `PLUGIN_TIMEOUT_SECONDS` (int, default=30) — setup timeout thresholds.

---

## 6. Verification Tests

Verified dynamically in `tests/verification/test_plugin_system.py`:
1. `test_register_plugin` — registers a plugin and asserts initial parameters.
2. `test_unregister_plugin` — cleans up registrations.
3. `test_get_all_tools` — verifies schemas of tools are aggregated.
4. `test_get_all_event_handlers` — validates event-handling listeners are registered.
5. `test_plugin_auto_load` — scans and hot-loads `slack` and `notion` mock plugins.
6. `test_agent_with_plugins` — simulates tools executing under agent prompts.
7. `test_security_gate_for_plugins` — tests that custom tools undergo context-firewall policy evaluation.
