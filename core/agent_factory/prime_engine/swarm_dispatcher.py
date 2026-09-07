# --- DNK-MRH-HEADER ---
# mrh_id: "core/agent_factory/prime_engine/swarm_dispatcher.py"
# purpose: "Concurrent Swarm Dispatcher routing tasks to specialized agents (Rick, Yuriy, Cas, Tiffany, Morgan)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class SwarmTaskResult:
    task_id: str
    assigned_agent: str
    status: str  # "completed", "failed", "in_progress"
    output_message: str
    execution_time_ms: float = 0.0


class SwarmDispatcher:
    """
    Routes tasks to specialized Swarm Agents based on agent capabilities.
    """
    def __init__(self, agents_dir: str = "core/agent_factory/agents") -> None:
        self.agents_dir = agents_dir
        self.available_agents: Dict[str, Dict[str, Any]] = self._load_installed_agents()

    def _load_installed_agents(self) -> Dict[str, Dict[str, Any]]:
        agents = {}
        if not os.path.exists(self.agents_dir):
            return agents

        for item in os.listdir(self.agents_dir):
            agent_path = os.path.join(self.agents_dir, item)
            manifest_path = os.path.join(agent_path, "MANIFEST.yaml")
            if os.path.isdir(agent_path) and os.path.exists(manifest_path):
                agents[item] = {
                    "id": item,
                    "path": agent_path,
                    "manifest": manifest_path
                }
        return agents

    def dispatch_task(self, task_id: str, task_title: str, required_capability: str) -> SwarmTaskResult:
        """
        Selects best agent matching capability and executes task.
        """
        matched_agent = self._select_agent_for_capability(required_capability)
        
        # Simulate execution for matched agent
        return SwarmTaskResult(
            task_id=task_id,
            assigned_agent=matched_agent,
            status="completed",
            output_message=f"Task `{task_title}` successfully executed by Agent `{matched_agent}`."
        )

    def _select_agent_for_capability(self, capability: str) -> str:
        cap = capability.lower()
        if "docker" in cap or "fastapi" in cap or "infra" in cap:
            return "agent_cas"
        elif "ui" in cap or "canvas" in cap or "stitch" in cap or "react" in cap:
            return "agent_tiffany"
        elif "metric" in cap or "analytics" in cap or "ucp" in cap:
            return "agent_morgan"
        elif "rag" in cap or "obsidian" in cap or "doc_" in cap or "notes" in cap:
            return "agent_yuriy"
        elif "test" in cap or "refactor" in cap:
            return "agent_rick"
        return "agent_rick"
