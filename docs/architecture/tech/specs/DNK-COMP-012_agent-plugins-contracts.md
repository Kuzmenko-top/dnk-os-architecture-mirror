# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-COMP-012_agent-plugins-contracts"
# purpose: "Component interface contracts and payload schemas for DNK OS Agent Plugins"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-13"
# --- END DNK-MRH-HEADER ---

# DNK-COMP-012: Agent Plugins Component Contracts

## 1. Plugin Base Interface Contract
```python
class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @property
    def description(self) -> str:
        return ""

    @property
    def author(self) -> str:
        return "DNK-e.com"

    @property
    def capabilities(self) -> List[str]:
        return ["tools", "event_handlers"]

    @property
    def config_schema(self) -> Dict[str, Any]:
        return {}

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def get_tools(self) -> List[Dict[str, Any]]:
        return []

    def get_event_handlers(self) -> Dict[str, callable]:
        return {}
```

## 2. Plugin Manager Interface Contract
```python
class PluginManager:
    def register_plugin(self, plugin: Plugin, config: Optional[Dict[str, Any]] = None) -> None: ...
    def unregister_plugin(self, plugin_name: str) -> None: ...
    def shutdown_plugin(self, plugin_name: str) -> None: ...
    def shutdown_all(self) -> None: ...
    def health_check_all(self) -> Dict[str, bool]: ...
    def get_plugin_state(self, plugin_name: str) -> PluginState: ...
    def get_all_tools(self) -> List[Dict[str, Any]]: ...
    def get_all_event_handlers(self) -> Dict[str, List[callable]]: ...
    def trigger_event(self, event_type: str, event_data: dict) -> Dict[str, Any]: ...
```

## 3. Event & Tool Delivery Payloads
- Tool definition payload schema:
  - `name`: string (required)
  - `description`: string (required)
  - `parameters`: JSON Schema dict
- Event dispatch result contract:
  - Returns dict mapping handler identity to execution status (`{"success": bool, "error": Optional[str]}`).
