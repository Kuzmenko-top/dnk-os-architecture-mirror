# --- DNK-MRH-HEADER ---
# mrh_id: "core/task_forest/forest.py"
# purpose: "Task Forest manager, graph CRUD, dependency enforcement, and canvas export."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.task_forest.models import TaskNode, ExecutionStage, NodeType, Priority
from core.task_forest.dependencies import DependencyGraph
from core.task_forest.stages import StageManager


class TaskForest:
    """
    Task Forest root manager orchestrating nodes, dependencies, stage transitions,
    and storage persistence.
    """

    def __init__(self, storage_path: str = "data/task_forest"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.nodes: Dict[str, TaskNode] = {}
        self.dependency_graph = DependencyGraph()
        self.stage_manager = StageManager()

        self._load()

    def _load(self) -> None:
        """
        Load forest from disk storage.
        """
        forest_file = self.storage_path / "forest.json"
        if forest_file.exists():
            try:
                data = json.loads(forest_file.read_text(encoding="utf-8"))
                for node_data in data.get("nodes", []):
                    node = TaskNode.from_dict(node_data)
                    self.nodes[node.id] = node
                    for dep in node.dependencies:
                        self.dependency_graph.add_dependency(node.id, dep)
            except Exception:
                pass

    def _save(self) -> None:
        """
        Save forest to disk storage.
        """
        data = {
            "nodes": [node.to_dict() for node in self.nodes.values()],
        }
        forest_file = self.storage_path / "forest.json"
        forest_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def create_node(self, node: TaskNode) -> TaskNode:
        """
        Create new node in forest.
        """
        self.nodes[node.id] = node
        for dep in node.dependencies:
            self.dependency_graph.add_dependency(node.id, dep)
        self._save()
        return node

    def add_node(
        self,
        node_or_title: Any,
        node_type: NodeType = NodeType.TASK,
        description: str = "",
        stage: ExecutionStage = ExecutionStage.BACKLOG,
        priority: Priority = Priority.MEDIUM,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None,
    ) -> TaskNode:
        """
        Add a node to the forest. Accepts either a TaskNode instance or parameters.
        """
        if isinstance(node_or_title, TaskNode):
            return self.create_node(node_or_title)

        import uuid
        nid = node_id or f"node-{uuid.uuid4().hex[:8]}"
        node = TaskNode(
            id=nid,
            title=str(node_or_title),
            description=description,
            type=node_type,
            stage=stage,
            priority=priority,
            dependencies=dependencies or [],
            tags=tags or [],
            metadata=metadata or {},
        )
        return self.create_node(node)

    def get_node(self, node_id: str) -> Optional[TaskNode]:
        """
        Get node by ID.
        """
        return self.nodes.get(node_id)

    def update_node(self, node_id: str, updates: Dict[str, Any]) -> Optional[TaskNode]:
        """
        Update node fields.
        """
        node = self.nodes.get(node_id)
        if not node:
            return None

        for key, value in updates.items():
            if hasattr(node, key):
                setattr(node, key, value)

        node.updated_at = datetime.now()
        self._save()
        return node

    def delete_node(self, node_id: str) -> bool:
        """
        Delete node (only if no other node depends on it).
        """
        if node_id not in self.nodes:
            return False

        dependents = self.dependency_graph.get_dependents(node_id)
        if dependents:
            raise ValueError(f"Cannot delete: {len(dependents)} nodes depend on this node")

        # Clean up dependencies of this node
        deps = list(self.dependency_graph.get_dependencies(node_id))
        for dep in deps:
            self.dependency_graph.remove_dependency(node_id, dep)

        del self.nodes[node_id]
        self._save()
        return True

    def add_dependency(self, from_node: str, to_node: str) -> bool:
        """
        Add dependency: from_node depends on to_node.
        """
        if from_node not in self.nodes or to_node not in self.nodes:
            return False

        if from_node == to_node:
            raise ValueError("Cannot add self-dependency")

        # Check for cycles
        self.dependency_graph.add_dependency(from_node, to_node)
        if self.dependency_graph.has_cycle():
            self.dependency_graph.remove_dependency(from_node, to_node)
            raise ValueError("Cannot add dependency: would create cycle")

        # Update node model
        if to_node not in self.nodes[from_node].dependencies:
            self.nodes[from_node].dependencies.append(to_node)
            self.nodes[from_node].updated_at = datetime.now()

        self._save()
        return True

    def remove_dependency(self, from_node: str, to_node: str) -> bool:
        """
        Remove dependency.
        """
        if from_node not in self.nodes or to_node not in self.nodes:
            return False

        self.dependency_graph.remove_dependency(from_node, to_node)
        self.nodes[from_node].dependencies = [
            dep for dep in self.nodes[from_node].dependencies if dep != to_node
        ]
        self.nodes[from_node].updated_at = datetime.now()
        self._save()
        return True

    def transition_stage(self, node_id: str, to_stage: ExecutionStage) -> bool:
        """
        Transition node to new stage. Checks that all blocking dependencies are completed (DONE).
        """
        node = self.nodes.get(node_id)
        if not node:
            return False

        # If advancing into IN_PROGRESS or REVIEW or DONE, check that dependencies are DONE
        if to_stage in (ExecutionStage.IN_PROGRESS, ExecutionStage.REVIEW, ExecutionStage.DONE):
            blocking = self.dependency_graph.get_blocking_nodes(node_id)
            for blocking_id in blocking:
                blocking_node = self.nodes.get(blocking_id)
                if blocking_node and blocking_node.stage != ExecutionStage.DONE:
                    raise ValueError(f"Cannot transition: blocked by {blocking_id} ({blocking_node.stage.value})")

        if not self.stage_manager.transition(node, to_stage):
            return False

        self._save()
        return True

    def get_nodes_by_stage(self, stage: ExecutionStage) -> List[TaskNode]:
        """
        Get all nodes in given stage.
        """
        return [node for node in self.nodes.values() if node.stage == stage]

    def get_execution_order(self) -> List[TaskNode]:
        """
        Get nodes in valid execution order (respecting dependencies).
        """
        try:
            order = self.dependency_graph.get_execution_order(list(self.nodes.keys()))
            return [self.nodes[nid] for nid in order if nid in self.nodes]
        except ValueError:
            return list(self.nodes.values())

    def to_canvas_format(self) -> Dict[str, Any]:
        """
        Convert forest to React Flow canvas format.
        """
        nodes = []
        edges = []

        for node in self.nodes.values():
            nodes.append({
                "id": node.id,
                "type": "taskNode",
                "position": node.position,
                "data": node.to_dict(),
            })

            for dep_id in node.dependencies:
                if dep_id in self.nodes:
                    edges.append({
                        "id": f"e-{dep_id}-{node.id}",
                        "source": dep_id,
                        "target": node.id,
                        "animated": node.stage == ExecutionStage.IN_PROGRESS,
                        "type": "smoothstep",
                    })

        return {
            "nodes": nodes,
            "edges": edges,
        }

    def assign_agent(self, node_id: str, agent_name: str) -> Optional[TaskNode]:
        """
        Assign a Swarm agent to a node.
        """
        node = self.nodes.get(node_id)
        if not node:
            return None
        node.assigned_agent = agent_name
        if not node.agent_status:
            node.agent_status = "idle"
        node.updated_at = datetime.now()
        self._save()
        return node

    def update_agent_status(
        self, node_id: str, status: str, run_id: Optional[str] = None
    ) -> Optional[TaskNode]:
        """
        Update execution status of the assigned Swarm agent.
        """
        node = self.nodes.get(node_id)
        if not node:
            return None
        node.agent_status = status
        if run_id:
            node.agent_run_id = run_id
        node.updated_at = datetime.now()
        self._save()
        return node

    def dispatch_agent(self, node_id: str, mode: str = "direct") -> Dict[str, Any]:
        """
        Prepare and trigger Swarm agent execution for a node.
        Advances stage to IN_PROGRESS if valid and sets agent_status to 'running'.
        """
        node = self.nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        if not node.assigned_agent:
            raise ValueError(f"Node {node_id} has no assigned agent")

        # Advance to in_progress if currently in backlog or planned
        if node.stage == ExecutionStage.BACKLOG:
            try:
                self.transition_stage(node_id, ExecutionStage.PLANNED)
                self.transition_stage(node_id, ExecutionStage.IN_PROGRESS)
            except ValueError:
                pass  # Keep current stage if blocked
        elif node.stage == ExecutionStage.PLANNED:
            try:
                self.transition_stage(node_id, ExecutionStage.IN_PROGRESS)
            except ValueError:
                pass  # Keep current stage if blocked

        node.agent_status = "running"
        node.updated_at = datetime.now()
        self._save()

        return {
            "node_id": node.id,
            "agent": node.assigned_agent,
            "stage": node.stage.value if isinstance(node.stage, Enum) else str(node.stage),
            "status": node.agent_status,
            "mode": mode,
            "task_description": f"Execute task '{node.title}': {node.description}",
        }

    def import_from_task_dna(
        self, dna_data: Dict[str, Any], base_x: float = 100.0, base_y: float = 100.0
    ) -> List[TaskNode]:
        """
        Convert a TaskDNA DAG (e.g. from dnk_decompose_task_dna) directly into Task Forest nodes and edges.
        """
        dag_items = dna_data.get("dag_tree", [])
        if not dag_items and isinstance(dna_data.get("tasks"), list):
            dag_items = dna_data.get("tasks", [])

        if not dag_items:
            return []

        # 1. Calculate topological depth for visual layered positioning
        dep_map: Dict[str, List[str]] = {}
        for item in dag_items:
            nid = item.get("id") or item.get("task_id", "")
            dep_map[nid] = list(item.get("dependencies", []))

        depth_map: Dict[str, int] = {}
        def get_depth(nid: str, visited: Optional[set] = None) -> int:
            if visited is None:
                visited = set()
            if nid in depth_map:
                return depth_map[nid]
            if nid in visited:
                return 0
            visited.add(nid)
            deps = dep_map.get(nid, [])
            if not deps:
                depth_map[nid] = 0
                return 0
            max_d = max(get_depth(d, visited.copy()) for d in deps if d in dep_map) if deps else -1
            depth_map[nid] = max_d + 1
            return depth_map[nid]

        for nid in dep_map:
            get_depth(nid)

        level_counts: Dict[int, int] = {}
        created_nodes: List[TaskNode] = []

        for item in dag_items:
            nid = item.get("id") or item.get("task_id")
            title = item.get("title", f"Task {nid}")
            desc = item.get("description", item.get("rationale", ""))
            agent = item.get("assigned_agent") or item.get("agent")
            risk = str(item.get("risk_level", "medium")).lower()

            # Priority mapping
            if risk in ("critical", "urgent"):
                priority = Priority.CRITICAL
            elif risk == "high":
                priority = Priority.HIGH
            elif risk == "low":
                priority = Priority.LOW
            else:
                priority = Priority.MEDIUM

            # Infer NodeType from title & desc
            lower_text = f"{title} {desc}".lower()
            if "bug" in lower_text or "fix" in lower_text:
                node_type = NodeType.BUG
            elif "idea" in lower_text or "hypothesis" in lower_text:
                node_type = NodeType.IDEA
            elif "goal" in lower_text or "milestone" in lower_text:
                node_type = NodeType.GOAL
            elif "doc" in lower_text or "specification" in lower_text or "audit" in lower_text:
                node_type = NodeType.DOCUMENTATION
            else:
                node_type = NodeType.TASK

            # Layout coordinates
            depth = depth_map.get(nid, 0)
            row_idx = level_counts.get(depth, 0)
            level_counts[depth] = row_idx + 1

            pos_x = base_x + (depth * 320.0)
            pos_y = base_y + (row_idx * 200.0)

            node = TaskNode(
                id=nid,
                title=title,
                description=desc,
                type=node_type,
                stage=ExecutionStage.BACKLOG,
                priority=priority,
                dependencies=list(item.get("dependencies", [])),
                tags=["task_dna", f"risk_{risk}"],
                assigned_agent=agent,
                agent_status="idle" if agent else None,
                metadata={
                    "task_dna_id": dna_data.get("task_id", ""),
                    "risk_level": risk,
                },
                position={"x": pos_x, "y": pos_y},
            )

            created_node = self.add_node(node)
            created_nodes.append(created_node)

        # Wire all dependencies into the graph
        for node in created_nodes:
            for dep in node.dependencies:
                if dep in self.nodes:
                    try:
                        self.add_dependency(node.id, dep)
                    except ValueError:
                        pass

        self._save()
        return created_nodes

