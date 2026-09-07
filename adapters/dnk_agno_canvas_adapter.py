# --- DNK-MRH-HEADER ---
# mrh_id: "adapters/dnk_agno_canvas_adapter.py"
# purpose: "Hexagonal bidirectional adapter bridging Agno multi-agent and workflow DAG primitives with DNK OS Infinite Canvas"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-AGNO-CANVAS-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

"""
DNK Agno Canvas Adapter for Gerych Core & Spatial Multi-Agent Orchestration.

Provides bidirectional translation and runtime execution between Agno Agent, Team,
and Workflow primitives and the DNK OS Infinite Canvas AST graph.
Supports asynchronous Human-in-the-Loop (HITL) checkpoints, SCONES memory sync,
and sandboxed tool execution.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Set, Union
import uuid

logger = logging.getLogger("DnkAgnoCanvasAdapter")


class CanvasNodeType(str, Enum):
    AGENT = "agent"
    TEAM = "team"
    WORKFLOW_STEP = "workflow_step"
    MEMORY = "memory"
    TOOL = "tool"
    HITL_GATE = "hitl_gate"
    CONDITION = "condition"


class AgnoTeamMode(str, Enum):
    ROUTE = "route"
    BROADCAST = "broadcast"
    TASKS = "tasks"
    CONSENSUS = "consensus"


class CanvasNodeStatus(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED_HITL = "paused_hitl"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CanvasNodeConfig:
    node_id: str
    node_type: CanvasNodeType = CanvasNodeType.AGENT
    title: str = "Untitled Node"
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    agent_name: Optional[str] = None
    model_id: str = "gemini-2.5-pro"
    instructions: Optional[str] = None
    team_mode: AgnoTeamMode = AgnoTeamMode.ROUTE
    member_agents: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    requires_hitl: bool = False
    hitl_threshold_tokens: Optional[int] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    memory_workspace: str = "ws-alpha-001"
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["node_type"] = self.node_type.value if isinstance(self.node_type, CanvasNodeType) else self.node_type
        data["team_mode"] = self.team_mode.value if isinstance(self.team_mode, AgnoTeamMode) else self.team_mode
        return data


@dataclass
class CanvasEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    source_port: str = "output"
    target_port: str = "input"
    condition_expr: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HITLCheckpoint:
    checkpoint_id: str
    graph_id: str
    node_id: str
    paused_at_timestamp: float
    reason: str
    pending_action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # "pending", "approved", "rejected"
    user_feedback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NodeExecutionResult:
    node_id: str
    status: CanvasNodeStatus
    output_data: Optional[Dict[str, Any]] = None
    tokens_consumed: int = 0
    duration_ms: float = 0.0
    checkpoint_id: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value if isinstance(self.status, CanvasNodeStatus) else self.status
        return data


class DnkAgnoCanvasAdapter:
    """
    Hexagonal adapter that executes Agno Agent, Team, and Workflow DAGs
    directly over the DNK OS Infinite Canvas AST.
    """

    DANGEROUS_ACTIONS = {
        "deploy_shopify_theme",
        "delete_file",
        "drop_table",
        "git_push_force",
        "execute_raw_shell",
        "payment_charge",
    }

    def __init__(self, scone_memory_store: Optional[Dict[str, Any]] = None):
        self.memory_store: Dict[str, List[Dict[str, Any]]] = scone_memory_store if scone_memory_store is not None else defaultdict(list)
        self.checkpoints: Dict[str, HITLCheckpoint] = {}
        self.execution_cache: Dict[str, NodeExecutionResult] = {}
        self.tool_handlers: Dict[str, Callable[..., Any]] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """Registers built-in mock and safe tool handlers."""
        self.tool_handlers["extract_keywords"] = lambda text: {"keywords": [w.strip() for w in text.split() if len(w) > 4]}
        self.tool_handlers["format_markdown"] = lambda content: {"formatted": f"# Report\n\n{content}"}
        self.tool_handlers["validate_liquid"] = lambda code: {"valid": True, "errors": []}

    def register_tool(self, tool_name: str, handler: Callable[..., Any]):
        """Registers an external tool handler or MCP adapter."""
        self.tool_handlers[tool_name] = handler

    def validate_graph(self, graph_data: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
        """
        Validates graph topology, node integrity, and detects circular dependencies.
        """
        nodes_raw = graph_data.get("nodes", []) if isinstance(graph_data, dict) else getattr(graph_data, "nodes", [])
        edges_raw = graph_data.get("edges", []) if isinstance(graph_data, dict) else getattr(graph_data, "edges", [])

        node_ids: Set[str] = set()
        for n in nodes_raw:
            nid = n.get("node_id") if isinstance(n, dict) else getattr(n, "node_id", None)
            if not nid:
                return {"valid": False, "error": "Node missing node_id"}
            if nid in node_ids:
                return {"valid": False, "error": f"Duplicate node_id: {nid}"}
            node_ids.add(str(nid))

        # Build adjacency and check for unknown target/sources
        adj: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = defaultdict(int)
        for nid in node_ids:
            in_degree[nid] = 0

        for e in edges_raw:
            src = str(e.get("source_node_id") if isinstance(e, dict) else getattr(e, "source_node_id", ""))
            tgt = str(e.get("target_node_id") if isinstance(e, dict) else getattr(e, "target_node_id", ""))
            if src not in node_ids or tgt not in node_ids:
                return {"valid": False, "error": f"Edge references nonexistent node: {src} -> {tgt}"}
            adj[src].append(tgt)
            in_degree[tgt] += 1

        # Cycle detection using Kahn's algorithm
        queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
        visited_count = 0
        while queue:
            curr = queue.popleft()
            visited_count += 1
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(node_ids):
            return {"valid": False, "error": "Circular dependency detected in Canvas DAG"}

        return {"valid": True, "node_count": len(node_ids), "edge_count": len(edges_raw)}

    def compile_topological_dag(self, graph_data: Dict[str, Any]) -> List[CanvasNodeConfig]:
        """
        Compiles the canvas nodes into a topologically sorted execution order.
        """
        nodes_map: Dict[str, CanvasNodeConfig] = {}
        for n in graph_data.get("nodes", []):
            if isinstance(n, CanvasNodeConfig):
                config = n
            else:
                ntype = CanvasNodeType(n.get("node_type", "agent"))
                tmode = AgnoTeamMode(n.get("team_mode", "route"))
                config = CanvasNodeConfig(
                    node_id=n["node_id"],
                    node_type=ntype,
                    title=n.get("title", "Untitled Node"),
                    position=n.get("position", {"x": 0.0, "y": 0.0}),
                    agent_name=n.get("agent_name"),
                    model_id=n.get("model_id", "gemini-2.5-pro"),
                    instructions=n.get("instructions"),
                    team_mode=tmode,
                    member_agents=n.get("member_agents", []),
                    tools=n.get("tools", []),
                    requires_hitl=n.get("requires_hitl", False),
                    hitl_threshold_tokens=n.get("hitl_threshold_tokens"),
                    input_schema=n.get("input_schema"),
                    output_schema=n.get("output_schema"),
                    memory_workspace=n.get("memory_workspace", "ws-alpha-001"),
                    custom_metadata=n.get("custom_metadata", {}),
                )
            nodes_map[config.node_id] = config

        adj: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = {nid: 0 for nid in nodes_map}
        for e in graph_data.get("edges", []):
            src = str(e.get("source_node_id") if isinstance(e, dict) else e.source_node_id)
            tgt = str(e.get("target_node_id") if isinstance(e, dict) else e.target_node_id)
            adj[src].append(tgt)
            in_degree[tgt] += 1

        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        sorted_nodes: List[CanvasNodeConfig] = []
        while queue:
            curr_id = queue.popleft()
            sorted_nodes.append(nodes_map[curr_id])
            for nxt_id in adj[curr_id]:
                in_degree[nxt_id] -= 1
                if in_degree[nxt_id] == 0:
                    queue.append(nxt_id)

        return sorted_nodes

    def create_hitl_checkpoint(
        self,
        graph_id: str,
        node_id: str,
        reason: str,
        pending_action: str,
        parameters: Optional[Dict[str, Any]] = None,
        state_snapshot: Optional[Dict[str, Any]] = None,
    ) -> HITLCheckpoint:
        """
        Suspends execution by generating a serializable HITL checkpoint.
        """
        cid = f"chk_{uuid.uuid4().hex[:8]}"
        checkpoint = HITLCheckpoint(
            checkpoint_id=cid,
            graph_id=graph_id,
            node_id=node_id,
            paused_at_timestamp=time.time(),
            reason=reason,
            pending_action=pending_action,
            parameters=parameters or {},
            state_snapshot=state_snapshot or {},
            status="pending",
        )
        self.checkpoints[cid] = checkpoint
        logger.info(f"Created HITL Checkpoint {cid} on Node {node_id}: {reason}")
        return checkpoint

    def resume_hitl_checkpoint(
        self,
        checkpoint_id: str,
        decision: str,
        modified_parameters: Optional[Dict[str, Any]] = None,
        user_comment: Optional[str] = None,
    ) -> NodeExecutionResult:
        """
        Resumes a paused checkpoint with user approval or rejection.
        """
        if checkpoint_id not in self.checkpoints:
            return NodeExecutionResult(
                node_id="unknown",
                status=CanvasNodeStatus.FAILED,
                error_message=f"Checkpoint {checkpoint_id} not found",
            )

        chk = self.checkpoints[checkpoint_id]
        chk.status = "approved" if decision == "approve" else "rejected"
        chk.user_feedback = user_comment

        if decision == "reject":
            return NodeExecutionResult(
                node_id=chk.node_id,
                status=CanvasNodeStatus.FAILED,
                error_message=f"Action '{chk.pending_action}' rejected by user: {user_comment or 'No reason provided'}",
                checkpoint_id=checkpoint_id,
            )

        # Execute approved action with modified parameters if provided
        final_params = modified_parameters if modified_parameters is not None else chk.parameters
        action = chk.pending_action

        start_time = time.time()
        try:
            if action in self.tool_handlers:
                output = self.tool_handlers[action](**final_params)
            else:
                output = {
                    "action_executed": action,
                    "params": final_params,
                    "approved": True,
                    "result": "success",
                }

            duration_ms = (time.time() - start_time) * 1000
            return NodeExecutionResult(
                node_id=chk.node_id,
                status=CanvasNodeStatus.COMPLETED,
                output_data={"result": output, "checkpoint_id": checkpoint_id},
                tokens_consumed=150,
                duration_ms=duration_ms,
                checkpoint_id=checkpoint_id,
            )
        except Exception as e:
            return NodeExecutionResult(
                node_id=chk.node_id,
                status=CanvasNodeStatus.FAILED,
                error_message=str(e),
                checkpoint_id=checkpoint_id,
            )

    def sync_memory(
        self,
        workspace_id: str,
        node_id: str,
        facts: Dict[str, Any],
    ) -> bool:
        """
        Synchronizes memory facts from a canvas node run into the workspace memory store.
        """
        entry = {
            "node_id": node_id,
            "timestamp": time.time(),
            "facts": facts,
        }
        self.memory_store[workspace_id].append(entry)
        return True

    def get_workspace_memories(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Returns all recorded memories for a workspace."""
        return self.memory_store.get(workspace_id, [])

    def _execute_agent_node(
        self,
        node: CanvasNodeConfig,
        inputs: Dict[str, Any],
        graph_id: str,
    ) -> NodeExecutionResult:
        """Simulates Agno Agent execution with instruction processing and tool calls."""
        start_time = time.time()
        prompt = str(inputs.get("prompt") or inputs.get("content") or inputs.get("input") or "")

        # Check for dangerous tool calls triggering HITL
        for tool in node.tools:
            if tool in self.DANGEROUS_ACTIONS or node.requires_hitl:
                chk = self.create_hitl_checkpoint(
                    graph_id=graph_id,
                    node_id=node.node_id,
                    reason=f"Agent '{node.agent_name or node.title}' requires approval to run '{tool}'",
                    pending_action=tool,
                    parameters={"prompt": prompt, "inputs": inputs},
                    state_snapshot={"inputs": inputs, "node": node.to_dict()},
                )
                return NodeExecutionResult(
                    node_id=node.node_id,
                    status=CanvasNodeStatus.PAUSED_HITL,
                    checkpoint_id=chk.checkpoint_id,
                    tokens_consumed=50,
                )

        # Pull memories from workspace
        memories = self.get_workspace_memories(node.memory_workspace)
        context_str = f" [Memories: {len(memories)} entries]" if memories else ""

        # Execute safe tools if registered
        tool_results = {}
        for tool in node.tools:
            if tool in self.tool_handlers:
                tool_results[tool] = self.tool_handlers[tool](prompt)

        response_text = f"Agent '{node.agent_name or node.title}' processed input successfully using {node.model_id}.{context_str}"
        output = {
            "response": response_text,
            "agent": node.agent_name or node.title,
            "model": node.model_id,
            "tool_results": tool_results,
            "received_inputs": inputs,
        }

        # Auto-record memory if enabled
        if node.custom_metadata.get("auto_record_memory", True):
            self.sync_memory(node.memory_workspace, node.node_id, {"summary": response_text})

        duration_ms = (time.time() - start_time) * 1000
        return NodeExecutionResult(
            node_id=node.node_id,
            status=CanvasNodeStatus.COMPLETED,
            output_data=output,
            tokens_consumed=420,
            duration_ms=duration_ms,
        )

    def _execute_team_node(
        self,
        node: CanvasNodeConfig,
        inputs: Dict[str, Any],
        graph_id: str,
    ) -> NodeExecutionResult:
        """Executes an Agno Multi-Agent Team with Route, Broadcast, Tasks, or Consensus modes."""
        start_time = time.time()
        members = node.member_agents or ["default_worker_1", "default_worker_2"]
        mode = node.team_mode

        member_outputs: Dict[str, Any] = {}
        total_tokens = 0

        if mode == AgnoTeamMode.ROUTE:
            # Route to the most specialized agent (first member by default or based on prompt)
            selected_member = members[0]
            member_outputs[selected_member] = {
                "role": "routed_specialist",
                "output": f"Specialist '{selected_member}' resolved the routed task.",
            }
            total_tokens += 350
        elif mode == AgnoTeamMode.BROADCAST:
            # Broadcast to all members concurrently
            for m in members:
                member_outputs[m] = {
                    "role": "collaborator",
                    "output": f"Worker '{m}' produced parallel sub-result.",
                }
                total_tokens += 250
        elif mode == AgnoTeamMode.TASKS:
            # Sequential task execution across members
            accumulated = str(inputs.get("prompt", ""))
            for i, m in enumerate(members):
                step_result = f"Worker '{m}' executed step {i+1} on [{accumulated[:30]}...]"
                member_outputs[m] = {"step": i + 1, "output": step_result}
                accumulated = step_result
                total_tokens += 200
        elif mode == AgnoTeamMode.CONSENSUS:
            # Debate / Consensus synthesis
            for m in members:
                member_outputs[m] = {"vote": "APPROVE", "stance": f"Stance from '{m}'"}
                total_tokens += 180
            member_outputs["synthesis"] = "Consensus reached: 100% APPROVE."

        duration_ms = (time.time() - start_time) * 1000
        return NodeExecutionResult(
            node_id=node.node_id,
            status=CanvasNodeStatus.COMPLETED,
            output_data={
                "team_title": node.title,
                "mode": mode.value,
                "member_outputs": member_outputs,
                "team_result": "Team execution completed successfully.",
            },
            tokens_consumed=total_tokens,
            duration_ms=duration_ms,
        )

    def _execute_workflow_step(
        self,
        node: CanvasNodeConfig,
        inputs: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Executes a deterministic workflow step."""
        start_time = time.time()
        duration_ms = (time.time() - start_time) * 1000
        return NodeExecutionResult(
            node_id=node.node_id,
            status=CanvasNodeStatus.COMPLETED,
            output_data={
                "step_name": node.title,
                "processed": True,
                "payload": inputs,
            },
            tokens_consumed=50,
            duration_ms=duration_ms,
        )

    def execute_graph_stepwise(
        self,
        graph_data: Dict[str, Any],
    ) -> Dict[str, NodeExecutionResult]:
        """
        Executes the entire Canvas Graph in topological order.
        If a node suspends for HITL, downstream execution pauses.
        """
        validation = self.validate_graph(graph_data)
        if not validation["valid"]:
            raise ValueError(f"Invalid Canvas Graph: {validation['error']}")

        graph_id = str(graph_data.get("graph_id", f"graph_{uuid.uuid4().hex[:6]}"))
        sorted_nodes = self.compile_topological_dag(graph_data)

        # Track outputs passed along edges
        node_outputs: Dict[str, Dict[str, Any]] = {}
        results: Dict[str, NodeExecutionResult] = {}

        # Edges lookup
        incoming_edges: Dict[str, List[str]] = defaultdict(list)
        for e in graph_data.get("edges", []):
            tgt = str(e.get("target_node_id") if isinstance(e, dict) else e.target_node_id)
            src = str(e.get("source_node_id") if isinstance(e, dict) else e.source_node_id)
            incoming_edges[tgt].append(src)

        initial_inputs = graph_data.get("initial_inputs", {})

        for node in sorted_nodes:
            # Aggregate inputs from parent nodes or initial inputs
            parents = incoming_edges[node.node_id]
            node_inputs = {}
            if not parents:
                node_inputs = dict(initial_inputs)
            else:
                for p_id in parents:
                    if p_id in node_outputs:
                        node_inputs.update(node_outputs[p_id])

            # Execute node based on type
            if node.node_type == CanvasNodeType.AGENT:
                res = self._execute_agent_node(node, node_inputs, graph_id)
            elif node.node_type == CanvasNodeType.TEAM:
                res = self._execute_team_node(node, node_inputs, graph_id)
            elif node.node_type == CanvasNodeType.WORKFLOW_STEP:
                res = self._execute_workflow_step(node, node_inputs)
            elif node.node_type == CanvasNodeType.HITL_GATE:
                chk = self.create_hitl_checkpoint(
                    graph_id=graph_id,
                    node_id=node.node_id,
                    reason=f"HITL Gate '{node.title}' requires manual approval",
                    pending_action="canvas_gate_approval",
                    parameters=node_inputs,
                )
                res = NodeExecutionResult(
                    node_id=node.node_id,
                    status=CanvasNodeStatus.PAUSED_HITL,
                    checkpoint_id=chk.checkpoint_id,
                )
            else:
                res = NodeExecutionResult(
                    node_id=node.node_id,
                    status=CanvasNodeStatus.COMPLETED,
                    output_data={"custom_node": node.title, "inputs": node_inputs},
                )

            results[node.node_id] = res
            self.execution_cache[node.node_id] = res

            if res.status == CanvasNodeStatus.PAUSED_HITL:
                logger.info(f"Execution paused at node {node.node_id} for HITL checkpoint {res.checkpoint_id}")
                break
            elif res.status == CanvasNodeStatus.FAILED:
                logger.error(f"Execution failed at node {node.node_id}: {res.error_message}")
                break
            else:
                node_outputs[node.node_id] = res.output_data or {}

        return results
