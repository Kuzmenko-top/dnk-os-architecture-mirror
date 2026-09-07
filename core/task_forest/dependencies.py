# --- DNK-MRH-HEADER ---
# mrh_id: "core/task_forest/dependencies.py"
# purpose: "Task Forest dependency graph, cycle detection, and topological sorting."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Set
from collections import defaultdict, deque


class DependencyGraph:
    """
    Directed graph managing dependencies between task nodes.
    An edge (from_node -> to_node) signifies: from_node depends on to_node
    (i.e., to_node must complete before from_node can execute).
    """

    def __init__(self):
        self.graph: Dict[str, Set[str]] = defaultdict(set)  # node -> dependencies
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)  # node -> dependents

    def add_dependency(self, from_node: str, to_node: str) -> None:
        """
        Add dependency: from_node depends on to_node (to_node blocks from_node).
        """
        self.graph[from_node].add(to_node)
        self.reverse_graph[to_node].add(from_node)

    def remove_dependency(self, from_node: str, to_node: str) -> None:
        """
        Remove dependency.
        """
        self.graph[from_node].discard(to_node)
        self.reverse_graph[to_node].discard(from_node)

    def get_dependencies(self, node_id: str) -> Set[str]:
        """
        Get all nodes that this node depends on directly.
        """
        return set(self.graph.get(node_id, set()))

    def get_dependents(self, node_id: str) -> Set[str]:
        """
        Get all nodes that depend directly on this node.
        """
        return set(self.reverse_graph.get(node_id, set()))

    def has_cycle(self) -> bool:
        """
        Detect cycles in dependency graph using DFS with recursion stack.
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        all_nodes = set(self.graph.keys()) | set(self.reverse_graph.keys())

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in all_nodes:
            if node not in visited:
                if dfs(node):
                    return True

        return False

    def topological_sort(self) -> List[str]:
        """
        Return topological order of nodes (respecting dependencies).
        Independent/blocking nodes come first.
        Raises ValueError if cycle detected.
        """
        if self.has_cycle():
            raise ValueError("Cannot sort: dependency cycle detected")

        all_nodes = set(self.graph.keys()) | set(self.reverse_graph.keys())
        if not all_nodes:
            return []

        # in_degree: number of unsatisfied dependencies for each node
        in_degree: Dict[str, int] = {node: len(self.graph.get(node, set())) for node in all_nodes}

        # Start with nodes that have 0 dependencies
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
        result: List[str] = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # Node completed: notify dependents
            for dependent in self.reverse_graph.get(node, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(all_nodes):
            raise ValueError("Cycle detected in dependency graph")

        return result

    def get_blocking_nodes(self, node_id: str) -> Set[str]:
        """
        Get all nodes that block this node (direct + transitive dependencies).
        """
        blocking: Set[str] = set()
        queue = deque([node_id])

        while queue:
            current = queue.popleft()
            for dep in self.graph.get(current, set()):
                if dep not in blocking:
                    blocking.add(dep)
                    queue.append(dep)

        return blocking

    def get_execution_order(self, node_ids: List[str]) -> List[str]:
        """
        Get valid execution order for given nodes (respecting dependencies).
        """
        node_set = set(node_ids)
        subgraph = DependencyGraph()
        for node in node_ids:
            for dep in self.graph.get(node, set()):
                if dep in node_set:
                    subgraph.add_dependency(node, dep)

        # Ensure all node_ids are registered in the subgraph
        all_sub_nodes = set(subgraph.graph.keys()) | set(subgraph.reverse_graph.keys())
        isolated_nodes = [n for n in node_ids if n not in all_sub_nodes]

        sorted_nodes = subgraph.topological_sort() if all_sub_nodes else []
        return isolated_nodes + sorted_nodes
