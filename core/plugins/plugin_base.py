# --- DNK-MRH-HEADER ---
# mrh_id: "core_plugins_plugin_base"
# purpose: "Base abstract class for all system plugins to enforce unified interface"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    def description(self) -> str:
        return "DNK OS Standard Plugin"

    @property
    def author(self) -> str:
        return "DNK-e.com Maksym"

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

    def get_event_handlers(self) -> Dict[str, Any]:
        return {}
