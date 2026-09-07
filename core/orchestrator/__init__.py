# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/__init__.py"
# purpose: "Core orchestrator package initialization."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

try:
    from core.orchestrator.swarm_coordinator import (
        GerychSwarmCoordinator,
        swarm_coordinator,
    )
except ImportError:
    GerychSwarmCoordinator = None  # type: ignore
    swarm_coordinator = None  # type: ignore

__all__ = ["GerychSwarmCoordinator", "swarm_coordinator"]

