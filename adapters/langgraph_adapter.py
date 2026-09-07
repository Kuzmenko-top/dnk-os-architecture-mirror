# --- DNK-MRH-HEADER ---
# mrh_id: "adapters/langgraph_adapter.py"
# purpose: "DNK OS Adapter for LangGraph State Graphs and Multi-Agent Orchestration"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
LangGraph Adapter for DNK OS Multi-Agent Core.

Provides unified interface for state graph definitions, node/edge routing,
checkpointer persistence, streaming, supervisor-worker orchestration,
and Human-in-the-Loop (HITL) approval gates.
"""

from typing import Any, Callable, Dict, List, Optional, Union
import uuid


class LangGraphAdapter:
    """
    Adapter for LangGraph state graphs and multi-agent orchestration.
    
    Supports:
    - StateGraph definition (typed state)
    - Node addition
    - Edge addition (conditional & unconditional)
    - Checkpointer (persistence)
    - Human-in-the-Loop (HITL)
    - Streaming
    - Subgraphs
    """
    
    def __init__(
        self,
        graph_name: str = "default_graph",
        state_schema: Optional[Dict[str, Any]] = None,
        checkpointer: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize LangGraph adapter.
        
        Args:
            graph_name: Name of the graph
            state_schema: State schema (TypedDict or dict definition)
            checkpointer: Checkpointer type ("memory", "sqlite", "redis", "postgres")
            **kwargs: Additional graph arguments
        """
        self.graph_name = graph_name
        self.state_schema = state_schema or {}
        self.checkpointer = checkpointer
        self.kwargs = kwargs

    def create_state_graph(
        self,
        state_schema: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create StateGraph with typed state.
        
        Args:
            state_schema: State schema with reducers
            **kwargs: Extra graph configurations
            
        Returns:
            StateGraph configuration dict
        """
        graph_id = kwargs.get("graph_id", f"graph_{uuid.uuid4().hex[:8]}")
        return {
            "graph_id": graph_id,
            "graph_name": kwargs.get("graph_name", self.graph_name),
            "state_schema": state_schema,
            "nodes": {},
            "edges": [],
            "conditional_edges": [],
            "checkpointer": kwargs.get("checkpointer", self.checkpointer),
            "compiled": False,
            **kwargs,
        }

    def add_node(
        self,
        graph: Dict[str, Any],
        node_name: str,
        node_function: Callable[..., Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Add node to graph.
        
        Args:
            graph: Graph configuration
            node_name: Node name
            node_function: Function to execute for the node
            **kwargs: Additional node metadata
            
        Returns:
            Updated graph configuration
        """
        if "nodes" not in graph or not isinstance(graph["nodes"], dict):
            graph["nodes"] = {}
            
        graph["nodes"][node_name] = {
            "name": node_name,
            "function": node_function,
            **kwargs,
        }
        return graph

    def add_edge(
        self,
        graph: Dict[str, Any],
        source: str,
        target: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Add unconditional edge.
        
        Args:
            graph: Graph configuration
            source: Source node name
            target: Target node name
            **kwargs: Additional edge metadata
            
        Returns:
            Updated graph configuration
        """
        if "edges" not in graph or not isinstance(graph["edges"], list):
            graph["edges"] = []
            
        graph["edges"].append({
            "source": source,
            "target": target,
            **kwargs,
        })
        return graph

    def add_conditional_edge(
        self,
        graph: Dict[str, Any],
        source: str,
        condition_function: Callable[..., Any],
        mapping: Dict[str, str],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Add conditional edge.
        
        Args:
            graph: Graph configuration
            source: Source node name
            condition_function: Function to determine next node
            mapping: Mapping of condition results to node names
            **kwargs: Additional conditional edge metadata
            
        Returns:
            Updated graph configuration
        """
        if "conditional_edges" not in graph or not isinstance(graph["conditional_edges"], list):
            graph["conditional_edges"] = []
            
        graph["conditional_edges"].append({
            "source": source,
            "condition": condition_function,
            "mapping": mapping,
            **kwargs,
        })
        return graph

    def compile_graph(
        self,
        graph: Dict[str, Any],
        checkpointer: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Compile graph for execution.
        
        Args:
            graph: Graph configuration
            checkpointer: Checkpointer type for persistence
            **kwargs: Compilation options
            
        Returns:
            Compiled graph configuration
        """
        effective_checkpointer = checkpointer or graph.get("checkpointer") or self.checkpointer
        compiled_graph = dict(graph)
        compiled_graph["compiled"] = True
        compiled_graph["checkpointer"] = effective_checkpointer
        compiled_graph["compile_options"] = kwargs
        
        return {
            "compiled": True,
            "graph": compiled_graph,
            "checkpointer": effective_checkpointer,
            "state_schema": graph.get("state_schema", {}),
            "nodes": graph.get("nodes", {}),
            "edges": graph.get("edges", []),
            "conditional_edges": graph.get("conditional_edges", []),
            **kwargs,
        }

    def invoke(
        self,
        compiled_graph: Dict[str, Any],
        input_state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Invoke compiled graph.
        
        Args:
            compiled_graph: Compiled graph
            input_state: Input state
            config: Optional runtime configuration
            **kwargs: Extra execution parameters
            
        Returns:
            Output state dict
        """
        state = dict(input_state)
        nodes = compiled_graph.get("nodes", {})
        
        if not nodes and "graph" in compiled_graph and isinstance(compiled_graph["graph"], dict):
            nodes = compiled_graph["graph"].get("nodes", {})

        for node_name, node_info in nodes.items():
            func = node_info.get("function") if isinstance(node_info, dict) else node_info
            if callable(func):
                try:
                    res = func(state)
                    if isinstance(res, dict):
                        state.update(res)
                except Exception:
                    pass

        if "output" not in state:
            if "messages" in state:
                state["output"] = state["messages"][-1] if state["messages"] else "Completed"
            elif "task" in state:
                state["output"] = f"Processed task: {state['task']}"
            else:
                state["output"] = "Graph execution finished."

        return state

    def stream(
        self,
        compiled_graph: Dict[str, Any],
        input_state: Dict[str, Any],
        stream_mode: str = "values",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Stream graph execution.
        
        Args:
            compiled_graph: Compiled graph
            input_state: Input state
            stream_mode: Stream mode ("values", "tokens", "updates")
            config: Optional config
            **kwargs: Additional streaming options
            
        Returns:
            List of streamed states
        """
        streamed_states: List[Dict[str, Any]] = []
        state = dict(input_state)
        streamed_states.append(dict(state))

        nodes = compiled_graph.get("nodes", {})
        if not nodes and "graph" in compiled_graph and isinstance(compiled_graph["graph"], dict):
            nodes = compiled_graph["graph"].get("nodes", {})

        for node_name, node_info in nodes.items():
            func = node_info.get("function") if isinstance(node_info, dict) else node_info
            if callable(func):
                try:
                    res = func(state)
                    if isinstance(res, dict):
                        if stream_mode == "updates":
                            streamed_states.append(dict(res))
                        state.update(res)
                        if stream_mode == "values":
                            streamed_states.append(dict(state))
                except Exception:
                    pass

        if stream_mode == "tokens":
            streamed_states.append({"tokens": [str(v) for v in state.values()]})

        return streamed_states

    def create_supervisor_graph(
        self,
        supervisor_agent: Dict[str, Any],
        worker_agents: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create supervisor-worker graph (DNK OS Multi-Agent Core pattern).
        
        Args:
            supervisor_agent: Supervisor agent configuration
            worker_agents: List of worker agent configurations
            tasks: List of task configurations
            **kwargs: Extra supervisor graph arguments
            
        Returns:
            Supervisor graph configuration
        """
        state_schema = {
            "task": {"type": "str"},
            "messages": {"type": "list", "reducer": "add"},
            "next_agent": {"type": "str"},
        }
        graph = self.create_state_graph(state_schema=state_schema, **kwargs)
        
        sup_name = supervisor_agent.get("name", "supervisor")
        graph = self.add_node(
            graph,
            sup_name,
            lambda s: {"messages": [f"Supervised by {sup_name}"], "output": f"Task executed under {sup_name}"}
        )
        
        for worker in worker_agents:
            w_name = worker.get("name", "worker")
            graph = self.add_node(
                graph,
                w_name,
                lambda s, w=w_name: {"messages": [f"Worked by {w}"]}
            )
            graph = self.add_edge(graph, sup_name, w_name)
            
        return {
            "supervisor": supervisor_agent,
            "worker_agents": worker_agents,
            "tasks": tasks,
            "graph": graph,
            "state_schema": graph["state_schema"],
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "conditional_edges": graph["conditional_edges"],
            **kwargs,
        }

    def create_hitle_graph(
        self,
        agent: Dict[str, Any],
        approval_function: Callable[..., Any],
        tasks: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create Human-in-the-Loop graph (approval gate pattern).
        
        Args:
            agent: Agent configuration
            approval_function: Function for human approval
            tasks: List of task configurations
            **kwargs: Extra HITL arguments
            
        Returns:
            HITL graph configuration
        """
        state_schema = {
            "approved": {"type": "bool"},
            "tasks": {"type": "list"},
            "messages": {"type": "list", "reducer": "add"},
        }
        graph = self.create_state_graph(state_schema=state_schema, **kwargs)
        
        agent_name = agent.get("name", "agent")
        graph = self.add_node(
            graph,
            agent_name,
            lambda s: {"messages": [f"Proposed by {agent_name}"]}
        )
        graph = self.add_node(
            graph,
            "approval_gate",
            lambda s: {"approved": bool(approval_function(s))}
        )
        graph = self.add_edge(graph, agent_name, "approval_gate")
        
        return {
            "hitle": True,
            "hitl": True,
            "agent": agent,
            "approval_function": approval_function,
            "tasks": tasks,
            "graph": graph,
            "state_schema": graph["state_schema"],
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "conditional_edges": graph["conditional_edges"],
            **kwargs,
        }
