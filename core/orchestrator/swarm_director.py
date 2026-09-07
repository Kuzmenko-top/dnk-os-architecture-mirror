# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/swarm_director.py"
# purpose: "Authoritative Swarm Director facade consolidating task routing, agent registry, and DAG execution via SwarmControlPlane."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import logging
import threading
from typing import Any, Callable, Dict, List, Optional

from core.orchestrator.control_plane import SwarmControlPlane, TaskNode, swarm_control_plane
from core.orchestrator.swarm_coordinator import GerychSwarmCoordinator
from core.swarm.engine_adapter import SwarmEngineAdapter
from core.swarm.quantum_engine import TaskQuantum

logger = logging.getLogger("dnk.orchestrator.swarm_director")


class SwarmDirector:
    """
    Unified Swarm Director: Single authoritative entry point for routing,
    scheduling, and executing swarm tasks across the 14 specialized agents.
    Backwards-compatible with legacy orchestrators while backed by SwarmControlPlane.
    """

    ROUTING_KEYWORDS = {
        "gerych_builder": ["ui", "frontend", "component", "react", "canvas", "css", "html", "tailwind"],
        "gerych_researcher": ["ast", "github", "research", "paper", "sota", "scrape", "search", "explore"],
        "gerych_auditor": ["security", "audit", "verify", "test", "gate", "adversarial", "lint", "vulnerability"],
        "dnk_dev_fullstack": ["backend", "api", "fastapi", "database", "sqlalchemy", "model", "migration", "router"],
        "dnk_shopify": ["shopify", "liquid", "store", "product", "cart", "checkout", "theme"],
        "dnk_video_ai_creator": ["video", "remotion", "composition", "animation", "render", "media"],
        "dnk_security_guard": ["guard", "firewall", "secret", "vault", "auth", "token", "permission"],
        "dnk_scones_memory": ["scones", "memory", "recall", "store", "embedding", "vector", "retrieve"],
        "dnk_analytics": ["analytics", "metric", "telemetry", "prometheus", "dashboard", "report", "stats"],
        "dnk_erp_supply": ["erp", "supply", "inventory", "order", "warehouse", "logistics"],
        "dnk_finance_cfo": ["finance", "cfo", "budget", "cost", "revenue", "invoice", "pricing"],
        "dnk_marketing_cmo": ["marketing", "cmo", "campaign", "growth", "copy", "brand", "social"],
        "herich_librarian": ["librarian", "obsidian", "vault", "notes", "markdown", "knowledge", "doc"],
        "gerych_prime": ["orchestrate", "plan", "triage", "meta", "general", "root"],
    }

    _instance: Optional["SwarmDirector"] = None
    _lock = threading.RLock()

    def __init__(
        self,
        control_plane: Optional[SwarmControlPlane] = None,
        coordinator: Optional[GerychSwarmCoordinator] = None,
    ):
        self.control_plane = control_plane or swarm_control_plane
        self.coordinator = coordinator or GerychSwarmCoordinator()
        self.engine_adapter = SwarmEngineAdapter(control_plane=self.control_plane)
        self._lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> "SwarmDirector":
        """Singleton accessor for SwarmDirector."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def route_agent(self, task_description: str, preferred_agent: Optional[str] = None) -> str:
        """
        Determines the most qualified agent for a task description based on
        preferred overrides, capabilities, and keyword matching.
        """
        if preferred_agent and preferred_agent in GerychSwarmCoordinator.AGENTS:
            return preferred_agent

        desc_lower = task_description.lower()

        scores: Dict[str, int] = {agent: 0 for agent in GerychSwarmCoordinator.AGENTS}
        for agent, keywords in self.ROUTING_KEYWORDS.items():
            if agent in scores:
                for kw in keywords:
                    if kw in desc_lower:
                        scores[agent] += 1

        best_agent = max(scores, key=lambda a: scores[a])
        if scores[best_agent] > 0:
            return best_agent

        return "gerych_prime"

    def dispatch_task(
        self,
        task_description: str,
        preferred_agent: Optional[str] = None,
        from_agent: str = "gerych_prime",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches a task to the resolved agent via the coordinator.
        """
        agent = self.route_agent(task_description, preferred_agent)
        payload = {"task_description": task_description}
        if parameters:
            payload.update(parameters)
        return self.coordinator.dispatch_task(
            from_agent=from_agent,
            to_agent=agent,
            payload=payload,
        )

    def submit_step(
        self,
        step_id: str,
        handler: Callable[..., Any],
        depends_on: Optional[List[str]] = None,
        agent_role: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        requires_approval: bool = False,
        max_retries: int = 3,
    ) -> TaskNode:
        """
        Registers an execution step directly in the SwarmControlPlane DAG.
        """
        resolved_role = agent_role or self.route_agent(step_id)
        return self.control_plane.add_step(
            step_id=step_id,
            handler=handler,
            depends_on=depends_on,
            requires_approval=requires_approval,
            agent_role=resolved_role,
            payload=payload,
            max_retries=max_retries,
        )

    def execute_dag(self) -> Dict[str, Any]:
        """
        Executes the registered DAG in the SwarmControlPlane and returns node outputs.
        """
        res = self.control_plane.execute_graph()
        return res.get("results", {})

    def execute_quanta(
        self,
        task_id: str,
        quanta: List[TaskQuantum],
    ) -> Dict[str, Any]:
        """
        Executes low-level task quanta through the engine adapter and control plane.
        """
        res = self.engine_adapter.execute_quanta_pipeline(task_id, quanta)
        return {
            "task_id": res.task_id,
            "status": res.overall_status,
            "completed": res.completed_quanta,
            "failed": res.failed_quanta,
            "timeline": res.execution_timeline,
        }

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        Returns full manifest of active swarm agents with status and capability profiles.
        """
        agents_info = []
        for agent_name in GerychSwarmCoordinator.AGENTS:
            agents_info.append({
                "agent_id": agent_name,
                "keywords": self.ROUTING_KEYWORDS.get(agent_name, []),
                "status": "ready",
            })
        return agents_info

    def get_swarm_health(self) -> Dict[str, Any]:
        """
        Aggregated health snapshot of control plane and registered agents.
        """
        state = self.control_plane.get_state()
        return {
            "total_agents": len(GerychSwarmCoordinator.AGENTS),
            "control_plane_run_id": state.get("run_id"),
            "registered_dag_nodes": len(state.get("nodes", {})),
            "status": "HEALTHY",
        }


# Global instance
swarm_director = SwarmDirector.get_instance()
