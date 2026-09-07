# --- DNK-MRH-HEADER ---
# mrh_id: "core/adapters/hermes_adapter.py"
# purpose: "Hexagonal Port and Adapter for HermesRuntime (hermes-agent donor)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable
try:
    from core.hermes_runtime import HermesRuntime
except ImportError:
    from core.hermes_runtime import HermesRuntime

class HermesPort(ABC):
    """
    Abstract Port for Hermes safety, dry-run, and rollback capabilities.
    Defines the hexagonal boundary interface.
    """
    @abstractmethod
    def run_dry_run(self, action_type: str, targets: List[str], details: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def run_safely(self, action_fn: Callable[[], Any], verify_fn: Callable[[], bool], file_paths: List[str]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def stage_destructive_action(self, action_type: str, target: str, details: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def confirm_destructive_action(self, approval_id: str, auth_phrase: str) -> bool:
        pass


class HermesAdapter(HermesPort):
    """
    Hexagonal Adapter wrapping the core HermesRuntime use cases.
    """
    def __init__(self, runtime: HermesRuntime):
        self._runtime = runtime

    def run_dry_run(self, action_type: str, targets: List[str], details: Dict[str, Any]) -> Dict[str, Any]:
        return self._runtime.generate_dry_run_plan(action_type, targets, details)

    def run_safely(self, action_fn: Callable[[], Any], verify_fn: Callable[[], bool], file_paths: List[str]) -> Dict[str, Any]:
        return self._runtime.execute_safely(action_fn, verify_fn, file_paths)

    def stage_destructive_action(self, action_type: str, target: str, details: Dict[str, Any]) -> str:
        return self._runtime.request_destructive_action(action_type, target, details)

    def confirm_destructive_action(self, approval_id: str, auth_phrase: str) -> bool:
        return self._runtime.approve_destructive_action(approval_id, auth_phrase)
