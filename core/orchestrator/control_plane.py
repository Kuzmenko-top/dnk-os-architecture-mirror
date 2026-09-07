# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/control_plane.py"
# purpose: "Unified Swarm Control Plane: Authoritative DAG State Machine, Checkpointing, and Multi-Agent Orchestration Engine."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import json
import time
import uuid
import logging
import threading
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class NodeState(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED_APPROVAL = "paused_approval"
    RETRYING = "retrying"

class TaskNode:
    """
    Unified task node inside the DAG execution graph.
    """
    def __init__(
        self,
        node_id: str,
        handler: Optional[Callable[..., Any]] = None,
        depends_on: Optional[List[str]] = None,
        requires_approval: bool = False,
        agent_role: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ):
        self.id = node_id
        self.node_id = node_id
        self.handler = handler
        self.depends_on: List[str] = list(depends_on or [])
        self.requires_approval = requires_approval
        self.agent_role = agent_role
        self.payload: Dict[str, Any] = payload or {}
        self.max_retries = max_retries
        self.retry_count = 0
        self.status = NodeState.PENDING
        self.result: Any = None
        self.error: Optional[str] = None
        self.created_at = time.time()
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "depends_on": self.depends_on,
            "requires_approval": self.requires_approval,
            "agent_role": self.agent_role,
            "payload": self.payload,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "status": self.status.value,
            "result": str(self.result) if self.result is not None else None,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

class StateCheckpointer:
    """
    Persistent state checkpointer for time-travel, fault tolerance, and crash recovery.
    Saves snapshots to an isolated runtime cache path.
    """
    def __init__(self, checkpoint_file: Optional[str] = None):
        if not checkpoint_file:
            runtime_dir = os.path.expanduser("~/.hermes/runtime")
            os.makedirs(runtime_dir, exist_ok=True)
            self.checkpoint_file = os.path.join(runtime_dir, "control_plane_checkpoints.json")
        else:
            self.checkpoint_file = checkpoint_file
        self._lock = threading.Lock()

    def save(self, run_id: str, graph_state: Dict[str, Any]) -> None:
        with self._lock:
            data = {}
            if os.path.exists(self.checkpoint_file):
                try:
                    with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data[run_id] = {
                "timestamp": time.time(),
                "state": graph_state,
            }
            try:
                temp_file = f"{self.checkpoint_file}.tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                os.replace(temp_file, self.checkpoint_file)
            except Exception as e:
                logger.warning(f"Failed to persist control plane checkpoint: {e}")

    def load(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if not os.path.exists(self.checkpoint_file):
                return None
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get(run_id, {}).get("state")
            except Exception as e:
                logger.warning(f"Failed to load control plane checkpoint: {e}")
                return None

class SwarmControlPlane:
    """
    Unified Authoritative Control Plane & State Machine for all swarm coordination.
    Combines DAG execution, supervisor retry loops, approval gates, and RAG skill injection.
    """
    def __init__(
        self,
        tenant_id: str = "default_tenant",
        workspace_id: str = "ws-alpha-001",
        checkpointer: Optional[Any] = None,
        checkpoint_path: Optional[str] = None,
    ):
        self.tenant_id = tenant_id
        self.workspace_id = workspace_id
        if isinstance(checkpointer, StateCheckpointer):
            self.checkpointer = checkpointer
        elif isinstance(checkpointer, str):
            self.checkpointer = StateCheckpointer(checkpoint_file=checkpointer)
        elif checkpoint_path:
            self.checkpointer = StateCheckpointer(checkpoint_file=checkpoint_path)
        else:
            self.checkpointer = StateCheckpointer()
        self.nodes: Dict[str, TaskNode] = {}
        self.approvals: Dict[str, bool] = {}
        self.roles: Dict[str, Dict[str, Any]] = {}
        self.skills: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.run_id = f"run_{uuid.uuid4().hex[:12]}"

    # --- Node & DAG Management ---

    def add_step(
        self,
        step_id: str,
        handler: Optional[Callable[..., Any]] = None,
        depends_on: Optional[List[str]] = None,
        requires_approval: bool = False,
        agent_role: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> TaskNode:
        with self._lock:
            node = TaskNode(
                node_id=step_id,
                handler=handler,
                depends_on=depends_on,
                requires_approval=requires_approval,
                agent_role=agent_role,
                payload=payload,
                max_retries=max_retries,
            )
            self.nodes[step_id] = node
            return node

    def add_node(self, node: TaskNode) -> TaskNode:
        with self._lock:
            self.nodes[node.node_id] = node
            return node

    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "run_id": self.run_id,
                "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
                "approvals": dict(self.approvals),
            }

    def grant_approval(self, step_id: str) -> None:
        with self._lock:
            self.approvals[step_id] = True
            if step_id in self.nodes:
                if self.nodes[step_id].status == NodeState.PAUSED_APPROVAL:
                    self.nodes[step_id].status = NodeState.PENDING

    def has_cycle(self) -> bool:
        with self._lock:
            visited: Set[str] = set()
            rec_stack: Set[str] = set()

            def dfs(node_id: str) -> bool:
                visited.add(node_id)
                rec_stack.add(node_id)
                for dep in self.nodes[node_id].depends_on:
                    if dep not in self.nodes:
                        continue
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        return True
                rec_stack.remove(node_id)
                return False

            for node_id in self.nodes:
                if node_id not in visited:
                    if dfs(node_id):
                        return True
            return False

    def checkpoint(self) -> None:
        with self._lock:
            state_dict = {nid: node.to_dict() for nid, node in self.nodes.items()}
            self.checkpointer.save(self.run_id, state_dict)

    def restore_checkpoint(self, run_id: str) -> bool:
        with self._lock:
            saved = self.checkpointer.load(run_id)
            if not saved:
                return False
            self.run_id = run_id
            for nid, node_data in saved.items():
                if nid in self.nodes:
                    self.nodes[nid].status = NodeState(node_data.get("status", "pending"))
                    self.nodes[nid].retry_count = node_data.get("retry_count", 0)
                    self.nodes[nid].result = node_data.get("result")
                    self.nodes[nid].error = node_data.get("error")
                else:
                    self.nodes[nid] = TaskNode(
                        node_id=nid,
                        agent_role=node_data.get("agent_role", "worker"),
                        depends_on=node_data.get("depends_on", []),
                        requires_approval=node_data.get("requires_approval", False),
                        payload=node_data.get("payload", {}),
                        max_retries=node_data.get("max_retries", 3),
                    )
                    self.nodes[nid].status = NodeState(node_data.get("status", "pending"))
                    self.nodes[nid].retry_count = node_data.get("retry_count", 0)
                    self.nodes[nid].result = node_data.get("result")
                    self.nodes[nid].error = node_data.get("error")
            return True

    # --- Execution Engine ---

    def execute_graph(self) -> Dict[str, Any]:
        """
        Executes the graph following DAG topological order with approval gates and checkpointers.
        """
        with self._lock:
            if self.has_cycle():
                raise ValueError("Cannot execute workflow: Graph contains circular dependency cycle.")

        executed_results: Dict[str, Any] = {}

        while True:
            progress_made = False
            paused_any = False

            with self._lock:
                for node_id, node in self.nodes.items():
                    if node.status in (NodeState.COMPLETED, NodeState.FAILED):
                        continue

                    # Check dependencies
                    deps_satisfied = True
                    for dep_id in node.depends_on:
                        if dep_id in self.nodes:
                            if self.nodes[dep_id].status != NodeState.COMPLETED:
                                deps_satisfied = False
                                break

                    if not deps_satisfied:
                        continue

                    # Check approval gate
                    if node.requires_approval and not self.approvals.get(node_id, False):
                        node.status = NodeState.PAUSED_APPROVAL
                        paused_any = True
                        continue

                    # Execute node
                    node.status = NodeState.RUNNING
                    node.updated_at = time.time()
                    try:
                        if node.handler:
                            if node.payload:
                                res = node.handler(node.payload)
                            else:
                                res = node.handler()
                        else:
                            res = {"status": "ok", "node_id": node_id}

                        node.result = res
                        node.status = NodeState.COMPLETED
                        node.updated_at = time.time()
                        executed_results[node_id] = res
                        progress_made = True
                    except Exception as e:
                        node.retry_count += 1
                        if node.retry_count <= node.max_retries:
                            node.status = NodeState.RETRYING
                            logger.warning(f"Node {node_id} failed (attempt {node.retry_count}): {e}. Retrying...")
                            progress_made = True
                        else:
                            node.status = NodeState.FAILED
                            node.error = str(e)
                            logger.error(f"Node {node_id} permanently failed: {e}")
                            executed_results[node_id] = {"error": str(e)}

                    self.checkpoint()

            if not progress_made:
                break

        with self._lock:
            all_done = all(n.status == NodeState.COMPLETED for n in self.nodes.values())
            any_paused = any(n.status == NodeState.PAUSED_APPROVAL for n in self.nodes.values())
            any_failed = any(n.status == NodeState.FAILED for n in self.nodes.values())

            return {
                "run_id": self.run_id,
                "all_completed": all_done,
                "is_paused": any_paused,
                "has_failures": any_failed,
                "results": executed_results,
                "states": {nid: n.status.value for nid, n in self.nodes.items()},
            }

    def execute_dag(self) -> Dict[str, Any]:
        """Alias for execute_graph returning results keyed by step id with node status."""
        res = self.execute_graph()
        out = {nid: {"status": node.status, "result": node.result, "error": node.error} for nid, node in self.nodes.items()}
        out["_summary"] = res
        return out

    def execute(self) -> Dict[str, Any]:
        """Convenience alias for execute_graph."""
        return self.execute_graph()

    # --- SOTA RAG Skill Injection (<0.05s set-intersection) ---

    def register_role(self, role_name: str, manifest: Dict[str, Any]) -> None:
        with self._lock:
            self.roles[role_name] = manifest

    def register_skill(self, name: str, description: str, content: str, tags: Optional[List[str]] = None) -> None:
        with self._lock:
            tag_list = [t.lower() for t in (tags or [])]
            tokens = set(name.lower().split() + description.lower().split() + tag_list)
            self.skills[name] = {
                "name": name,
                "description": description,
                "content": content,
                "tags": tag_list,
                "tokens": tokens,
            }

    def inject_skills_rag(self, role_name: Optional[str], query: str, limit: int = 2) -> Tuple[List[Dict[str, Any]], float]:
        start_time = time.perf_counter()
        with self._lock:
            allowed_skills = None
            if role_name and role_name in self.roles:
                role_def = self.roles[role_name]
                if isinstance(role_def, dict) and "skills" in role_def:
                    allowed_skills = set(role_def["skills"])

            query_tokens = set(query.lower().split())
            scored: List[Tuple[float, Dict[str, Any]]] = []

            for name, skill in self.skills.items():
                if allowed_skills is not None and name not in allowed_skills:
                    continue
                inter = query_tokens.intersection(skill["tokens"])
                score = len(inter) / max(1, len(query_tokens))
                for tag in skill["tags"]:
                    if tag in query.lower():
                        score += 0.5
                if score > 0:
                    scored.append((score, skill))

            scored.sort(key=lambda x: x[0], reverse=True)
            results = [s[1] for s in scored[:limit]]
            duration = time.perf_counter() - start_time
            return results, duration

# Global canonical instance
swarm_control_plane = SwarmControlPlane()
