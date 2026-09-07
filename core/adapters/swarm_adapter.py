# --- DNK-MRH-HEADER ---
# mrh_id: "core/adapters/swarm_adapter.py"
# purpose: "Hexagonal Port and Adapter for SwarmOrchestrator (agentswarms donor)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from core.swarm_orchestrator import SwarmOrchestrator

class SwarmPort(ABC):
    """
    Abstract Port for Swarm orchestration, role definitions, and dynamic RAG skill injection.
    Defines the hexagonal boundary interface.
    """
    @abstractmethod
    def load_role(self, yaml_content: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def add_skill(self, name: str, description: str, content: str, tags: Optional[List[str]] = None) -> None:
        pass

    @abstractmethod
    def retrieve_skills(self, agent_name: str, query: str, limit: int = 2) -> Tuple[List[Dict[str, Any]], float]:
        pass

    @abstractmethod
    def prepare_instructions(self, agent_name: str, task_query: str) -> str:
        pass


class SwarmAdapter(SwarmPort):
    """
    Hexagonal Adapter wrapping the core SwarmOrchestrator use cases.
    """
    def __init__(self, orchestrator: SwarmOrchestrator):
        self._orchestrator = orchestrator

    def load_role(self, yaml_content: str) -> Dict[str, Any]:
        return self._orchestrator.load_role_manifest(yaml_content)

    def add_skill(self, name: str, description: str, content: str, tags: Optional[List[str]] = None) -> None:
        self._orchestrator.register_skill(name, description, content, tags)

    def retrieve_skills(self, agent_name: str, query: str, limit: int = 2) -> Tuple[List[Dict[str, Any]], float]:
        return self._orchestrator.inject_skills_rag(agent_name, query, limit)

    def prepare_instructions(self, agent_name: str, task_query: str) -> str:
        return self._orchestrator.compile_agent_system_instructions(agent_name, task_query)
