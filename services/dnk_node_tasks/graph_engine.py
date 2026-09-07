# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_node_tasks/graph_engine.py"
# purpose: "Graph Engine with DAG Dependency Verification, Cycle Detection, Stage Gating & Rollup"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple, Any

from .models import (
    NodeType,
    ExecutionStage,
    NodeStatus,
    EdgeRelation,
    DependencyEdge,
    NodePosition,
    NodeItem,
    NodeTaskGraph,
    GraphStatistics,
    IdeaConversionRequest,
)


class NodeTaskGraphEngine:
    """Core mathematical and business logic for Node-based Tasks & Ideas."""

    @staticmethod
    def detect_cycle_with_new_edge(
        existing_edges: List[DependencyEdge],
        new_source: str,
        new_target: str,
        relation: EdgeRelation = EdgeRelation.DEPENDS_ON
    ) -> Tuple[bool, List[str]]:
        """
        Check if adding an edge from new_source -> new_target creates a cycle
        in the DAG dependency structure (where source precedes target).
        Returns: (has_cycle: bool, cycle_path: List[str])
        """
        if new_source == new_target:
            return True, [new_source, new_target]

        # Only directional dependency relationships cause DAG blocking cycles
        if relation not in (EdgeRelation.DEPENDS_ON, EdgeRelation.BLOCKS, EdgeRelation.PARENT_OF):
            return False, []

        adj = defaultdict(list)
        for e in existing_edges:
            if e.relation in (EdgeRelation.DEPENDS_ON, EdgeRelation.BLOCKS, EdgeRelation.PARENT_OF):
                adj[e.source].append(e.target)
        adj[new_source].append(new_target)

        # Run BFS/DFS from new_target to see if it can reach new_source
        queue = deque([[new_target]])
        visited = set()

        while queue:
            path = queue.popleft()
            curr = path[-1]
            if curr == new_source:
                return True, [new_source] + path

            if curr not in visited:
                visited.add(curr)
                for neighbor in adj.get(curr, []):
                    queue.append(path + [neighbor])

        return False, []

    @classmethod
    def recalculate_graph_dependencies(cls, graph: NodeTaskGraph) -> None:
        """
        Recalculate dynamic DAG fields for all nodes:
        - `is_blocked`: True if any prerequisite node is not completed.
        - `blocked_by`: List of prerequisite node IDs that are incomplete.
        - Hierarchical progress rollup if parent-child edges exist.
        """
        # Map: target_node_id -> list of prerequisite source_node_ids
        prereqs: Dict[str, List[str]] = defaultdict(list)
        parent_children: Dict[str, List[str]] = defaultdict(list)

        for edge in graph.edges:
            if edge.relation in (EdgeRelation.DEPENDS_ON, EdgeRelation.BLOCKS):
                # Edge source is prerequisite, target depends on it
                prereqs[edge.target].append(edge.source)
            elif edge.relation == EdgeRelation.PARENT_OF:
                parent_children[edge.source].append(edge.target)

        # Update blocked states
        for node_id, node in graph.nodes.items():
            sources = prereqs.get(node_id, [])
            incomplete = []
            for s_id in sources:
                s_node = graph.nodes.get(s_id)
                if not s_node:
                    continue
                # If prerequisite is not completed and progress < 100, it blocks
                if s_node.status != NodeStatus.COMPLETED and s_node.progress < 100.0:
                    incomplete.append(s_id)

            node.blocked_by = incomplete
            node.is_blocked = len(incomplete) > 0

            # If node status was ready or backlog, update status reflection
            if node.is_blocked and node.status == NodeStatus.READY:
                node.status = NodeStatus.BLOCKED
            elif not node.is_blocked and node.status == NodeStatus.BLOCKED:
                node.status = NodeStatus.READY

        # Perform rollup for parent nodes
        for parent_id, child_ids in parent_children.items():
            parent_node = graph.nodes.get(parent_id)
            if not parent_node or not child_ids:
                continue
            child_nodes = [graph.nodes[c] for c in child_ids if c in graph.nodes]
            if child_nodes:
                avg_progress = sum(c.progress for c in child_nodes) / len(child_nodes)
                parent_node.progress = round(avg_progress, 1)
                if avg_progress >= 100.0 and parent_node.status != NodeStatus.CANCELLED:
                    parent_node.status = NodeStatus.COMPLETED
                    parent_node.stage = ExecutionStage.COMPLETED

    @classmethod
    def can_transition_stage(
        cls,
        node: NodeItem,
        target_stage: ExecutionStage,
        graph: NodeTaskGraph,
        force: bool = False
    ) -> Tuple[bool, str]:
        """
        Validates if node is allowed to transition to target_stage.
        """
        if force:
            return True, "Forced transition approved"

        # Rule 1: Cannot move to IN_PROGRESS or READY if blocked by dependencies
        if target_stage in (ExecutionStage.READY, ExecutionStage.IN_PROGRESS):
            if node.is_blocked:
                blocker_titles = [
                    graph.nodes[bid].title for bid in node.blocked_by if bid in graph.nodes
                ]
                return (
                    False,
                    f"Node is blocked by incomplete prerequisite tasks: {', '.join(blocker_titles or node.blocked_by)}"
                )

        # Rule 2: Cannot complete if any validating gate is not satisfied
        if target_stage == ExecutionStage.COMPLETED:
            for edge in graph.edges:
                if edge.target == node.id and edge.relation == EdgeRelation.VALIDATES:
                    gate_node = graph.nodes.get(edge.source)
                    if gate_node and gate_node.status != NodeStatus.COMPLETED:
                        return False, f"Verification gate '{gate_node.title}' must be completed first."

        return True, "Transition allowed"

    @classmethod
    def convert_idea_to_task(
        cls,
        graph: NodeTaskGraph,
        req: IdeaConversionRequest
    ) -> Tuple[NodeItem, DependencyEdge]:
        """
        Transforms an idea into an executable Task or Epic node,
        creating an evolutionary SPAWNS_FROM edge.
        """
        idea = graph.nodes.get(req.idea_id)
        if not idea:
            raise ValueError(f"Idea node '{req.idea_id}' not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        new_task_id = f"task-{req.target_module or 'core'}-{int(datetime.now().timestamp() * 1000) % 100000:05d}"
        task_title = req.new_task_title or f"Implement: {idea.title}"

        # Position slightly offset to the right of the idea
        pos_x = idea.position.x + 320.0
        pos_y = idea.position.y + 40.0

        new_task = NodeItem(
            id=new_task_id,
            title=task_title,
            description=f"Engineered from idea: {idea.description}",
            node_type=req.node_type,
            stage=ExecutionStage.ARCHITECTURE,
            status=NodeStatus.READY,
            progress=0.0,
            assigned_agent=req.assigned_agent or "gerych_builder",
            target_module=req.target_module or "core",
            target_files=req.target_files or [],
            tags=list(set(idea.tags + ["spawned_from_idea"])),
            position=NodePosition(x=pos_x, y=pos_y),
            created_at=now_iso,
            updated_at=now_iso
        )

        edge_id = f"edge-{idea.id}-to-{new_task_id}"
        spawn_edge = DependencyEdge(
            id=edge_id,
            source=idea.id,
            target=new_task_id,
            relation=EdgeRelation.SPAWNS_FROM,
            description="Task spawned from Idea node"
        )

        # Mark Idea as completed/converted
        idea.status = NodeStatus.COMPLETED
        idea.stage = ExecutionStage.COMPLETED
        if "converted" not in idea.tags:
            idea.tags.append("converted")
        idea.updated_at = now_iso

        graph.nodes[new_task_id] = new_task
        graph.edges.append(spawn_edge)
        graph.updated_at = now_iso

        cls.recalculate_graph_dependencies(graph)
        return new_task, spawn_edge

    @classmethod
    def get_topological_execution_order(cls, graph: NodeTaskGraph) -> List[str]:
        """
        Kahn's Algorithm for topological sorting of executable nodes.
        """
        in_degree = defaultdict(int)
        adj = defaultdict(list)

        node_ids = set(graph.nodes.keys())
        for nid in node_ids:
            in_degree[nid] = 0

        for edge in graph.edges:
            if edge.relation in (EdgeRelation.DEPENDS_ON, EdgeRelation.BLOCKS):
                if edge.source in node_ids and edge.target in node_ids:
                    adj[edge.source].append(edge.target)
                    in_degree[edge.target] += 1

        queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
        order = []

        while queue:
            curr = queue.popleft()
            order.append(curr)
            for neighbor in adj.get(curr, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order

    @classmethod
    def compute_critical_path(cls, graph: NodeTaskGraph) -> Dict[str, Any]:
        """
        Calculates the Critical Path Method (CPM) for the task DAG.
        Computes ES (Early Start), EF (Early Finish), LS (Late Start), LF (Late Finish),
        and Float/Slack to identify critical path tasks and blocking bottlenecks.
        """
        node_ids = set(graph.nodes.keys())
        if not node_ids:
            return {
                "critical_path_node_ids": [],
                "critical_edge_ids": [],
                "total_duration_hours": 0.0,
                "bottlenecks": [],
                "node_metrics": {}
            }

        duration: Dict[str, float] = {}
        for nid, node in graph.nodes.items():
            if node.status == NodeStatus.COMPLETED or node.stage == ExecutionStage.COMPLETED:
                d = 0.0
            else:
                p_map = {"critical": 8.0, "high": 5.0, "medium": 3.0, "low": 1.0}
                base = p_map.get(str(node.priority).lower(), 3.0)
                if node.node_type == NodeType.EPIC:
                    base = max(base, 10.0)
                elif node.node_type == NodeType.GATE:
                    base = 1.0
                rem_factor = max(0.0, (100.0 - float(node.progress)) / 100.0)
                d = max(0.5, round(base * rem_factor, 1)) if rem_factor > 0 else 0.0
            duration[nid] = d

        preds = defaultdict(list)
        succs = defaultdict(list)
        edge_map = {}

        for edge in graph.edges:
            if edge.relation in (EdgeRelation.DEPENDS_ON, EdgeRelation.BLOCKS, EdgeRelation.SPAWNS_FROM):
                if edge.source in node_ids and edge.target in node_ids:
                    preds[edge.target].append(edge.source)
                    succs[edge.source].append(edge.target)
                    edge_map[(edge.source, edge.target)] = edge.id

        topo_order = cls.get_topological_execution_order(graph)
        es: Dict[str, float] = {}
        ef: Dict[str, float] = {}

        for nid in topo_order:
            if not preds[nid]:
                es[nid] = 0.0
            else:
                es[nid] = max(ef.get(p, 0.0) for p in preds[nid])
            ef[nid] = round(es[nid] + duration[nid], 2)

        max_duration = max(ef.values()) if ef else 0.0

        lf: Dict[str, float] = {}
        ls: Dict[str, float] = {}

        for nid in reversed(topo_order):
            if not succs[nid]:
                lf[nid] = max_duration
            else:
                lf[nid] = min(ls.get(s, max_duration) for s in succs[nid])
            ls[nid] = round(lf[nid] - duration[nid], 2)

        critical_nodes = []
        node_metrics = {}

        for nid in topo_order:
            slack = round(ls.get(nid, 0.0) - es.get(nid, 0.0), 2)
            is_crit = abs(slack) < 0.05 and duration.get(nid, 0.0) > 0
            node_metrics[nid] = {
                "duration_hours": duration.get(nid, 0.0),
                "early_start": es.get(nid, 0.0),
                "early_finish": ef.get(nid, 0.0),
                "late_start": ls.get(nid, 0.0),
                "late_finish": lf.get(nid, 0.0),
                "slack": slack,
                "is_critical": is_crit
            }
            if is_crit:
                critical_nodes.append(nid)

        critical_edge_ids = []
        for (u, v), eid in edge_map.items():
            if u in critical_nodes and v in critical_nodes:
                if abs(ef.get(u, 0.0) - es.get(v, 0.0)) < 0.05:
                    critical_edge_ids.append(eid)

        bottlenecks = []
        for nid in critical_nodes:
            downstream_count = len(succs[nid])
            node_item = graph.nodes[nid]
            if downstream_count > 0 or node_metrics[nid]["duration_hours"] >= 5.0:
                bottlenecks.append({
                    "node_id": nid,
                    "title": node_item.title,
                    "assigned_agent": node_item.assigned_agent,
                    "blocking_count": downstream_count,
                    "duration_hours": node_metrics[nid]["duration_hours"],
                    "priority": node_item.priority
                })

        bottlenecks.sort(key=lambda x: (x["blocking_count"], x["duration_hours"]), reverse=True)

        return {
            "critical_path_node_ids": critical_nodes,
            "critical_edge_ids": critical_edge_ids,
            "total_duration_hours": round(max_duration, 1),
            "bottlenecks": bottlenecks,
            "node_metrics": node_metrics
        }

    @classmethod
    def compute_statistics(cls, graph: NodeTaskGraph) -> GraphStatistics:
        total = len(graph.nodes)
        ideas = sum(1 for n in graph.nodes.values() if n.node_type == NodeType.IDEA)
        epics = sum(1 for n in graph.nodes.values() if n.node_type == NodeType.EPIC)
        tasks = sum(1 for n in graph.nodes.values() if n.node_type == NodeType.TASK)
        slices = sum(1 for n in graph.nodes.values() if n.node_type == NodeType.SLICE)
        gates = sum(1 for n in graph.nodes.values() if n.node_type == NodeType.GATE)

        blocked = sum(1 for n in graph.nodes.values() if n.is_blocked)
        ready = sum(1 for n in graph.nodes.values() if n.status == NodeStatus.READY)
        in_prog = sum(1 for n in graph.nodes.values() if n.status == NodeStatus.IN_PROGRESS)
        completed = sum(1 for n in graph.nodes.values() if n.status == NodeStatus.COMPLETED)

        avg_prog = sum(n.progress for n in graph.nodes.values()) / total if total > 0 else 0.0

        workload: Dict[str, int] = defaultdict(int)
        for n in graph.nodes.values():
            if n.status != NodeStatus.COMPLETED:
                agent = n.assigned_agent or "unassigned"
                workload[agent] += 1

        return GraphStatistics(
            total_nodes=total,
            ideas_count=ideas,
            epics_count=epics,
            tasks_count=tasks,
            slices_count=slices,
            gates_count=gates,
            blocked_count=blocked,
            ready_count=ready,
            in_progress_count=in_prog,
            completed_count=completed,
            overall_progress=round(avg_prog, 1),
            agent_workload=dict(workload),
            by_type={
                "idea": ideas,
                "epic": epics,
                "task": tasks,
                "slice": slices,
                "gate": gates,
            },
            by_stage={
                "ready": ready,
                "in_progress": in_prog,
                "completed": completed,
            },
            blocked_nodes_count=blocked,
            overall_progress_pct=round(avg_prog, 1),
        )

    @classmethod
    def compute_auto_layout(cls, graph: NodeTaskGraph) -> Dict[str, NodePosition]:
        """
        Computes non-overlapping topological DAG coordinates (x, y) for all nodes.
        Uses topological level grouping with horizontal pitch 440px and vertical pitch 280px.
        Updates node.position in place and returns the mapping of node_id -> NodePosition.
        """
        node_ids = set(graph.nodes.keys())
        if not node_ids:
            return {}

        in_degree: Dict[str, int] = {nid: 0 for nid in node_ids}
        adj: Dict[str, List[str]] = {nid: [] for nid in node_ids}

        for edge in graph.edges:
            if edge.relation in (EdgeRelation.DEPENDS_ON, EdgeRelation.BLOCKS, EdgeRelation.PARENT_OF):
                if edge.source in node_ids and edge.target in node_ids:
                    adj[edge.source].append(edge.target)
                    in_degree[edge.target] += 1

        depth: Dict[str, int] = {}
        queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
        for nid in queue:
            depth[nid] = 0

        visited = set(queue)
        while queue:
            curr = queue.popleft()
            curr_depth = depth[curr]
            for neighbor in adj.get(curr, []):
                depth[neighbor] = max(depth.get(neighbor, 0), curr_depth + 1)
                in_degree[neighbor] -= 1
                if in_degree[neighbor] <= 0 and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        # Handle any remaining unvisited nodes (cycles or isolated)
        for nid in node_ids:
            if nid not in depth:
                node = graph.nodes[nid]
                if node.node_type == NodeType.IDEA:
                    depth[nid] = 0
                elif node.node_type == NodeType.EPIC:
                    depth[nid] = 0
                elif node.node_type == NodeType.GATE:
                    depth[nid] = 3
                else:
                    depth[nid] = 1

        # Group nodes by depth
        levels: Dict[int, List[str]] = defaultdict(list)
        for nid, d in depth.items():
            levels[d].append(nid)

        # Sort within levels: IDEAS first, then EPICS, then TASKS, then GATES
        type_priority = {NodeType.IDEA: 0, NodeType.EPIC: 1, NodeType.TASK: 2, NodeType.SLICE: 3, NodeType.GATE: 4}
        for d in levels:
            levels[d].sort(key=lambda nid: (type_priority.get(graph.nodes[nid].node_type, 2), graph.nodes[nid].title))

        positions: Dict[str, NodePosition] = {}
        horizontal_pitch = 440.0
        vertical_pitch = 280.0
        base_x = 60.0
        base_y = 80.0

        for d, nids in sorted(levels.items()):
            col_x = base_x + (d * horizontal_pitch)
            for idx, nid in enumerate(nids):
                row_y = base_y + (idx * vertical_pitch)
                pos = NodePosition(x=col_x, y=row_y)
                graph.nodes[nid].position = pos
                positions[nid] = pos

        return positions
