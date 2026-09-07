# --- DNK-MRH-HEADER ---
# mrh_id: "core/canvas_engine.py"
# purpose: "Node-Based Canvas & Component Renderer with ReactFlow Export & Auto-Layout."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-08-08"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Any, Set, Tuple, Optional

class CanvasNode:
    """Represents a node in the interactive canvas with visual coordinates and styling."""
    def __init__(self, node_id: str, name: str, node_type: str, state: str = "Queued", metadata: Optional[Dict[str, Any]] = None, x: float = 0.0, y: float = 0.0):
        if node_type not in ["PatternNode", "TaskNode", "AgentNode", "DocNode"]:
            raise ValueError("Type must be one of: PatternNode, TaskNode, AgentNode, DocNode")
        if state not in ["Done", "Executing", "Blocked", "Queued"]:
            raise ValueError("State must be one of: Done, Executing, Blocked, Queued")
        
        self.id = node_id
        self.name = name
        self.type = node_type
        self.state = state
        self.metadata = metadata or {}
        self.x = x
        self.y = y

    def get_state_indicator(self) -> str:
        """Returns color state indicator as specified in the standard."""
        indicators = {
            "Done": "🟢 Done",
            "Executing": "🔵 Executing",
            "Blocked": "🔴 Blocked",
            "Queued": "🔘 Queued"
        }
        return indicators[self.state]

    def get_glassmorphism_style(self) -> Dict[str, str]:
        """Generates standard SOTA glassmorphism style for ReactFlow rendering."""
        colors = {
            "Done": "rgba(40, 167, 69, 0.2)",
            "Executing": "rgba(0, 123, 255, 0.2)",
            "Blocked": "rgba(220, 53, 69, 0.2)",
            "Queued": "rgba(108, 117, 125, 0.2)"
        }
        border_colors = {
            "Done": "rgba(40, 167, 69, 0.4)",
            "Executing": "rgba(0, 123, 255, 0.4)",
            "Blocked": "rgba(220, 53, 69, 0.4)",
            "Queued": "rgba(108, 117, 125, 0.4)"
        }
        bg = colors.get(self.state, "rgba(255, 255, 255, 0.1)")
        border = border_colors.get(self.state, "rgba(255, 255, 255, 0.2)")
        
        return {
            "background": bg,
            "backdropFilter": "blur(12px)",
            "border": f"1px solid {border}",
            "borderRadius": "12px",
            "padding": "15px",
            "color": "#ffffff",
            "boxShadow": "0 8px 32px 0 rgba(0, 0, 0, 0.37)"
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes node to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "state": self.state,
            "indicator": self.get_state_indicator(),
            "position": {"x": self.x, "y": self.y},
            "metadata": self.metadata
        }

class CanvasEngine:
    """
    CanvasEngine implements an interactive node-based canvas system
    for visual state monitoring of tasks, agents, and documents.
    """
    def __init__(self):
        self.nodes: Dict[str, CanvasNode] = {}
        self.edges: List[Tuple[str, str]] = []  # Direct links (from_id, to_id)
        self.history: List[Dict[str, Any]] = [] # Time-travel snapshots list
        self.history_cursor: int = -1           # Pointer to the current active history snapshot

    def add_node(self, node_id: str, name: str, node_type: str, state: str = "Queued", metadata: Optional[Dict[str, Any]] = None, x: float = 0.0, y: float = 0.0) -> CanvasNode:
        """Adds a new node to the canvas."""
        node = CanvasNode(node_id, name, node_type, state, metadata, x, y)
        self.nodes[node_id] = node
        return node

    def update_node_state(self, node_id: str, new_state: str) -> None:
        """Updates the execution state of a specific node."""
        if node_id not in self.nodes:
            raise KeyError(f"Node {node_id} not found on canvas")
        if new_state not in ["Done", "Executing", "Blocked", "Queued"]:
            raise ValueError("Invalid state")
        self.nodes[node_id].state = new_state

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Establishes a directed link/dependency between two nodes."""
        if from_id not in self.nodes or to_id not in self.nodes:
            raise KeyError("Both source and target nodes must exist on the canvas")
        edge = (from_id, to_id)
        if edge not in self.edges:
            self.edges.append(edge)

    def remove_edge(self, from_id: str, to_id: str) -> bool:
        """Removes a directed link/dependency if it exists."""
        edge = (from_id, to_id)
        if edge in self.edges:
            self.edges.remove(edge)
            return True
        return False

    def take_snapshot(self, description: str = "") -> int:
        """Saves a deepcopy snapshot of the current canvas state to history, resetting any forward history."""
        if self.history_cursor < len(self.history) - 1:
            self.history = self.history[:self.history_cursor + 1]

        import time
        nodes_snapshot = {}
        for nid, node in self.nodes.items():
            nodes_snapshot[nid] = CanvasNode(
                node_id=node.id,
                name=node.name,
                node_type=node.type,
                state=node.state,
                metadata=dict(node.metadata),
                x=node.x,
                y=node.y
            )
        edges_snapshot = list(self.edges)

        snapshot = {
            "timestamp": time.time(),
            "description": description,
            "nodes": nodes_snapshot,
            "edges": edges_snapshot
        }
        self.history.append(snapshot)
        self.history_cursor += 1
        return self.history_cursor

    def undo(self) -> bool:
        """Restores the previous canvas state from history. Returns True if successful."""
        if self.history_cursor <= 0:
            return False
        self.history_cursor -= 1
        snapshot = self.history[self.history_cursor]
        self._apply_snapshot(snapshot)
        return True

    def redo(self) -> bool:
        """Restores the next canvas state from history. Returns True if successful."""
        if self.history_cursor >= len(self.history) - 1:
            return False
        self.history_cursor += 1
        snapshot = self.history[self.history_cursor]
        self._apply_snapshot(snapshot)
        return True

    def _apply_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Applies a deepcopied snapshot to active state."""
        self.nodes = {}
        for nid, node in snapshot["nodes"].items():
            self.nodes[nid] = CanvasNode(
                node_id=node.id,
                name=node.name,
                node_type=node.type,
                state=node.state,
                metadata=dict(node.metadata),
                x=node.x,
                y=node.y
            )
        self.edges = list(snapshot["edges"])

    def has_cycle(self) -> bool:
        """Performs Depth First Search to detect dependency loops/cycles in the canvas."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        # Build adjacency list
        adj: Dict[str, List[str]] = {nid: [] for nid in self.nodes}
        for u, v in self.edges:
            adj[u].append(v)

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        return False

    def render_canvas_text(self) -> str:
        """Renders interactive node-based canvas as an aligned text graph."""
        lines = ["=== DNK OS CANVAS VIEW ==="]
        for node_id, node in self.nodes.items():
            out_edges = [to for f, to in self.edges if f == node_id]
            in_edges = [f for f, to in self.edges if to == node_id]
            
            line = f"[{node.type[:4]}] {node_id} ({node.name}) -> {node.get_state_indicator()}"
            if in_edges:
                line += f" | Depends on: {', '.join(in_edges)}"
            if out_edges:
                line += f" | Blocks: {', '.join(out_edges)}"
            lines.append(line)
        lines.append("==========================")
        return chr(10).join(lines)

    def calculate_auto_layout(self) -> None:
        """
        Calculates optimal non-overlapping X/Y coordinates in columns based on node types.
        Column 1: PatternNode, DocNode (X=50)
        Column 2: AgentNode (X=350)
        Column 3: TaskNode (X=650)
        """
        columns: Dict[str, List[CanvasNode]] = {
            "docs": [],
            "agents": [],
            "tasks": []
        }
        for node in self.nodes.values():
            if node.type in ["PatternNode", "DocNode"]:
                columns["docs"].append(node)
            elif node.type == "AgentNode":
                columns["agents"].append(node)
            else:
                columns["tasks"].append(node)

        # Space nodes vertically in each column (Y-offset = 180px)
        x_offsets = {"docs": 50.0, "agents": 350.0, "tasks": 650.0}
        for col_name, nodes_list in columns.items():
            x = x_offsets[col_name]
            for idx, node in enumerate(sorted(nodes_list, key=lambda n: n.id)):
                node.x = x
                node.y = 50.0 + (idx * 180.0)

    def to_reactflow_graph(self) -> Dict[str, Any]:
        """Exports canvas graph structure matching official ReactFlow expectations."""
        # Run layout to ensure coordinates are valid
        self.calculate_auto_layout()
        
        reactflow_nodes = []
        for node in self.nodes.values():
            reactflow_nodes.append({
                "id": node.id,
                "type": "custom",
                "position": {"x": node.x, "y": node.y},
                "data": {
                    "label": node.name,
                    "type": node.type,
                    "state": node.state,
                    "indicator": node.get_state_indicator(),
                    "metadata": node.metadata
                },
                "style": node.get_glassmorphism_style()
            })

        reactflow_edges = []
        for u, v in self.edges:
            reactflow_edges.append({
                "id": f"edge-{u}-{v}",
                "source": u,
                "target": v,
                "animated": True,
                "style": {"stroke": "rgba(0, 240, 255, 0.6)", "strokeWidth": 2}
            })

        return {
            "nodes": reactflow_nodes,
            "edges": reactflow_edges,
            "has_cycle": self.has_cycle()
        }

    def sync_patterns_to_nodes(self) -> List[str]:
        """Loads agentic patterns via PatternSynthesizer and syncs them into canvas nodes."""
        from pathlib import Path
        try:
            from core.pattern_synthesizer import PatternSynthesizer
            base_dir = Path(__file__).resolve().parent.parent
            registry_path = str(base_dir / "docs/tech/SPEC_02_Agentic_Patterns_Registry.md")
            schema_path = str(base_dir / "docs/schemas/agentic_pattern_schema.json")
            synthesizer = PatternSynthesizer(registry_path=registry_path, schema_path=schema_path)
            
            synced_ids = []
            for p in synthesizer.patterns:
                p_id = p.get("id")
                if not p_id:
                    continue
                node_type = "AgentNode" if p_id.startswith("DNK-AGNT") else "TaskNode"
                name = p.get("name", "Unknown Pattern")
                metadata = {
                    "type": p.get("type"),
                    "roles": p.get("roles", []),
                    "triggers": p.get("triggers", [])
                }
                self.add_node(
                    node_id=p_id,
                    name=name,
                    node_type=node_type,
                    state="Done",
                    metadata=metadata
                )
                synced_ids.append(p_id)
            return synced_ids
        except Exception as e:
            print(f"CanvasEngine: Failed to sync patterns: {e}")
            return []

    def sync_with_pattern_registry(self, registry_path: str = "docs/tech/SPEC_02_Agentic_Patterns_Registry.md") -> None:
        """
        Loads agentic patterns via PatternSynthesizer, creates PatternNode/DocNode nodes on canvas,
        and establishes sequential acyclic edges.
        """
        from core.pattern_synthesizer import PatternSynthesizer
        try:
            synthesizer = PatternSynthesizer(registry_path=registry_path)
            patterns = synthesizer.patterns
        except Exception as e:
            print(f"Failed to load registry: {e}")
            return

        sorted_patterns = sorted(patterns, key=lambda p: p.get("id", ""))
        
        # Add nodes
        for p in sorted_patterns:
            p_id = p.get("id") or p.get("pattern_id")
            if not p_id:
                continue
            name = p.get("name", "Unknown Pattern")
            # Map correctly based on prefix or metadata
            node_type = "PatternNode" if p_id.startswith("DNK-PAT") else "DocNode"
            metadata = {
                "roles": p.get("roles", []),
                "triggers": p.get("triggers", []),
                "validation_methods": p.get("validation_methods", [])
            }
            self.add_node(node_id=p_id, name=name, node_type=node_type, state="Done", metadata=metadata)

        # Connect sequentially to ensure NO CYCLES (has_cycle() remains False)
        for i in range(len(sorted_patterns) - 1):
            id_current = sorted_patterns[i].get("id") or sorted_patterns[i].get("pattern_id")
            id_next = sorted_patterns[i+1].get("id") or sorted_patterns[i+1].get("pattern_id")
            if id_current and id_next:
                self.add_edge(id_current, id_next)

    def to_dict(self) -> Dict[str, Any]:
        """Dumps total canvas state as structured dictionary."""
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [{"from": f, "to": t} for f, t in self.edges],
            "has_cycle": self.has_cycle()
        }
