# --- DNK-MRH-HEADER ---
# mrh_id: "core/adapters/canvas_adapter.py"
# purpose: "Hexagonal Port and Adapter for CanvasEngine (open-design donor)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from core.canvas_engine import CanvasEngine, CanvasNode

class CanvasPort(ABC):
    """
    Abstract Port for Canvas visual, structural, and cycle detection capabilities.
    Defines the hexagonal boundary interface.
    """
    @abstractmethod
    def create_node(self, node_id: str, name: str, node_type: str, state: str = "Queued", metadata: Optional[Dict[str, Any]] = None) -> CanvasNode:
        pass

    @abstractmethod
    def modify_node_state(self, node_id: str, new_state: str) -> None:
        pass

    @abstractmethod
    def connect_nodes(self, from_id: str, to_id: str) -> None:
        pass

    @abstractmethod
    def disconnect_nodes(self, from_id: str, to_id: str) -> bool:
        pass

    @abstractmethod
    def check_cycle_dependencies(self) -> bool:
        pass

    @abstractmethod
    def draw_text_representation(self) -> str:
        pass

    @abstractmethod
    def export_state_dict(self) -> Dict[str, Any]:
        pass


class CanvasAdapter(CanvasPort):
    """
    Hexagonal Adapter wrapping the core CanvasEngine use cases.
    """
    def __init__(self, engine: CanvasEngine):
        self._engine = engine

    def create_node(self, node_id: str, name: str, node_type: str, state: str = "Queued", metadata: Optional[Dict[str, Any]] = None) -> CanvasNode:
        return self._engine.add_node(node_id, name, node_type, state, metadata)

    def modify_node_state(self, node_id: str, new_state: str) -> None:
        self._engine.update_node_state(node_id, new_state)

    def connect_nodes(self, from_id: str, to_id: str) -> None:
        self._engine.add_edge(from_id, to_id)

    def disconnect_nodes(self, from_id: str, to_id: str) -> bool:
        return self._engine.remove_edge(from_id, to_id)

    def check_cycle_dependencies(self) -> bool:
        return self._engine.has_cycle()

    def draw_text_representation(self) -> str:
        return self._engine.render_canvas_text()

    def export_state_dict(self) -> Dict[str, Any]:
        return self._engine.to_dict()
