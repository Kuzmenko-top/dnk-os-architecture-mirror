# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-SERVICE-REBALANCER"
# purpose: "A2A Dynamic Load Rebalancer and Heartbeat Health Monitor"
# canonical_source: true
# alters_files: ["apps/api/services/a2a_load_rebalancer.py"]
# triggers_tasks: ["DNK-A2A-003-PHASE3"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple


class A2ALoadRebalancer:
    """Dynamic load rebalancing engine monitoring swarm agents, detecting overloads, and shedding tasks."""

    CPU_THRESHOLD_DEFAULT = 80.0
    RAM_THRESHOLD_DEFAULT = 80.0
    HEARTBEAT_TIMEOUT_DEFAULT_SEC = 15.0

    def __init__(self):
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._node_tasks: Dict[str, List[Dict[str, Any]]] = {}  # agent_id -> list of task dicts

    def register_node(
        self,
        agent_id: str,
        agent_name: str,
        capabilities: List[str],
        cpu_utilization: float = 0.0,
        memory_utilization: float = 0.0,
        workspace_id: str = "ws-default",
    ) -> Dict[str, Any]:
        node_info = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "workspace_id": workspace_id,
            "capabilities": capabilities or [],
            "cpu_utilization": cpu_utilization,
            "memory_utilization": memory_utilization,
            "status": "online",
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        }
        self._nodes[agent_id] = node_info
        if agent_id not in self._node_tasks:
            self._node_tasks[agent_id] = []
        return node_info

    def update_heartbeat(
        self,
        agent_id: str,
        cpu_utilization: float,
        memory_utilization: float,
        active_tasks: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        node = self._nodes.get(agent_id)
        if not node:
            node = self.register_node(
                agent_id=agent_id,
                agent_name=agent_id,
                capabilities=[],
                cpu_utilization=cpu_utilization,
                memory_utilization=memory_utilization,
            )

        if node is not None:
            node["cpu_utilization"] = cpu_utilization
            node["memory_utilization"] = memory_utilization
            node["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
            node["status"] = "online"

        if active_tasks is not None:
            self._node_tasks[agent_id] = active_tasks
        return True

    def assign_task(self, agent_id: str, task: Dict[str, Any]) -> bool:
        if agent_id not in self._nodes:
            return False
        if agent_id not in self._node_tasks:
            self._node_tasks[agent_id] = []
        self._node_tasks[agent_id].append(task)
        return True

    def evaluate_mesh_health(
        self,
        cpu_threshold: float = CPU_THRESHOLD_DEFAULT,
        ram_threshold: float = RAM_THRESHOLD_DEFAULT,
        heartbeat_timeout_sec: float = HEARTBEAT_TIMEOUT_DEFAULT_SEC,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        timeout_delta = timedelta(seconds=heartbeat_timeout_sec)

        healthy_nodes = []
        overloaded_nodes = []
        unhealthy_nodes = []

        for agent_id, node in self._nodes.items():
            last_hb = datetime.fromisoformat(node["last_heartbeat"])
            is_timed_out = (now - last_hb) > timeout_delta

            if is_timed_out:
                node["status"] = "unhealthy"
                unhealthy_nodes.append(node)
                continue

            is_overloaded = (
                node["cpu_utilization"] >= cpu_threshold or
                node["memory_utilization"] >= ram_threshold
            )
            if is_overloaded:
                node["status"] = "overloaded"
                overloaded_nodes.append(node)
            else:
                node["status"] = "online"
                healthy_nodes.append(node)

        return {
            "total_nodes": len(self._nodes),
            "healthy_nodes": healthy_nodes,
            "overloaded_nodes": overloaded_nodes,
            "unhealthy_nodes": unhealthy_nodes,
            "nodes": {k: v for k, v in self._nodes.items()},
        }

    def plan_and_execute_rebalance(
        self,
        cpu_threshold: float = CPU_THRESHOLD_DEFAULT,
        ram_threshold: float = RAM_THRESHOLD_DEFAULT,
        heartbeat_timeout_sec: float = HEARTBEAT_TIMEOUT_DEFAULT_SEC,
    ) -> Dict[str, Any]:
        health = self.evaluate_mesh_health(cpu_threshold, ram_threshold, heartbeat_timeout_sec)
        troubled_nodes = health["overloaded_nodes"] + health["unhealthy_nodes"]
        healthy_nodes = health["healthy_nodes"]

        reassigned_tasks: List[Dict[str, Any]] = []

        if not troubled_nodes or not healthy_nodes:
            return {
                "rebalanced": False,
                "reassigned_tasks_count": 0,
                "reassigned_tasks": [],
                "health": health,
            }

        for source_node in troubled_nodes:
            source_id = source_node["agent_id"]
            tasks = list(self._node_tasks.get(source_id, []))
            if not tasks:
                continue

            # If node is completely unhealthy (timed out), reassign all tasks.
            # If merely overloaded, offload half of tasks.
            num_tasks_to_move = len(tasks) if source_node["status"] == "unhealthy" else max(1, len(tasks) // 2)
            tasks_to_move = tasks[:num_tasks_to_move]

            for task in tasks_to_move:
                req_caps = task.get("required_capabilities", [])

                # Find candidate healthy node that has capabilities and lowest CPU
                candidates = [
                    h for h in healthy_nodes
                    if all(c in h["capabilities"] for c in req_caps)
                ]
                if not candidates:
                    candidates = healthy_nodes  # Fallback to any healthy node

                best_target = min(candidates, key=lambda h: (h["cpu_utilization"] + h["memory_utilization"]) / 2.0)
                target_id = best_target["agent_id"]

                # Move task
                self._node_tasks[source_id].remove(task)
                self._node_tasks[target_id].append(task)

                reassigned_tasks.append({
                    "task_id": task.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                    "from_agent_id": source_id,
                    "to_agent_id": target_id,
                    "reason": f"Source node status: {source_node['status']}",
                })

        return {
            "rebalanced": len(reassigned_tasks) > 0,
            "reassigned_tasks_count": len(reassigned_tasks),
            "reassigned_tasks": reassigned_tasks,
            "health": health,
        }

    def get_node_tasks(self, agent_id: str) -> List[Dict[str, Any]]:
        return self._node_tasks.get(agent_id, [])

    def list_nodes(self) -> List[Dict[str, Any]]:
        return list(self._nodes.values())
